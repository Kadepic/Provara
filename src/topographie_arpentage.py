"""TOPOGRAPHIE / ARPENTAGE — relations métriques exactes du terrain, FAUX=0.

Mécanismes établis de l'arpentage (relations trigonométriques exactes, aucune approximation) :
  • pente_pourcent(Δh, d)        = 100·Δh/d        (pente en %, d = distance HORIZONTALE > 0)
  • distance_horizontale(D, α)   = D·cos(α)        (projection au sol d'une distance mesurée le long de la pente)
  • denivele(α, D)               = D·sin(α)        (dénivelé = composante verticale)
  • aire_polygone_coords(pts)    = ½·|Σ(xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)|   (formule du lacet / shoelace de Gauss)

Sorties arrondies à 6 chiffres significatifs. Fonctions PURES, déterministes.
SOUNDNESS (abstention, jamais un faux) : distance ≤ 0, angle hors (−90°,90°) [resp. [−90°,90°] pour le dénivelé],
moins de 3 points pour une aire, coordonnée non numérique -> ValueError.

Couvre le sujet borné « Topographie / arpentage ». Vérifié en adverse par `valide_topographie_arpentage.py`.
"""
from __future__ import annotations

import math

_SIG = 6


def _sig(x):
    """Arrondi à 6 chiffres significatifs (0.0 reste 0.0)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs):
    """N'accepte que des nombres réels (rejette bool, str, None…)."""
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def pente_pourcent(denivele, distance_horizontale) -> float:
    """Pente en pourcentage = 100·Δh/d. La distance horizontale d doit être > 0."""
    _num(denivele, distance_horizontale)
    if distance_horizontale <= 0:
        raise ValueError("distance horizontale > 0 requise")
    return _sig(100.0 * denivele / distance_horizontale)


def distance_horizontale(distance_pente, pente_deg) -> float:
    """Projection horizontale d'une distance D mesurée le long de la pente : d = D·cos(α).
    D > 0 ; angle de pente α ∈ (−90°, 90°) (cos > 0)."""
    _num(distance_pente, pente_deg)
    if distance_pente <= 0:
        raise ValueError("distance de pente > 0 requise")
    if not (-90 < pente_deg < 90):
        raise ValueError("angle de pente ∈ (−90°, 90°) requis")
    return _sig(distance_pente * math.cos(math.radians(pente_deg)))


def denivele(angle_deg, distance) -> float:
    """Dénivelé (composante verticale) d'une distance D le long d'une pente d'angle α : Δh = D·sin(α).
    D > 0 ; α ∈ [−90°, 90°]. Le signe de Δh suit le signe de α (montée/descente)."""
    _num(angle_deg, distance)
    if distance <= 0:
        raise ValueError("distance > 0 requise")
    if not (-90 <= angle_deg <= 90):
        raise ValueError("angle de pente ∈ [−90°, 90°] requis")
    return _sig(distance * math.sin(math.radians(angle_deg)))


def aire_polygone_coords(points) -> float:
    """Aire d'un polygone simple par la formule du lacet (shoelace de Gauss) :
    A = ½·|Σ_{i} (xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)|. Au moins 3 sommets (xᵢ, yᵢ) requis ; l'ordre est cyclique."""
    try:
        pts = list(points)
    except TypeError:
        raise ValueError("liste de sommets attendue")
    if len(pts) < 3:
        raise ValueError("au moins 3 sommets requis pour une aire")
    coords = []
    for p in pts:
        try:
            x, y = p
        except (TypeError, ValueError):
            raise ValueError(f"sommet (x, y) attendu, reçu {p!r}")
        _num(x, y)
        coords.append((float(x), float(y)))
    n = len(coords)
    s = 0.0
    for i in range(n):
        x_i, y_i = coords[i]
        x_j, y_j = coords[(i + 1) % n]
        s += x_i * y_j - x_j * y_i
    return _sig(abs(s) / 2.0)
