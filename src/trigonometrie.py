"""TRIGONOMÉTRIE — fonctions et résolution de triangles, FAUX=0 (mission formule/concept 2026-06-29).

sin/cos/tan (degrés), conversions degré↔radian, loi des cosinus / loi des sinus, identité de Pythagore. Les valeurs
sont arrondies à 12 décimales (précision HONNÊTE : les angles remarquables 30/45/60/90° retombent exacts : sin30=0.5,
tan45=1…). Abstention STRUCTURELLE : tangente d'un angle où cos=0 (90°+k·180°) -> ValueError (asymptote, pas un faux) ;
triangle impossible (côté ≤ 0, inégalité triangulaire violée) -> ValueError.

Couvre le sujet borné « Trigonométrie ».
Vérifié en adverse par `valide_trigonometrie.py` (angles remarquables, Pythagore, triangle 3-4-5…).
"""
from __future__ import annotations

import math

_DEC = 12


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"nombre attendu, reçu {x!r}")
    return float(x)


def deg_vers_rad(deg) -> float:
    return round(_num(deg) * math.pi / 180.0, _DEC)


def rad_vers_deg(rad) -> float:
    return round(_num(rad) * 180.0 / math.pi, _DEC)


def sin_deg(deg) -> float:
    return round(math.sin(math.radians(_num(deg))), _DEC)


def cos_deg(deg) -> float:
    return round(math.cos(math.radians(_num(deg))), _DEC)


def tan_deg(deg) -> float:
    """tan en degrés. ValueError si cos = 0 (asymptote : 90°, 270°…) — jamais un nombre absurde."""
    d = _num(deg)
    if abs(round(math.cos(math.radians(d)), _DEC)) == 0.0:
        raise ValueError(f"tan({d}°) non définie (asymptote)")
    return round(math.tan(math.radians(d)), _DEC)


def loi_cosinus(a, b, angle_c_deg) -> float:
    """Troisième côté c = √(a² + b² − 2ab·cos C). a,b > 0. Pour C=90° -> Pythagore."""
    a, b = _num(a), _num(b)
    if a <= 0 or b <= 0:
        raise ValueError("côtés a, b > 0 requis")
    c2 = a * a + b * b - 2 * a * b * math.cos(math.radians(_num(angle_c_deg)))
    if c2 < 0:
        raise ValueError("configuration impossible (c² < 0)")
    return round(math.sqrt(c2), _DEC)


def angle_par_cotes(a, b, c) -> float:
    """Angle (en degrés) opposé au côté c, par la loi des cosinus inverse. ValueError si triangle impossible."""
    a, b, c = _num(a), _num(b), _num(c)
    if a <= 0 or b <= 0 or c <= 0:
        raise ValueError("côtés > 0 requis")
    if a + b <= c or a + c <= b or b + c <= a:
        raise ValueError("inégalité triangulaire violée")
    cos_c = (a * a + b * b - c * c) / (2 * a * b)
    cos_c = max(-1.0, min(1.0, cos_c))
    return round(math.degrees(math.acos(cos_c)), _DEC)


def hypotenuse(a, b) -> float:
    """Hypoténuse d'un triangle rectangle de cathètes a, b (= loi des cosinus à 90°)."""
    return loi_cosinus(a, b, 90)


if __name__ == "__main__":
    print("sin30 :", sin_deg(30), "| cos60 :", cos_deg(60), "| tan45 :", tan_deg(45))
    print("sin90 :", sin_deg(90), "| cos0 :", cos_deg(0), "| sin0 :", sin_deg(0))
    print("Pythagore sin²+cos² (37°) :", round(sin_deg(37) ** 2 + cos_deg(37) ** 2, 10))
    print("hypoténuse 3,4 :", hypotenuse(3, 4))
    print("angle opposé à 5 (triangle 3-4-5) :", angle_par_cotes(3, 4, 5))
    try:
        tan_deg(90)
    except ValueError as e:
        print("tan90 :", e)
