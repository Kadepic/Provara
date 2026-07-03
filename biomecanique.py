"""
BIOMÉCANIQUE DU GESTE — physique EXACTE du mouvement sportif (mandat Yohan : couvrir le borné, bloc « FORMULE »).

Même posture que `physique` / `aerodynamique` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la cinématique du projectile, la statique du levier) est EXACT — garantie structurelle.
  • Aucune « valeur-pays » ni constante inventée : seule G_PESANTEUR = 9.81 m/s² est une donnée conventionnelle
    (gravité terrestre standard), passable en paramètre `g` pour un autre astre.
  • La sortie est ARRONDIE à 6 chiffres significatifs — précision HONNÊTE, déterministe.

GARANTIES (vérifiées en adverse par `valide_biomecanique.py`) :
  - vitesse initiale v0 < 0            -> ValueError (jamais une portée absurde) ;
  - angle hors de l'intervalle [0,90]° -> ValueError (tir balistique de surface) ;
  - g ≤ 0                              -> ValueError ;
  - bras de levier < 0 / durée ≤ 0 / grandeur non finie -> ValueError ;
  - déterministe ; conservateur (abstention/HORS toléré, faux POSITIF interdit).

Le geste sportif = un projectile (le centre de masse, le ballon, le javelot) + des leviers articulaires.
"""
from __future__ import annotations

import math

# Gravité terrestre standard (m/s²). Conventionnelle ; surchargeable via le paramètre `g`.
G_PESANTEUR = 9.81

# Angle de tir (degrés) maximisant la PORTÉE d'un projectile lancé et reçu à la même altitude,
# sans résistance de l'air : 45°. C'est un EXTREMUM analytique de v0²·sin(2θ)/g (max de sin(2θ) à 2θ=90°).
ANGLE_OPTIMAL_PORTEE_DEG = 45.0

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _reel(x) -> float:
    """Convertit en float fini ; abstient (ValueError) sur bool / NaN / inf / non-numérique."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"grandeur non numérique : {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"grandeur non finie : {x!r}")
    return f


def _valide_tir(v0, angle_deg, g) -> tuple[float, float, float]:
    """Valide (v0 ≥ 0, 0 ≤ angle ≤ 90, g > 0) ou lève ValueError."""
    v0 = _reel(v0)
    angle_deg = _reel(angle_deg)
    g = _reel(g)
    if v0 < 0:
        raise ValueError(f"vitesse initiale négative : {v0}")
    if not (0.0 <= angle_deg <= 90.0):
        raise ValueError(f"angle hors [0,90]° : {angle_deg}")
    if g <= 0:
        raise ValueError(f"pesanteur non positive : {g}")
    return v0, angle_deg, g


# ── CINÉMATIQUE DU PROJECTILE (tir balistique de surface, sans frottement) ──────────────────────────────────────
def portee_projectile(v0: float, angle_deg: float, g: float = G_PESANTEUR) -> float:
    """Portée horizontale : R = v0²·sin(2θ)/g  (lancé et reçu à la même altitude)."""
    v0, angle_deg, g = _valide_tir(v0, angle_deg, g)
    return _sig(v0 * v0 * math.sin(math.radians(2.0 * angle_deg)) / g)


def hauteur_max(v0: float, angle_deg: float, g: float = G_PESANTEUR) -> float:
    """Hauteur maximale : H = (v0·sinθ)² / (2g)."""
    v0, angle_deg, g = _valide_tir(v0, angle_deg, g)
    vy = v0 * math.sin(math.radians(angle_deg))
    return _sig(vy * vy / (2.0 * g))


def temps_de_vol(v0: float, angle_deg: float, g: float = G_PESANTEUR) -> float:
    """Temps de vol : t = 2·v0·sinθ / g  (retour à l'altitude de lancement)."""
    v0, angle_deg, g = _valide_tir(v0, angle_deg, g)
    return _sig(2.0 * v0 * math.sin(math.radians(angle_deg)) / g)


def angle_optimal_portee() -> float:
    """Angle (degrés) maximisant la portée sans frottement : 45° (extremum de sin(2θ))."""
    return ANGLE_OPTIMAL_PORTEE_DEG


# ── STATIQUE / DYNAMIQUE DU LEVIER ARTICULAIRE ──────────────────────────────────────────────────────────────────
def moment_force(force: float, bras_levier: float) -> float:
    """Moment de force (couple) : M = F·d  (force × bras de levier perpendiculaire), en N·m.

    F et d sont des MAGNITUDES (≥ 0). On abstient sur une magnitude négative plutôt que de mélanger
    les conventions de signe (jamais un faux).
    """
    force = _reel(force)
    bras_levier = _reel(bras_levier)
    if force < 0:
        raise ValueError(f"magnitude de force négative : {force}")
    if bras_levier < 0:
        raise ValueError(f"bras de levier négatif : {bras_levier}")
    return _sig(force * bras_levier)


# Alias métier : le moment d'une force est aussi appelé « couple ».
def couple(force: float, bras_levier: float) -> float:
    """Synonyme de `moment_force` : couple = F·d (N·m)."""
    return moment_force(force, bras_levier)


def impulsion(force: float, temps: float) -> float:
    """Impulsion : J = F·t  (égale la variation de quantité de mouvement Δp), en N·s.

    Durée t > 0 strictement (une impulsion s'exerce sur une durée non nulle).
    """
    force = _reel(force)
    temps = _reel(temps)
    if force < 0:
        raise ValueError(f"magnitude de force négative : {force}")
    if temps <= 0:
        raise ValueError(f"durée non strictement positive : {temps}")
    return _sig(force * temps)
