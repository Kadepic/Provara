"""
GÉOMÉTRIES NON-EUCLIDIENNES — géométrie SPHÉRIQUE (courbure positive constante).

Même posture FAUX=0 que `physique` / `chimie` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est un THÉORÈME EXACT, pas une corrélation :
      – Théorème de Girard / Harriot : sur une sphère de rayon R, l'AIRE d'un triangle géodésique vaut
            A = R² · (Σ angles − π),
        donc l'EXCÈS sphérique  E = Σ angles − π = A / R²  est strictement positif (somme des angles > π,
        contrairement à la géométrie euclidienne où elle vaut exactement π).
      – La COURBURE de Gauss d'une sphère de rayon R est constante  K = 1/R²  (> 0).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (les angles d'entrée sont des
    flottants, on ne prétend pas à l'exactitude au-delà).

GARANTIES (vérifiées en adverse par `valide_geometries_non_euclidiennes.py`) :
  - R ≤ 0  -> ValueError  (un rayon de sphère est strictement positif ; jamais une courbure absurde) ;
  - aire ≤ 0  -> ValueError  (un triangle non dégénéré a une aire strictement positive) ;
  - un angle hors de l'intervalle ]0, π[  -> ValueError  (angle de triangle sphérique mal posé) ;
  - somme des angles ≤ π  -> ValueError  : ce N'EST PAS un triangle sphérique non dégénéré (la signature de
    la courbure positive est justement Σ > π) ; on refuse plutôt que de rendre une aire/un excès négatif ou nul ;
  - excès ≥ 2π  -> ValueError  (Σ < 3π pour un triangle, donc E = Σ − π < 2π) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

PI = math.pi
SOURCE = "théorème de Girard (aire sphérique) + courbure de Gauss K=1/R² (géométrie différentielle classique)"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_rayon(R) -> float:
    if not _est_reel(R) or R <= 0:
        raise ValueError("rayon de sphère R invalide : un réel strictement positif est requis")
    return float(R)


def _exige_angle(a) -> float:
    """Angle d'un sommet de triangle sphérique : réel dans ]0, π[ (strict)."""
    if not _est_reel(a) or not (0.0 < a < PI):
        raise ValueError("angle invalide : un réel dans l'intervalle ]0, pi[ est requis")
    return float(a)


# ── COURBURE ───────────────────────────────────────────────────────────────────────────────────────────────────
def courbure_gauss_sphere(R: float) -> float:
    """Courbure de Gauss d'une sphère de rayon R : K = 1/R² (constante, positive). R ≤ 0 -> ValueError."""
    R = _exige_rayon(R)
    return _sig(1.0 / (R * R))


# ── EXCÈS SPHÉRIQUE ──────────────────────────────────────────────────────────────────────────────────────────--
def exces_spherique(aire: float, R: float) -> float:
    """Excès sphérique E = aire / R² (= Σ angles − π, en radians).

    aire ≤ 0 -> ValueError (triangle dégénéré) ; R ≤ 0 -> ValueError ; E ≥ 2π -> ValueError (Σ < 3π)."""
    R = _exige_rayon(R)
    if not _est_reel(aire) or aire <= 0:
        raise ValueError("aire invalide : un réel strictement positif est requis (triangle non dégénéré)")
    exces = aire / (R * R)
    if exces >= 2.0 * PI:
        raise ValueError("excès ≥ 2π : pas un triangle sphérique simple (la somme des angles serait ≥ 3π)")
    return _sig(exces)


# ── SOMME DES ANGLES ─────────────────────────────────────────────────────────────────────────────────────────--
def somme_angles_triangle_spherique(a1: float, a2: float, a3: float):
    """Somme des angles (rad) d'un triangle sphérique non dégénéré.

    Renvoie le couple (somme, somme > π). Sur la sphère la somme est TOUJOURS > π : on refuse (ValueError)
    toute somme ≤ π (cas euclidien/dégénéré) ou tout angle hors ]0, π[ — jamais un résultat trompeur."""
    a1 = _exige_angle(a1)
    a2 = _exige_angle(a2)
    a3 = _exige_angle(a3)
    somme = a1 + a2 + a3
    if somme <= PI:
        raise ValueError("somme des angles ≤ π : pas un triangle sphérique non dégénéré (excès nul ou négatif)")
    return (_sig(somme), somme > PI)


# ── AIRE (THÉORÈME DE GIRARD) ────────────────────────────────────────────────────────────────────────────────--
def aire_triangle_spherique(angles, R: float) -> float:
    """Aire d'un triangle sphérique : A = R² · (Σ angles − π)  (théorème de Girard).

    `angles` = séquence de 3 angles (rad) dans ]0, π[ ; R ≤ 0 -> ValueError ; Σ ≤ π -> ValueError."""
    R = _exige_rayon(R)
    if not isinstance(angles, (list, tuple)) or len(angles) != 3:
        raise ValueError("angles invalide : exactement 3 angles (liste/tuple) sont requis")
    a1, a2, a3 = (_exige_angle(a) for a in angles)
    somme = a1 + a2 + a3
    if somme <= PI:
        raise ValueError("somme des angles ≤ π : pas un triangle sphérique non dégénéré")
    return _sig(R * R * (somme - PI))
