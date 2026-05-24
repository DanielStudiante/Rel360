from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class PortionInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)
    descripcion: str | None = None
    porcion_g: float = 100.0
    porciones_por_envase: float | None = None

class NutritionPer100g(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)
    calorias_kcal: float | None = None
    proteina_g: float | None = None
    grasa_total_g: float | None = None
    grasa_saturada_g: float | None = None
    grasa_trans_mg: float | None = None
    carbohidratos_totales_g: float | None = None
    azucares_totales_g: float | None = None
    azucares_anadidos_g: float | None = None
    fibra_dietaria_g: float | None = None
    sodio_mg: float | None = None
    hierro_mg: float | None = None
    calcio_mg: float | None = None
    potasio_mg: float | None = None
    zinc_mg: float | None = None
    vitamina_a_ug: float | None = None
    vitamina_d_ug: float | None = None

class NutritionPerPortion(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)
    calorias_kcal: float | None = None
    proteina_g: float | None = None
    grasa_total_g: float | None = None
    grasa_saturada_g: float | None = None
    grasa_trans_mg: float | None = None
    carbohidratos_totales_g: float | None = None
    azucares_totales_g: float | None = None
    azucares_anadidos_g: float | None = None
    fibra_dietaria_g: float | None = None
    sodio_mg: float | None = None
    hierro_mg: float | None = None
    calcio_mg: float | None = None
    potasio_mg: float | None = None
    zinc_mg: float | None = None
    vitamina_a_ug: float | None = None
    vitamina_d_ug: float | None = None