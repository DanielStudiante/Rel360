"""
Reglas Resolución 810/2021 + 2492/2022 — módulo puro, sin dependencias del proyecto.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

# Factores Atwater (Art. 11.1)
KCAL_PER_G_PROTEINA = 4.0
KCAL_PER_G_CARBOHIDRATOS = 4.0
KCAL_PER_G_GRASA = 9.0
KCAL_PER_G_FIBRA = 2.0  # fibra soluble fermentable

class TipoAlimento(str, Enum):
    SOLIDO = "solido"
    LIQUIDO = "liquido"

@dataclass(frozen=True)
class LimiteSello:
    nutriente: str
    limite_absoluto: float | None
    unidad_absoluta: str | None
    limite_porcentaje_energia: float | None

LIMITES_SOLIDOS: list[LimiteSello] = [
    LimiteSello("sodio",          300.0, "mg", None),
    LimiteSello("azucares_libres", None,  None, 10.0),
    LimiteSello("grasa_saturada",  None,  None, 10.0),
    LimiteSello("grasa_trans",     None,  None,  1.0),
]

LIMITES_LIQUIDOS: list[LimiteSello] = [
    LimiteSello("sodio",           40.0, "mg", None),
    LimiteSello("azucares_libres", None,  None, 10.0),
    LimiteSello("grasa_saturada",  None,  None, 10.0),
    LimiteSello("grasa_trans",     None,  None,  1.0),
]

ETIQUETA_SELLO: dict[str, str] = {
    "sodio":           "EXCESO EN SODIO",
    "azucares_libres": "EXCESO EN AZÚCARES",
    "grasa_saturada":  "EXCESO EN GRASAS SATURADAS",
    "grasa_trans":     "EXCESO EN GRASAS TRANS",
}

PORCION_REFERENCIA_DEFAULT_G = 100.0


def calcular_calorias_por_100g(
    proteina_g: float | None,
    grasa_total_g: float | None,
    carbohidratos_totales_g: float | None,
    fibra_dietaria_g: float | None,
) -> float:
    return round(
        (proteina_g or 0.0) * KCAL_PER_G_PROTEINA
        + (grasa_total_g or 0.0) * KCAL_PER_G_GRASA
        + (carbohidratos_totales_g or 0.0) * KCAL_PER_G_CARBOHIDRATOS
        + (fibra_dietaria_g or 0.0) * KCAL_PER_G_FIBRA,
        2,
    )


def escalar_a_porcion(valor_100g: float | None, porcion_g: float) -> float | None:
    if valor_100g is None:
        return None
    return round(valor_100g * porcion_g / 100.0, 4)


def _porcentaje_energia(kcal_nutriente: float, kcal_totales: float) -> float:
    if kcal_totales <= 0:
        return 0.0
    return (kcal_nutriente / kcal_totales) * 100.0


def evaluar_sellos(
    kcal_100g: float,
    sodio_mg_100g: float | None,
    grasa_saturada_g_100g: float | None,
    grasa_trans_mg_100g: float | None,
    azucares_libres_g_100g: float | None,
    tipo: TipoAlimento = TipoAlimento.SOLIDO,
) -> list[str]:
    sellos: list[str] = []
    limites = LIMITES_SOLIDOS if tipo == TipoAlimento.SOLIDO else LIMITES_LIQUIDOS

    for limite in limites:
        disparado = False

        if limite.nutriente == "sodio" and sodio_mg_100g is not None:
            excede_absoluto = limite.limite_absoluto is not None and sodio_mg_100g >= limite.limite_absoluto
            excede_por_kcal = kcal_100g > 0 and sodio_mg_100g / kcal_100g >= 1.0
            disparado = excede_absoluto or excede_por_kcal

        elif limite.nutriente == "azucares_libres" and azucares_libres_g_100g is not None:
            pct = _porcentaje_energia(azucares_libres_g_100g * KCAL_PER_G_CARBOHIDRATOS, kcal_100g)
            disparado = limite.limite_porcentaje_energia is not None and pct >= limite.limite_porcentaje_energia

        elif limite.nutriente == "grasa_saturada" and grasa_saturada_g_100g is not None:
            pct = _porcentaje_energia(grasa_saturada_g_100g * KCAL_PER_G_GRASA, kcal_100g)
            disparado = limite.limite_porcentaje_energia is not None and pct >= limite.limite_porcentaje_energia

        elif limite.nutriente == "grasa_trans" and grasa_trans_mg_100g is not None:
            grasa_trans_g = grasa_trans_mg_100g / 1000.0
            pct = _porcentaje_energia(grasa_trans_g * KCAL_PER_G_GRASA, kcal_100g)
            disparado = limite.limite_porcentaje_energia is not None and pct >= limite.limite_porcentaje_energia

        if disparado:
            sellos.append(limite.nutriente)

    return sellos