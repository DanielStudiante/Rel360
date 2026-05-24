"""
Construye NutritionTable a partir de NutritionData + PortionInfo.
Solo transforma datos — sin I/O, sin BD, sin IA.
"""
from __future__ import annotations
from app.models.nutrition_model import NutritionData
from app.models.portion_model import PortionInfo, NutritionPer100g, NutritionPerPortion
from app.models.nutrition_table_model import NutritionTable, WarningLabel
from app.rules.invima import (
    TipoAlimento, ETIQUETA_SELLO,
    calcular_calorias_por_100g, escalar_a_porcion, evaluar_sellos,
)

def build_nutrition_table(
    data: NutritionData,
    porcion: PortionInfo,
    tipo_alimento: TipoAlimento = TipoAlimento.SOLIDO,
    contiene_edulcorantes: bool = False,
) -> NutritionTable:
    pg = porcion.porcion_g

    kcal_100g = calcular_calorias_por_100g(
        data.proteina, data.grasa_total, data.carbohidratos_totales, data.fibra_dietaria
    )

    por_100g = NutritionPer100g(
        calorias_kcal=kcal_100g,
        proteina_g=data.proteina,
        grasa_total_g=data.grasa_total,
        grasa_saturada_g=data.grasa_saturada,
        grasa_trans_mg=data.grasa_trans_mg_100g,
        carbohidratos_totales_g=data.carbohidratos_totales,
        azucares_totales_g=data.azucares_totales,
        azucares_anadidos_g=data.azucares_anadidos,
        fibra_dietaria_g=data.fibra_dietaria,
        sodio_mg=data.sodio_mg_100g,
        hierro_mg=data.hierro_mg_100g,
        calcio_mg=data.calcio_mg_100g,
        potasio_mg=data.potasio_mg_100g,
        zinc_mg=data.zinc_mg_100g,
        vitamina_a_ug=data.vitamina_a_ug_100g,
        vitamina_d_ug=data.vitamina_d_ug_100g,
    )

    por_porcion = NutritionPerPortion(
        calorias_kcal=escalar_a_porcion(kcal_100g, pg),
        proteina_g=escalar_a_porcion(data.proteina, pg),
        grasa_total_g=escalar_a_porcion(data.grasa_total, pg),
        grasa_saturada_g=escalar_a_porcion(data.grasa_saturada, pg),
        grasa_trans_mg=escalar_a_porcion(data.grasa_trans_mg_100g, pg),
        carbohidratos_totales_g=escalar_a_porcion(data.carbohidratos_totales, pg),
        azucares_totales_g=escalar_a_porcion(data.azucares_totales, pg),
        azucares_anadidos_g=escalar_a_porcion(data.azucares_anadidos, pg),
        fibra_dietaria_g=escalar_a_porcion(data.fibra_dietaria, pg),
        sodio_mg=escalar_a_porcion(data.sodio_mg_100g, pg),
        hierro_mg=escalar_a_porcion(data.hierro_mg_100g, pg),
        calcio_mg=escalar_a_porcion(data.calcio_mg_100g, pg),
        potasio_mg=escalar_a_porcion(data.potasio_mg_100g, pg),
        zinc_mg=escalar_a_porcion(data.zinc_mg_100g, pg),
        vitamina_a_ug=escalar_a_porcion(data.vitamina_a_ug_100g, pg),
        vitamina_d_ug=escalar_a_porcion(data.vitamina_d_ug_100g, pg),
    )

    azucares_para_sello = (
        data.azucares_anadidos if data.azucares_anadidos is not None else data.azucares_totales
    )

    claves = evaluar_sellos(
        kcal_100g=kcal_100g,
        sodio_mg_100g=data.sodio_mg_100g,
        grasa_saturada_g_100g=data.grasa_saturada,
        grasa_trans_mg_100g=data.grasa_trans_mg_100g,
        azucares_libres_g_100g=azucares_para_sello,
        tipo=tipo_alimento,
    )

    return NutritionTable(
        producto=data.producto,
        lote=data.lote,
        porcion=porcion,
        por_100g=por_100g,
        por_porcion=por_porcion,
        advertencias=[WarningLabel(clave=c, etiqueta=ETIQUETA_SELLO[c]) for c in claves],
        contiene_edulcorantes=contiene_edulcorantes,
    )