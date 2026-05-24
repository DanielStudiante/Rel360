from __future__ import annotations

import json

from pydantic import ValidationError

from app.models.nutrition_model import NutritionData
from app.models.portion_model import PortionInfo
from app.models.nutrition_table_model import NutritionTable
from app.services.ai_service import process_text_with_ai, process_portion_with_ai
from app.services.nutrition_table_service import build_nutrition_table
from app.rules.invima import TipoAlimento


def _sanitize_dict(data: object) -> dict:
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


def _parse_nutrition_data(ai_response: str) -> NutritionData:
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
        return NutritionData.model_validate(data_dict)
    except ValidationError as exc:
        print(f"[nutrition_service] Error validando NutritionData: {exc}")
        raise ValueError(f"Error de parsing del modelo: {exc}") from exc


def process_nutrition_text_with_raw(text: str) -> tuple[NutritionData, str]:
    ai_response = process_text_with_ai(text)
    nutrition = _parse_nutrition_data(ai_response)
    return nutrition, ai_response


def process_nutrition_text(text: str) -> NutritionData:
    nutrition, _ = process_nutrition_text_with_raw(text)
    return nutrition


def process_full_nutrition_table(
    text: str,
    tipo_alimento: TipoAlimento = TipoAlimento.SOLIDO,
    contiene_edulcorantes: bool = False,
) -> tuple[NutritionTable, str, str]:
    nutrition_raw = process_text_with_ai(text)
    portion_raw = process_portion_with_ai(text)

    nutrition_data = _parse_nutrition_data(nutrition_raw)

    try:
        portion_dict = json.loads(portion_raw)
        portion_info = PortionInfo.model_validate(portion_dict)
    except Exception as exc:
        raise ValueError(f"Error parseando porción: {exc}") from exc

    table = build_nutrition_table(
        data=nutrition_data,
        porcion=portion_info,
        tipo_alimento=tipo_alimento,
        contiene_edulcorantes=contiene_edulcorantes,
    )

    return table, nutrition_raw, portion_raw