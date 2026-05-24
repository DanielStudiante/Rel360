from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from app.models.portion_model import PortionInfo, NutritionPer100g, NutritionPerPortion

class WarningLabel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)
    clave: str       # e.g. "sodio"
    etiqueta: str    # e.g. "EXCESO EN SODIO"

class NutritionTable(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)
    producto: str | None = None
    lote: str | None = None
    porcion: PortionInfo
    por_100g: NutritionPer100g
    por_porcion: NutritionPerPortion
    advertencias: list[WarningLabel] = []
    contiene_edulcorantes: bool = False