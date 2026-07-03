"""ÉQUATIONS DIFFÉRENTIELLES — solutions analytiques et numériques, FAUX=0 (mission formule/concept 2026-06-29).

Solution exacte de l'équation linéaire du 1er ordre y' = k·y (croissance/décroissance exponentielle : y(t)=y₀·e^(kt)),
solution de y' = a·y + b (avec point d'équilibre), méthode d'Euler explicite (numérique) VÉRIFIÉE contre la solution
analytique. Mécanisme EXACT pour l'analytique. Abstention STRUCTURELLE : pas de discrétisation ≤ 0 -> ValueError.

Couvre le sujet borné « Équations différentielles ».
Vérifié en adverse par `valide_equa_diff.py` (décroissance radioactive, Euler converge vers e^t).
"""
from __future__ import annotations

import math

_DEC = 9


def solution_exponentielle(y0, k, t) -> float:
    """Solution exacte de y' = k·y : y(t) = y₀·e^(k·t)."""
    for v in (y0, k, t):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("nombres requis")
    return round(y0 * math.exp(k * t), _DEC)


def solution_affine(y0, a, b, t) -> float:
    """Solution exacte de y' = a·y + b (a ≠ 0) : y(t) = (y₀ + b/a)·e^(a·t) − b/a. Point d'équilibre −b/a."""
    for v in (y0, a, b, t):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("nombres requis")
    if a == 0:
        return round(y0 + b * t, _DEC)            # y' = b -> y = y0 + b t
    eq = -b / a
    return round((y0 - eq) * math.exp(a * t) + eq, _DEC)


def demi_vie(k) -> float:
    """Demi-vie d'une décroissance y' = −k·y (k > 0) : t½ = ln(2)/k."""
    if isinstance(k, bool) or not isinstance(k, (int, float)) or k <= 0:
        raise ValueError("constante k > 0 requise")
    return round(math.log(2) / k, _DEC)


def euler(f, y0, t0, t_final, n_pas):
    """Méthode d'Euler explicite pour y' = f(t, y). Renvoie y approché en t_final. `f` appelable (t,y)->dy/dt."""
    if not callable(f):
        raise ValueError("f doit être appelable")
    if not isinstance(n_pas, int) or isinstance(n_pas, bool) or n_pas <= 0:
        raise ValueError("n_pas entier > 0 requis")
    h = (t_final - t0) / n_pas
    t, y = t0, y0
    for _ in range(n_pas):
        y = y + h * f(t, y)
        t = t + h
    return round(y, _DEC)


if __name__ == "__main__":
    print("y'=−0.1y, y0=100, t=0 :", solution_exponentielle(100, -0.1, 0))
    print("croissance y0=1,k=1,t=1 (=e) :", solution_exponentielle(1, 1, 1))
    print("demi-vie k=ln2 (=1) :", demi_vie(math.log(2)))
    print("refroidissement y'=−(y−20), y0=100, t=1 :", solution_affine(100, -1, 20, 1))
    print("Euler y'=y, y0=1, t=1, 1000 pas (~e) :", euler(lambda t, y: y, 1, 0, 1, 1000))
    print("Euler converge vers analytique :", abs(euler(lambda t, y: y, 1, 0, 1, 100000) - math.e) < 1e-3)
