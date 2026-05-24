from __future__ import annotations
from pydantic import BaseModel
from app.rules.invima import TipoAlimento


class TextRequest(BaseModel):
    text: str


class ExtractRequest(BaseModel):
    file_id: str


class NutritionTableRequest(BaseModel):
    file_id: str
    tipo_alimento: TipoAlimento = TipoAlimento.SOLIDO
    contiene_edulcorantes: bool = False