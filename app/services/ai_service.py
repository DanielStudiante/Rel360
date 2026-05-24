from __future__ import annotations

import json
import os
import re
from importlib import import_module
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_MODEL_NAME = "gemini-2.5-flash"

def _extract_json_text(response_text: str) -> str:
    stripped_text = response_text.strip()
    stripped_text = re.sub(r"^```(?:json)?\s*", "", stripped_text, flags=re.IGNORECASE)
    stripped_text = re.sub(r"\s*```$", "", stripped_text, flags=re.IGNORECASE)

    start_index = stripped_text.find("{")
    end_index = stripped_text.rfind("}")
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise ValueError("La respuesta no contiene un JSON válido")

    return stripped_text[start_index : end_index + 1]


def _build_simulated_response() -> str:
    result = {
        "producto": "Turron mani",
        "lote": None,
        "humedad": None,
        "materia_seca": None,
        "nitrogeno": None,
        "proteina": 12.7,
        "grasa_total": 18.08,
        "grasa_saturada": None,
        "grasa_trans_mg_100g": None,
        "cenizas": None,
        "fibra_dietaria": None,
        "carbohidratos_totales": None,
        "azucares_totales": None,
        "sodio_mg_100g": 113.75,
        "hierro_mg_100g": None,
        "calcio_mg_100g": None,
        "potasio_mg_100g": None,
        "zinc_mg_100g": None,
        "vitamina_a_ug_100g": None,
        "vitamina_d_ug_100g": None,
    }
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def _build_gemini_response(text: str, api_key: str) -> str:
    genai = import_module("google.genai")

    prompt = (
    "Eres un sistema experto en extracción de información nutricional a partir de análisis de laboratorio.\n\n"

    "Debes extraer los datos del texto y devolver EXCLUSIVAMENTE un JSON válido.\n"
    "NO incluyas explicaciones, texto adicional ni markdown.\n\n"

    "REGLAS CRÍTICAS:\n"
    "1. NO inventes valores.\n"
    "2. SOLO extrae valores que estén explícitamente en el texto.\n"
    "3. Si un dato no aparece claramente, usa null.\n"
    "4. Convierte números con coma decimal a punto (ej: 7,34 → 7.34).\n"
    "5. Ignora unidades como %, mg/100g, ug/100g, etc.\n"
    "6. 'ND' (No Detectado) debe convertirse en null.\n"
    "7. Extrae el lote si aparece en el texto (ej: 'lote.038' → '038').\n\n"

    "El JSON debe contener EXACTAMENTE estas claves:\n"
    "producto, lote, humedad, materia_seca, nitrogeno, proteina, "
    "grasa_total, grasa_saturada, grasa_trans_mg_100g, cenizas, fibra_dietaria, "
    "carbohidratos_totales, azucares_totales, sodio_mg_100g, hierro_mg_100g, "
    "calcio_mg_100g, potasio_mg_100g, zinc_mg_100g, vitamina_a_ug_100g, vitamina_d_ug_100g.\n\n"

    "Ejemplo:\n"
    "Entrada:\n"
    "Carbohidratos Totales % 60,3\n"
    "Azucares Totales % 41,06\n"
    "Zinc mg/100g ND\n\n"
    "Salida:\n"
    "{\n"
    '  "carbohidratos_totales": 60.3,\n'
    '  "azucares_totales": 41.06,\n'
    '  "zinc_mg_100g": null\n'
    "}\n\n"

    f"Texto:\n{text}"
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=GEMINI_MODEL_NAME, contents=prompt)
    response_text = getattr(response, "text", None)
    if not response_text:
        raise ValueError("Gemini no devolvió texto")

    json_text = _extract_json_text(str(response_text))
    parsed_response = json.loads(json_text)
    if not isinstance(parsed_response, dict):
        raise ValueError(f"Gemini devolvió {type(parsed_response).__name__}, se esperaba dict")

    return json.dumps(parsed_response, ensure_ascii=False, separators=(",", ":"))


def process_text_with_ai(text: str) -> str:
    """Usa Gemini cuando hay API key; si no, devuelve la simulación."""

    api_key = os.getenv("REL360_API_KEY")
    if not api_key:
        return _build_simulated_response()

    try:
        return _build_gemini_response(text, api_key)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return _build_simulated_response()
    
def _build_simulated_portion_response() -> str:
    result = {
        "descripcion": "1 Unidad (10g)",
        "porcion_g": 10.0,
        "porciones_por_envase": 15.0,
    }
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def _build_gemini_portion_response(text: str, api_key: str) -> str:
    genai = import_module("google.genai")
    prompt = (
        "Eres un sistema experto en etiquetado nutricional colombiano.\n\n"
        "Extrae la información de porción del siguiente texto y devuelve EXCLUSIVAMENTE un JSON válido.\n"
        "NO incluyas explicaciones, texto adicional ni markdown.\n\n"
        "REGLAS:\n"
        "1. Busca 'Tamaño por porción', 'Tamaño de la porción', 'Número de porciones por envase'.\n"
        "2. Extrae el peso en gramos (ej: '1 Unidad (10g)' → porcion_g: 10.0).\n"
        "3. Si no hay info de porción, usa porcion_g: 100.0.\n"
        "4. Convierte comas decimales a punto.\n\n"
        "Claves del JSON: descripcion (str o null), porcion_g (float), porciones_por_envase (float o null).\n\n"
        f"Texto:\n{text}"
    )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=GEMINI_MODEL_NAME, contents=prompt)
    response_text = getattr(response, "text", None)
    if not response_text:
        raise ValueError("Gemini no devolvió texto para porción")
    json_text = _extract_json_text(str(response_text))
    parsed = json.loads(json_text)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini no devolvió dict para porción")
    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))


def process_portion_with_ai(text: str) -> str:
    api_key = os.getenv("REL360_API_KEY")
    if not api_key:
        return _build_simulated_portion_response()
    try:
        return _build_gemini_portion_response(text, api_key)
    except Exception:
        import traceback
        traceback.print_exc()
        return _build_simulated_portion_response()
