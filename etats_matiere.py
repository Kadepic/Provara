"""ÉTATS DE LA MATIÈRE — état physique selon la température, FAUX=0 (mission formule/concept 2026-06-29).

À partir d'une température et des points de fusion / d'ébullition d'un corps (dans la MÊME unité), on détermine son
état physique : solide (T < fusion), liquide (fusion ≤ T < ébullition), gaz (T ≥ ébullition). Conversions d'échelles
de température (Celsius/Kelvin/Fahrenheit). Mécanisme EXACT (comparaisons / formules de conversion). Abstention
STRUCTURELLE : points incohérents (fusion ≥ ébullition), température sous le zéro absolu -> ValueError.

Couvre le sujet borné « États de la matière ».
Vérifié en adverse par `valide_etats_matiere.py` (eau solide/liquide/gaz, conversions d'échelle).
"""
from __future__ import annotations

_ZERO_ABSOLU_C = -273.15


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"température numérique attendue, reçu {x!r}")


def etat_physique(temperature, point_fusion, point_ebullition) -> str:
    """État physique d'un corps à `temperature` : 'solide' / 'liquide' / 'gaz'. Les trois valeurs dans la MÊME unité.
    Convention : à T = fusion -> liquide (transition), à T = ébullition -> gaz."""
    _num(temperature, point_fusion, point_ebullition)
    if point_fusion >= point_ebullition:
        raise ValueError("point de fusion < point d'ébullition requis")
    if temperature < point_fusion:
        return "solide"
    if temperature < point_ebullition:
        return "liquide"
    return "gaz"


def celsius_vers_kelvin(c) -> float:
    _num(c)
    if c < _ZERO_ABSOLU_C - 1e-9:
        raise ValueError("température sous le zéro absolu")
    return round(c - _ZERO_ABSOLU_C, 10)


def kelvin_vers_celsius(k) -> float:
    _num(k)
    if k < 0:
        raise ValueError("Kelvin ≥ 0 requis (zéro absolu)")
    return round(k + _ZERO_ABSOLU_C, 10)


def celsius_vers_fahrenheit(c) -> float:
    _num(c)
    return round(c * 9 / 5 + 32, 10)


def fahrenheit_vers_celsius(f) -> float:
    _num(f)
    return round((f - 32) * 5 / 9, 10)


def nombre_changements_etat() -> dict:
    """Les 6 transitions de phase entre solide/liquide/gaz (référentiel conventionnel, sourcé)."""
    return {"fusion": "solide->liquide", "solidification": "liquide->solide",
            "vaporisation": "liquide->gaz", "liquefaction": "gaz->liquide",
            "sublimation": "solide->gaz", "condensation": "gaz->solide"}


if __name__ == "__main__":
    # eau : fusion 0 °C, ébullition 100 °C
    for t in [-10, 0, 25, 100, 150]:
        print(f"  eau à {t} °C -> {etat_physique(t, 0, 100)}")
    print("0 °C en K :", celsius_vers_kelvin(0), "| 100 °C en K :", celsius_vers_kelvin(100))
    print("373.15 K en °C :", kelvin_vers_celsius(373.15))
    print("100 °C en °F :", celsius_vers_fahrenheit(100), "| 32 °F en °C :", fahrenheit_vers_celsius(32))
