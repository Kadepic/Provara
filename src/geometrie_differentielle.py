"""GÉOMÉTRIE DIFFÉRENTIELLE — primitives EXACTES sur les courbes paramétrées planes, FAUX=0
(mission formule/concept 2026-06-29).

Posture identique à `physique` / `maths_discretes` : le MÉCANISME (la formule de géométrie différentielle) est
EXACT — c'est la garantie structurelle — et l'abstention est STRUCTURELLE : toute entrée invalide (type, domaine,
vitesse nulle, courbure nulle pour un rayon) lève `ValueError`, JAMAIS un résultat faux. Conservateur : un faux
négatif (abstention) est toléré, un faux POSITIF est interdit.

COUVRE (courbe plane t ↦ (x(t), y(t)), dérivées notées x', y', x'', y'') :
  • courbure(x', y', x'', y'')  =  |x'·y'' − y'·x''| / (x'² + y'²)^(3/2)
        – cercle de rayon r (paramétrage x=r cosθ, y=r sinθ) -> courbure = 1/r en TOUT point ;
          ex. θ=0 : x'=0, y'=r, x''=−r, y''=0  ->  |0·0 − r·(−r)| / (0+r²)^(3/2) = r²/r³ = 1/r ;
        – droite (accélération colinéaire à la vitesse, ici nulle) -> courbure = 0 ;
          ex. x'=1, y'=1, x''=0, y''=0  ->  |1·0 − 1·0| / 2^(3/2) = 0.
  • courbure_graphe(y', y'')  =  |y''| / (1 + y'²)^(3/2)   (cas particulier d'un graphe y=f(x), où x'=1, x''=0) ;
        – parabole y=x² au sommet (x=0 : y'=0, y''=2) -> courbure = 2 ; rayon de courbure = 1/2.
  • rayon_courbure(...)  =  1 / courbure(...)   (rayon du cercle osculateur) ; courbure nulle (droite) -> ValueError.
  • longueur_arc_segment(dx, dy)  =  √(dx² + dy²)   (élément d'arc d'un déplacement infinitésimal/segment).
  • longueur_polyligne(points)  =  Σ √(Δx² + Δy²)   (longueur d'arc approchée d'une polyligne de sommets).
  • tangente_unitaire(x', y')  =  (x', y') / ‖(x', y')‖   ;   normale_unitaire(x', y') = rotation +90° de la tangente
        = (−y', x') / ‖(x', y')‖ ; vitesse nulle -> ValueError (tangente indéfinie).

SOUNDNESS (vérifiée en adverse par `valide_geometrie_differentielle.py`) :
  - vitesse nulle x'=y'=0 -> ValueError (le dénominateur (x'²+y'²)^(3/2) s'annule : courbure/tangente indéfinies) ;
  - courbure nulle -> rayon_courbure lève ValueError (rayon infini : on s'abstient au lieu de rendre ∞) ;
  - type invalide (bool, complexe, str, None) -> ValueError ; polyligne mal formée -> ValueError ; déterministe.
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10  # précision HONNÊTE (pas un faux exact au-delà du flottant double)


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (préserve l'exactitude des valeurs simples : 0.5, 5.0, 0…)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _reel(*xs) -> None:
    """Garde de type : exige des nombres réels (int/float). bool/complexe/str/None -> ValueError (jamais un faux)."""
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre réel attendu, reçu {x!r}")
        if not math.isfinite(x):
            raise ValueError(f"valeur finie attendue, reçu {x!r}")


# ── COURBURE D'UNE COURBE PARAMÉTRÉE PLANE ────────────────────────────────────────────────────────────────────
def courbure(xp: float, yp: float, xpp: float, ypp: float) -> float:
    """Courbure κ = |x'·y'' − y'·x''| / (x'² + y'²)^(3/2) au point de dérivées (x', y', x'', y'').

    Vitesse nulle (x'=y'=0) -> ValueError (courbure indéfinie). Toujours ≥ 0 (valeur absolue)."""
    _reel(xp, yp, xpp, ypp)
    vitesse_carre = xp * xp + yp * yp
    if vitesse_carre <= 0.0:
        raise ValueError("vitesse nulle (x'=y'=0) : courbure indéfinie")
    num = abs(xp * ypp - yp * xpp)
    return _sig(num / vitesse_carre ** 1.5)


def courbure_graphe(yp: float, ypp: float) -> float:
    """Courbure d'un graphe y=f(x) : κ = |y''| / (1 + y'²)^(3/2). Cas particulier de `courbure(1, y', 0, y'')`.

    Dénominateur ≥ 1 : toujours défini (aucune vitesse nulle possible)."""
    _reel(yp, ypp)
    return _sig(abs(ypp) / (1.0 + yp * yp) ** 1.5)


def rayon_courbure(xp: float, yp: float, xpp: float, ypp: float) -> float:
    """Rayon du cercle osculateur R = 1/κ. Courbure nulle (droite) -> ValueError (rayon infini : abstention)."""
    k = courbure(xp, yp, xpp, ypp)
    if k <= 0.0:
        raise ValueError("courbure nulle : rayon de courbure infini (abstention)")
    return _sig(1.0 / k)


# ── LONGUEUR D'ARC ────────────────────────────────────────────────────────────────────────────────────────────
def longueur_arc_segment(dx: float, dy: float) -> float:
    """Élément/longueur d'arc d'un déplacement (dx, dy) : √(dx² + dy²)."""
    _reel(dx, dy)
    return _sig(math.hypot(dx, dy))


def longueur_polyligne(points) -> float:
    """Longueur d'arc d'une polyligne : Σ des longueurs de segments entre sommets consécutifs.

    `points` = suite (≥ 2) de couples (x, y) de réels. Mal formée -> ValueError."""
    if not isinstance(points, (list, tuple)) or len(points) < 2:
        raise ValueError("au moins 2 sommets (x, y) attendus")
    coords = []
    for p in points:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError(f"sommet (x, y) attendu, reçu {p!r}")
        _reel(p[0], p[1])
        coords.append((float(p[0]), float(p[1])))
    total = 0.0
    for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
        total += math.hypot(x1 - x0, y1 - y0)
    return _sig(total)


# ── REPÈRE DE FRENET (plan) ───────────────────────────────────────────────────────────────────────────────────
def tangente_unitaire(xp: float, yp: float):
    """Vecteur tangent unitaire T = (x', y') / ‖(x', y')‖. Vitesse nulle -> ValueError (tangente indéfinie)."""
    _reel(xp, yp)
    norme = math.hypot(xp, yp)
    if norme <= 0.0:
        raise ValueError("vitesse nulle : tangente indéfinie")
    return (_sig(xp / norme), _sig(yp / norme))


def normale_unitaire(xp: float, yp: float):
    """Normale unitaire N = rotation +90° de la tangente = (−y', x') / ‖(x', y')‖. Vitesse nulle -> ValueError."""
    _reel(xp, yp)
    norme = math.hypot(xp, yp)
    if norme <= 0.0:
        raise ValueError("vitesse nulle : normale indéfinie")
    return (_sig(-yp / norme), _sig(xp / norme))
