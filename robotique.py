"""ROBOTIQUE (cinématique) — modèle géométrique direct, FAUX=0 (mission formule/concept 2026-06-29).

Cinématique directe d'un bras planaire à 2 articulations rotoïdes (2R) : position de l'effecteur à partir des
longueurs de segments et des angles. Mécanisme EXACT (trigonométrie), sortie 6 chiffres significatifs. Portée
(min/max) et atteignabilité d'un point. Abstention STRUCTURELLE : longueur ≤ 0 -> ValueError.

Couvre le sujet borné « Robotique (cinématique) ».
Vérifié en adverse par `valide_robotique.py` (positions connues, portée, atteignabilité).
"""
from __future__ import annotations

import math

_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _pos(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0:
            raise ValueError("longueur strictement positive requise")


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def cinematique_directe_2r(l1, l2, theta1_deg, theta2_deg) -> tuple[float, float]:
    """Position (x, y) de l'effecteur d'un bras 2R planaire :
       x = l₁·cosθ₁ + l₂·cos(θ₁+θ₂) ; y = l₁·sinθ₁ + l₂·sin(θ₁+θ₂). Angles en degrés."""
    _pos(l1, l2)
    _num(theta1_deg, theta2_deg)
    t1 = math.radians(theta1_deg)
    t12 = math.radians(theta1_deg + theta2_deg)
    x = l1 * math.cos(t1) + l2 * math.cos(t12)
    y = l1 * math.sin(t1) + l2 * math.sin(t12)
    return (_sig(x), _sig(y))


def portee_max(l1, l2) -> float:
    """Rayon maximal atteignable (bras tendu) = l₁ + l₂."""
    _pos(l1, l2)
    return _sig(l1 + l2)


def portee_min(l1, l2) -> float:
    """Rayon minimal atteignable (bras replié) = |l₁ − l₂|."""
    _pos(l1, l2)
    return _sig(abs(l1 - l2))


def atteignable(l1, l2, x, y) -> bool:
    """Le point (x, y) est-il dans l'espace de travail du bras 2R ? (portee_min ≤ distance ≤ portee_max)."""
    _pos(l1, l2)
    _num(x, y)
    d = math.hypot(x, y)
    return abs(l1 - l2) - 1e-9 <= d <= l1 + l2 + 1e-9


if __name__ == "__main__":
    print("2R(1,1,0,0) :", cinematique_directe_2r(1, 1, 0, 0))      # (2,0)
    print("2R(1,1,90,0) :", cinematique_directe_2r(1, 1, 90, 0))    # (0,2)
    print("2R(1,1,0,90) :", cinematique_directe_2r(1, 1, 0, 90))    # (1,1)
    print("2R(2,1,90,-90) :", cinematique_directe_2r(2, 1, 90, -90))  # (1,2)
    print("portée max/min (3,1) :", portee_max(3, 1), portee_min(3, 1))
    print("atteignable (2,1)@(2.5,0) :", atteignable(2, 1, 2.5, 0), "| @(0.5,0) :", atteignable(2, 1, 0.5, 0))
