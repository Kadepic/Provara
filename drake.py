"""
DRAKE — Recherche de vie (SETI) : ÉQUATION DE DRAKE, bornée par sa DÉFINITION.

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est EXACT : l'équation de Drake (Frank Drake, 1961) est une DÉFINITION — un simple produit de
    sept facteurs. Il n'y a pas d'approximation possible : N = R · fp · ne · fl · fi · fc · L. Le résultat est donc
    EXACT au sens de la définition (ce qui est incertain, ce sont les valeurs des facteurs en entrée, pas le calcul).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision HONNÊTE (on ne fabrique pas de décimales fausses
    issues du bruit flottant ; ex. 1·0.5·2·1·0.01·0.01·10000 = 1.0 exactement).

SIGNIFICATION DES FACTEURS (et leur DOMAINE, qui borne la validité) :
  • R   = taux de formation d'étoiles propices (étoiles / an)            → réel ≥ 0
  • fp  = fraction de ces étoiles ayant des planètes                     → fraction ∈ [0, 1]
  • ne  = nb moyen de planètes habitables par étoile à planètes          → réel ≥ 0 (peut dépasser 1)
  • fl  = fraction de ces planètes où la vie apparaît                    → fraction ∈ [0, 1]
  • fi  = fraction où apparaît une vie INTELLIGENTE                      → fraction ∈ [0, 1]
  • fc  = fraction émettant des signaux DÉTECTABLES                      → fraction ∈ [0, 1]
  • L   = durée d'émission de ces signaux (années)                       → réel ≥ 0
  N = nombre de civilisations communicantes détectables dans la Galaxie.

ABSTENTION STRUCTURELLE (vérifiée en adverse par `valide_drake.py`) — JAMAIS un nombre faux :
  - facteur NÉGATIF (R, ne ou L < 0)                 -> ValueError ;
  - fraction HORS [0, 1] (fp, fl, fi ou fc)          -> ValueError ;
  - type non numérique / booléen / NaN / ±inf        -> ValueError.
  Déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10  # précision honnête : on ne publie pas le bruit flottant au-delà


def _num(x, nom: str) -> float:
    """Convertit en float réel fini, sinon lève ValueError. bool REFUSÉ (True/False ≠ grandeur physique)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre réel, reçu {x!r}")
    v = float(x)
    if math.isnan(v) or math.isinf(v):
        raise ValueError(f"{nom} doit être fini, reçu {x!r}")
    return v


def _nonneg(x, nom: str) -> float:
    """Facteur physique ≥ 0 (un taux, un compte ou une durée négatif n'a aucun sens) -> sinon ValueError."""
    v = _num(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} doit être ≥ 0 (facteur négatif interdit), reçu {v}")
    return v


def _fraction(x, nom: str) -> float:
    """Fraction ∈ [0, 1] (une proportion hors de [0,1] n'a aucun sens) -> sinon ValueError."""
    v = _num(x, nom)
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{nom} doit être une fraction ∈ [0,1], reçu {v}")
    return v


def _arrondi(x: float) -> float:
    """Arrondit à 10 chiffres significatifs (élimine le bruit flottant ; précision honnête)."""
    if x == 0.0:
        return 0.0
    return float(f"{x:.{_CHIFFRES_SIGNIFICATIFS}g}")


def nombre_civilisations(R, fp, ne, fl, fi, fc, L) -> float:
    """
    Équation de Drake : N = R · fp · ne · fl · fi · fc · L.

    Renvoie N (float ≥ 0, arrondi à 10 chiffres significatifs). Chaque facteur est validé selon son domaine
    (R, ne, L ≥ 0 ; fp, fl, fi, fc ∈ [0, 1]) — toute entrée hors domaine lève ValueError (jamais un N faux).

    Exemple (valeurs « classiques » de Drake) :
        nombre_civilisations(1, 0.5, 2, 1, 0.01, 0.01, 10000) == 1.0
    """
    r = _nonneg(R, "R")
    p = _fraction(fp, "fp")
    n = _nonneg(ne, "ne")
    l_vie = _fraction(fl, "fl")
    i = _fraction(fi, "fi")
    c = _fraction(fc, "fc")
    duree = _nonneg(L, "L")
    return _arrondi(r * p * n * l_vie * i * c * duree)
