"""
OPTIQUE GÉOMÉTRIQUE — réflexion et réfraction (lois de Snell-Descartes).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité/la loi juge, jamais un faux) :
  • Le MÉCANISME est une LOI EXACTE de l'optique géométrique, pas une corrélation :
      – RÉFLEXION : l'angle de réflexion est ÉGAL à l'angle d'incidence (θr = θ1), angles mesurés par
        rapport à la NORMALE au dioptre.
      – RÉFRACTION (Snell-Descartes) :  n1·sin(θ1) = n2·sin(θ2).
        Si n1·sin(θ1)/n2 > 1, il n'existe AUCUN rayon réfracté : c'est la RÉFLEXION TOTALE interne
        -> on REFUSE (ValueError) plutôt que d'inventer un angle.
      – ANGLE CRITIQUE : θc = asin(n2/n1), défini SEULEMENT quand n1 > n2 (passage vers un milieu
        moins réfringent) ; sinon la réflexion totale n'existe pas -> ValueError.
  • Catalogue d'indices de réfraction SOURCÉ (raie D du sodium, λ ≈ 589 nm, valeurs de référence
    classiques des tables d'optique) : vide 1.0, air 1.000293, eau 1.333, verre crown 1.52,
    diamant 2.417, glycérine 1.473.
  • Les angles sont en RADIANS, mesurés depuis la normale, dans [0, π/2].
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (flottants en entrée,
    on ne prétend pas à l'exactitude au-delà) ; les valeurs sont donc APPROCHÉES à ce niveau.

GARANTIES (vérifiées en adverse par `valide_optique_geometrique.py`) :
  - indice n < 1 -> ValueError (en optique géométrique classique, n ≥ 1 : le vide est le minimum) ;
  - angle hors [0, π/2] -> ValueError (angle d'incidence mesuré depuis la normale, mal posé sinon) ;
  - sin(θ2) > 1 -> ValueError « réflexion totale : aucun rayon réfracté » (JAMAIS un angle inventé) ;
  - angle_critique demandé avec n1 ≤ n2 -> ValueError (l'angle critique n'existe pas dans ce sens) ;
  - milieu hors catalogue -> ValueError (on ne devine pas un indice) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

PI = math.pi
SOURCE = ("loi de Snell-Descartes n1·sinθ1 = n2·sinθ2 (optique géométrique classique) ; "
          "indices à λ≈589 nm : tables de référence (CRC Handbook / Hecht, Optics)")

_CHIFFRES_SIGNIFICATIFS = 10

# ── CATALOGUE SOURCÉ (indice de réfraction à λ ≈ 589 nm, raie D du sodium) ────────────────────────────────────
INDICES: dict[str, float] = {
    "vide": 1.0,
    "air": 1.000293,
    "eau": 1.333,
    "verre crown": 1.52,
    "diamant": 2.417,
    "glycérine": 1.473,
}


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_indice(n) -> float:
    """Indice de réfraction : réel fini ≥ 1 (le vide, n = 1, est le minimum en optique classique)."""
    if not _est_reel(n) or n < 1.0:
        raise ValueError("indice de réfraction invalide : un réel fini ≥ 1 est requis (le vide vaut 1)")
    return float(n)


def _exige_angle(theta) -> float:
    """Angle (rad) mesuré depuis la normale : réel fini dans [0, π/2]."""
    if not _est_reel(theta) or not (0.0 <= theta <= PI / 2):
        raise ValueError("angle invalide : un réel dans [0, pi/2] (radians, depuis la normale) est requis")
    return float(theta)


# ── CATALOGUE ─────────────────────────────────────────────────────────────────────────────────────────────────
def indice(milieu: str) -> float:
    """Indice de réfraction du milieu (λ ≈ 589 nm), depuis le catalogue SOURCÉ uniquement.

    Milieu inconnu -> ValueError (on ne devine JAMAIS un indice)."""
    if not isinstance(milieu, str):
        raise ValueError("milieu invalide : une chaîne (nom du milieu) est requise")
    cle = milieu.strip().lower()
    if cle not in INDICES:
        connus = ", ".join(sorted(INDICES))
        raise ValueError(f"milieu hors catalogue : « {milieu} » inconnu (connus : {connus})")
    return INDICES[cle]


# ── RÉFLEXION ─────────────────────────────────────────────────────────────────────────────────────────────────
def angle_reflexion(theta1: float) -> float:
    """Loi de la réflexion : θr = θ1 (angles depuis la normale). θ1 hors [0, π/2] -> ValueError."""
    return _exige_angle(theta1)


# ── RÉFRACTION (SNELL-DESCARTES) ─────────────────────────────────────────────────────────────────────────────-
def angle_refraction(n1: float, theta1: float, n2: float) -> float:
    """Angle réfracté θ2 (rad) : n1·sin(θ1) = n2·sin(θ2), soit θ2 = asin(n1·sin(θ1)/n2).

    Si n1·sin(θ1)/n2 > 1, aucun rayon réfracté n'existe -> ValueError (réflexion totale).
    Résultat approché, arrondi à 10 chiffres significatifs."""
    n1 = _exige_indice(n1)
    n2 = _exige_indice(n2)
    theta1 = _exige_angle(theta1)
    sin_theta2 = n1 * math.sin(theta1) / n2
    if sin_theta2 > 1.0:
        raise ValueError("réflexion totale : aucun rayon réfracté (n1·sin(θ1) > n2)")
    return _sig(math.asin(sin_theta2))


# ── ANGLE CRITIQUE ────────────────────────────────────────────────────────────────────────────────────────────
def angle_critique(n1: float, n2: float) -> float:
    """Angle critique θc = asin(n2/n1) (rad), défini SEULEMENT si n1 > n2 ; sinon ValueError.

    Au-delà de θc, tout rayon incident subit la réflexion totale interne.
    Résultat approché, arrondi à 10 chiffres significatifs."""
    n1 = _exige_indice(n1)
    n2 = _exige_indice(n2)
    if not (n1 > n2):
        raise ValueError("angle critique inexistant : il exige n1 > n2 (passage vers un milieu moins réfringent)")
    return _sig(math.asin(n2 / n1))


# ── RÉFLEXION TOTALE ─────────────────────────────────────────────────────────────────────────────────────────-
def reflexion_totale(n1: float, theta1: float, n2: float) -> bool:
    """True ssi le rayon subit la réflexion totale interne : n1·sin(θ1) > n2 (aucun rayon réfracté).

    Si n1 ≤ n2, la réflexion totale est impossible -> False. À θ1 = θc exactement, un rayon réfracté
    rasant (θ2 = π/2) existe encore -> False (l'inégalité est STRICTE)."""
    n1 = _exige_indice(n1)
    n2 = _exige_indice(n2)
    theta1 = _exige_angle(theta1)
    return n1 * math.sin(theta1) > n2
