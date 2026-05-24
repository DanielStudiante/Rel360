from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NutritionData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)
    
    producto: str | None = None
    lote: str | None = None
    humedad: float | None = None
    materia_seca: float | None = None
    nitrogeno: float | None = None
    proteina: float | None = None
    grasa_total: float | None = None
    grasa_saturada: float | None = None
    grasa_trans_mg_100g: float | None = None
    cenizas: float | None = None
    fibra_dietaria: float | None = None
    carbohidratos_totales: float | None = None
    azucares_totales: float | None = None
    sodio_mg_100g: float | None = None
    hierro_mg_100g: float | None = None
    calcio_mg_100g: float | None = None
    potasio_mg_100g: float | None = None
    zinc_mg_100g: float | None = None
    vitamina_a_ug_100g: float | None = None
    vitamina_d_ug_100g: float | None = None
    azucares_anadidos: float | None = None     # g/100g
    grasa_trans_mg_100g: float | None = None   # mg/100g (el lab reporta en mg)