"""GÉOTECHNIQUE — mécanique des sols, FAUX=0 (mission formule/concept 2026-06-29).

Contrainte verticale (σ = γ·z), principe de Terzaghi (contrainte EFFECTIVE σ' = σ − u), coefficient de poussée
active de Rankine (Ka = tan²(45°−φ/2)) et poussée active sur un mur. Mécanisme EXACT, sortie 6 chiffres significatifs.
Abstection STRUCTURELLE : poids volumique/profondeur négatifs, angle de frottement hors [0,90°[ -> ValueError.

Couvre le sujet borné « Géotechnique ».
Vérifié en adverse par `valide_geotechnique.py` (contrainte effective, Rankine φ=30°→Ka=1/3…).
"""
from __future__ import annotations

import math

_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def contrainte_verticale(poids_volumique, profondeur) -> float:
    """Contrainte verticale totale σ = γ·z (kPa si γ en kN/m³, z en m). γ ≥ 0, z ≥ 0."""
    _num(poids_volumique, profondeur)
    if poids_volumique < 0 or profondeur < 0:
        raise ValueError("γ et z ≥ 0 requis")
    return _sig(poids_volumique * profondeur)


def contrainte_effective(contrainte_totale, pression_interstitielle) -> float:
    """Principe de Terzaghi : σ' = σ − u (contrainte effective = totale − pression de l'eau)."""
    _num(contrainte_totale, pression_interstitielle)
    if pression_interstitielle < 0:
        raise ValueError("pression interstitielle ≥ 0 requise")
    return _sig(contrainte_totale - pression_interstitielle)


def coefficient_poussee_active(phi_deg) -> float:
    """Coefficient de poussée active de Rankine Ka = tan²(45° − φ/2). φ ∈ [0, 90°[."""
    _num(phi_deg)
    if not (0 <= phi_deg < 90):
        raise ValueError("angle de frottement φ ∈ [0, 90°[ requis")
    return _sig(math.tan(math.radians(45 - phi_deg / 2)) ** 2)


def coefficient_poussee_passive(phi_deg) -> float:
    """Coefficient de poussée passive de Rankine Kp = tan²(45° + φ/2) = 1/Ka."""
    _num(phi_deg)
    if not (0 <= phi_deg < 90):
        raise ValueError("angle de frottement φ ∈ [0, 90°[ requis")
    return _sig(math.tan(math.radians(45 + phi_deg / 2)) ** 2)


def poussee_active(poids_volumique, hauteur, phi_deg) -> float:
    """Force de poussée active sur un mur de soutènement : Pa = ½·Ka·γ·H² (par mètre linéaire). γ,H ≥ 0."""
    _num(poids_volumique, hauteur)
    if poids_volumique < 0 or hauteur < 0:
        raise ValueError("γ et H ≥ 0 requis")
    ka = coefficient_poussee_active(phi_deg)
    return _sig(0.5 * ka * poids_volumique * hauteur ** 2)


if __name__ == "__main__":
    print("σ totale γ=18,z=5 :", contrainte_verticale(18, 5), "kPa")
    print("σ' = 90 - 20 :", contrainte_effective(90, 20), "kPa")
    print("Ka(φ=30°) :", coefficient_poussee_active(30), "(= 1/3)")
    print("Kp(φ=30°) :", coefficient_poussee_passive(30), "(= 3)")
    print("Ka·Kp :", round(coefficient_poussee_active(30) * coefficient_poussee_passive(30), 6))
    print("poussée active γ=18,H=5,φ=30 :", poussee_active(18, 5, 30), "kN/m")
