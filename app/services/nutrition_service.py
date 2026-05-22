from __future__ import annotations

import json
from typing import Tuple

from pydantic import ValidationError

from app.models.nutrition_model import NutritionData
from app.services.ai_service import process_text_with_ai


def _sanitize_dict(data: object) -> dict:
    """Asegura que el diccionario contiene solo tipos primitivos válidos."""
    if not isinstance(data, dict):
        raise ValueError(f"Esperado dict, recibido {type(data).__name__}")

    sanitized: dict[str, object] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            key = str(key)

        if value is None:
            sanitized[key] = None
        elif isinstance(value, str):
            sanitized[key] = value
        elif isinstance(value, bool):
            raise ValueError("Boolean no permitido")
        elif isinstance(value, (int, float)):
            sanitized[key] = float(value)
        else:
            raise ValueError(f"Tipo no válido para clave '{key}': {type(value).__name__}")

    return sanitized


def process_nutrition_text_with_raw(text: str) -> tuple[NutritionData, str]:
    """Procesa texto y retorna el modelo validado junto con la respuesta cruda de IA."""
    ai_response = process_text_with_ai(text)
    if not isinstance(ai_response, str):
        raise ValueError(f"AI response debe ser string, recibido {type(ai_response).__name__}")

    try:
        data_dict = json.loads(ai_response)
    except Exception as exc:
        print(f"[nutrition_service] Error parseando JSON de IA: {exc}")
        raise ValueError(f"JSON inválido desde AI: {exc}") from exc

    try:
        data_dict = _sanitize_dict(data_dict)
    except ValueError as exc:
        print(f"[nutrition_service] Error sanitizando JSON: {exc}")
        raise

    try:
        nutrition = NutritionData.model_validate(data_dict)
    except ValidationError as exc:
        print(f"[nutrition_service] Error validando modelo nutricional: {exc}")
        raise ValueError(f"Error de parsing del modelo: {exc}") from exc

    return nutrition, ai_response


def process_nutrition_text(text: str) -> NutritionData:
    """Procesa texto, llama IA, parsea JSON y valida el modelo nutricional."""
    nutrition, _ = process_nutrition_text_with_raw(text)
    return nutrition
