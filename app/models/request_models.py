from __future__ import annotations
from pydantic import BaseModel

class TextRequest(BaseModel):
    text: str

class ExtractRequest(BaseModel):
    file_id: str

class NutritionTableRequest(BaseModel):
    file_id: str
    tipo_alimento: str = "solido"
    contiene_edulcorantes: bool = False