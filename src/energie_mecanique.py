"""
ÉNERGIE MÉCANIQUE — conservation dans un système ISOLÉ (mécanique classique).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est un THÉORÈME EXACT de la mécanique newtonienne, pas une corrélation :
      – Énergie cinétique      Ec = ½·m·v²          (translation d'un point matériel de masse m, vitesse v) ;
      – Énergie potentielle    Ep = m·g·h           (pesanteur uniforme, hauteur h ≥ 0 au-dessus de la référence) ;
      – Énergie mécanique      Em = Ec + Ep ;
      – THÉORÈME DE CONSERVATION : pour un système isolé soumis aux seules forces CONSERVATIVES (poids),
        Em est CONSTANTE le long du mouvement : Em₁ = Em₂. Toute perte (frottement) casse l'égalité.
      – Corollaire (chute libre depuis le repos / pendule) :  m·g·h = ½·m·v²  ⇒  v = √(2·g·h)  et  h = v²/(2·g).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (les entrées sont des flottants,
    on ne prétend pas à l'exactitude au-delà).
  • `conserve` compare Em₁ et Em₂ à une tolérance près, en arithmétique EXACTE (fractions.Fraction) :
    chaque flottant d'entrée est converti SANS perte en rationnel, donc |Em₁ − Em₂| est calculé exactement
    et AUCUN écart réel ne peut être absorbé par l'arrondi float64 (l'ulp de Em ne masque plus rien,
    même pour Em ~ 10¹² J et un écart de 10⁻⁵ J). Un écart au-delà de tol renvoie False (constat
    physique : le système n'est PAS conservé — frottement, apport d'énergie…), PAS une exception.
    L'exception (ValueError) est réservée aux entrées MAL POSÉES (types, domaines).

GARANTIES (vérifiées en adverse par `valide_energie_mecanique.py`) :
  - m ≤ 0  -> ValueError  (une masse est strictement positive) ;
  - h < 0  -> ValueError  (hauteur comptée au-dessus de la référence ; h = 0 est licite) ;
  - g ≤ 0  -> ValueError  (accélération de pesanteur strictement positive) ;
  - tol < 0  -> ValueError  (une tolérance est un réel ≥ 0) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise structure d'état) -> ValueError ;
  - `conserve` renvoie False (jamais une exception) quand Em diffère au-delà de tol — frottement détecté ;
  - `conserve` calcule |Em₁ − Em₂| en EXACT (Fraction) : pas de faux positif par absorption sous l'ulp
    float64 (contre-exemple d'audit : m=1, v=10⁶, h₂=10⁻⁶, g=10, tol=10⁻⁹ -> écart exact ≈ 10⁻⁵ J -> False) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Un ÉTAT est un triplet (m, v, h) : masse (kg), vitesse (m/s, signe libre — seul v² compte), hauteur (m ≥ 0).
Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("théorème de l'énergie mécanique (mécanique newtonienne) : Em = ½mv² + mgh constante pour un "
          "système isolé à forces conservatives ; g normal = 9.80665 m/s² (3e CGPM, 1901)")

#: Accélération normale de la pesanteur (valeur CONVENTIONNELLE exacte, 3e CGPM 1901).
G_NORMAL = 9.80665

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_masse(m) -> float:
    if not _est_reel(m) or m <= 0:
        raise ValueError("masse invalide : un réel strictement positif (kg) est requis")
    return float(m)


def _exige_vitesse(v) -> float:
    """Vitesse algébrique : tout réel fini (le signe n'affecte pas Ec, qui dépend de v²)."""
    if not _est_reel(v):
        raise ValueError("vitesse invalide : un réel fini (m/s) est requis")
    return float(v)


def _exige_hauteur(h) -> float:
    if not _est_reel(h) or h < 0:
        raise ValueError("hauteur invalide : un réel ≥ 0 (m, au-dessus de la référence) est requis")
    return float(h)


def _exige_g(g) -> float:
    if not _est_reel(g) or g <= 0:
        raise ValueError("pesanteur g invalide : un réel strictement positif (m/s²) est requis")
    return float(g)


def _exige_etat(etat):
    """Un état = triplet (m, v, h). Toute autre structure -> ValueError."""
    if not isinstance(etat, (list, tuple)) or len(etat) != 3:
        raise ValueError("état invalide : exactement (masse, vitesse, hauteur) est requis")
    m, v, h = etat
    return _exige_masse(m), _exige_vitesse(v), _exige_hauteur(h)


# ── ÉNERGIES ─────────────────────────────────────────────────────────────────────────────────────────────────--
def energie_cinetique(m: float, v: float) -> float:
    """Ec = ½·m·v² (J). m ≤ 0 -> ValueError ; v de signe libre (seul v² compte)."""
    m = _exige_masse(m)
    v = _exige_vitesse(v)
    return _sig(0.5 * m * v * v)


def energie_potentielle(m: float, h: float, g: float = G_NORMAL) -> float:
    """Ep = m·g·h (J, pesanteur uniforme). m ≤ 0, h < 0 ou g ≤ 0 -> ValueError."""
    m = _exige_masse(m)
    h = _exige_hauteur(h)
    g = _exige_g(g)
    return _sig(m * g * h)


def energie_mecanique(m: float, v: float, h: float, g: float = G_NORMAL) -> float:
    """Em = Ec + Ep = ½·m·v² + m·g·h (J)."""
    m = _exige_masse(m)
    v = _exige_vitesse(v)
    h = _exige_hauteur(h)
    g = _exige_g(g)
    return _sig(0.5 * m * v * v + m * g * h)


# ── CONSERVATION (système isolé) ─────────────────────────────────────────────────────────────────────────────--
def _em_exacte(m: float, v: float, h: float, g: float) -> Fraction:
    """Em = ½·m·v² + m·g·h en arithmétique EXACTE : chaque flottant (déjà validé fini) est converti
    sans perte en Fraction, donc le résultat est le rationnel exact déterminé par les entrées."""
    mf, vf, hf, gf = Fraction(m), Fraction(v), Fraction(h), Fraction(g)
    return mf * vf * vf / 2 + mf * gf * hf


def conserve(etat1, etat2, tol: float = 1e-9, g: float = G_NORMAL) -> bool:
    """True ssi Em(etat1) == Em(etat2) à tol près (théorème de conservation, système isolé).

    etat = (m, v, h). La différence |Em₁ − Em₂| est calculée en EXACT (fractions.Fraction sur les
    entrées converties sans perte) : aucun écart réel ne peut être absorbé par l'arrondi float64,
    quelle que soit la magnitude de Em (garantie FAUX=0 : pas de « conservé » à tort).
    Renvoie False — PAS une exception — si |Em₁ − Em₂| > tol (frottement / apport d'énergie détecté).
    ValueError est réservée aux entrées mal posées (types, m ≤ 0, h < 0, g ≤ 0, tol < 0)."""
    m1, v1, h1 = _exige_etat(etat1)
    m2, v2, h2 = _exige_etat(etat2)
    g = _exige_g(g)
    if not _est_reel(tol) or tol < 0:
        raise ValueError("tolérance invalide : un réel ≥ 0 est requis")
    ecart = abs(_em_exacte(m1, v1, h1, g) - _em_exacte(m2, v2, h2, g))
    return ecart <= Fraction(float(tol))


# ── CHUTE LIBRE / PENDULE (corollaires de la conservation) ───────────────────────────────────────────────────--
def vitesse_depuis_hauteur(h: float, g: float = G_NORMAL) -> float:
    """v = √(2·g·h) : vitesse acquise en bas d'une chute libre de hauteur h, départ au repos.

    Corollaire de m·g·h = ½·m·v² (la masse s'élimine). h < 0 ou g ≤ 0 -> ValueError ; h = 0 -> v = 0."""
    h = _exige_hauteur(h)
    g = _exige_g(g)
    return _sig(math.sqrt(2.0 * g * h))


def hauteur_depuis_vitesse(v: float, g: float = G_NORMAL) -> float:
    """h = v²/(2·g) : hauteur atteinte (ou de chute équivalente) pour une vitesse v, réciproque exacte.

    Corollaire de ½·m·v² = m·g·h. g ≤ 0 -> ValueError ; v de signe libre (seul v² compte)."""
    v = _exige_vitesse(v)
    g = _exige_g(g)
    return _sig(v * v / (2.0 * g))
