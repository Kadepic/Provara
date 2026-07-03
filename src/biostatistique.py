"""
BIOSTATISTIQUE — tests diagnostiques (épidémiologie EXACTE).

Posture FAUX=0 (même que `physique`/`chimie` : la réalité juge, jamais un faux) :
  • Le MÉCANISME est EXACT : ce sont des DÉFINITIONS de l'épidémiologie clinique (pas des estimations).
    À partir des effectifs d'un tableau de contingence 2×2 (test vs maladie), chaque indice est un RAPPORT exact.
        VP = vrais positifs    (malade ET test +)
        FN = faux négatifs     (malade ET test −)
        VN = vrais négatifs    (sain   ET test −)
        FP = faux positifs     (sain   ET test +)
  • Les fonctions sont PURES, DÉTERMINISTES, sans état.
  • SOUNDNESS (jamais inventer) :
        - effectif/quantité NÉGATIF        -> ValueError
        - type non numérique / bool / NaN  -> ValueError
        - DÉNOMINATEUR nul                 -> ValueError (rapport indéfini)
        - probabilité hors [0, 1]          -> ValueError
        - malades > total                  -> ValueError (prévalence > 1 absurde)
    Toute entrée hors référentiel => abstention par exception, jamais un nombre faux.

Références (conventions ÉTABLIES, universelles) :
    Sensibilité  Se = VP/(VP+FN)          Spécificité  Sp = VN/(VN+FP)
    VPP          = VP/(VP+FP)             VPN          = VN/(VN+FN)
    Prévalence   = malades/total
    Rapport de vraisemblance positif  RV+ = Se/(1−Sp)
    Rapport de vraisemblance négatif  RV− = (1−Se)/Sp
    Exactitude (accuracy) = (VP+VN)/(VP+VN+FP+FN)
"""
from __future__ import annotations

import math

SOURCE = "définitions épidémiologie clinique (tableau 2×2 test/maladie)"


# ── garde-fous (soundness) ──────────────────────────────────────────────────────────────────────────────────────
def _effectif(x, nom):
    """Effectif/quantité valide = nombre réel fini >= 0, hors booléen."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : un booléen n'est pas un effectif")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : effectif non numérique ({type(x).__name__})")
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError(f"{nom} : effectif non fini ({x})")
    if x < 0:
        raise ValueError(f"{nom} : effectif négatif ({x})")
    return float(x)


def _probabilite(x, nom):
    """Probabilité/proportion valide = nombre réel fini dans [0, 1], hors booléen."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : un booléen n'est pas une probabilité")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : probabilité non numérique ({type(x).__name__})")
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError(f"{nom} : probabilité non finie ({x})")
    if x < 0 or x > 1:
        raise ValueError(f"{nom} : probabilité hors [0, 1] ({x})")
    return float(x)


def _rapport(num, den, nom):
    if den == 0:
        raise ValueError(f"{nom} : dénominateur nul")
    return num / den


# ── indices diagnostiques ───────────────────────────────────────────────────────────────────────────────────────
def sensibilite(VP, FN):
    """Se = VP/(VP+FN) — proportion de malades correctement détectés."""
    vp = _effectif(VP, "VP")
    fn = _effectif(FN, "FN")
    return _rapport(vp, vp + fn, "sensibilite")


def specificite(VN, FP):
    """Sp = VN/(VN+FP) — proportion de sains correctement classés négatifs."""
    vn = _effectif(VN, "VN")
    fp = _effectif(FP, "FP")
    return _rapport(vn, vn + fp, "specificite")


def valeur_predictive_positive(VP, FP):
    """VPP = VP/(VP+FP) — P(malade | test +)."""
    vp = _effectif(VP, "VP")
    fp = _effectif(FP, "FP")
    return _rapport(vp, vp + fp, "valeur_predictive_positive")


def valeur_predictive_negative(VN, FN):
    """VPN = VN/(VN+FN) — P(sain | test −)."""
    vn = _effectif(VN, "VN")
    fn = _effectif(FN, "FN")
    return _rapport(vn, vn + fn, "valeur_predictive_negative")


def prevalence(malades, total):
    """Prévalence = malades/total — proportion de malades dans la population."""
    m = _effectif(malades, "malades")
    t = _effectif(total, "total")
    if t == 0:
        raise ValueError("prevalence : total nul")
    if m > t:
        raise ValueError(f"prevalence : malades ({malades}) > total ({total})")
    return m / t


def rapport_vraisemblance_positif(sens, spec):
    """RV+ = Se/(1−Sp) — facteur multiplicatif des cotes après un test positif."""
    se = _probabilite(sens, "sens")
    sp = _probabilite(spec, "spec")
    return _rapport(se, 1.0 - sp, "rapport_vraisemblance_positif")


def rapport_vraisemblance_negatif(sens, spec):
    """RV− = (1−Se)/Sp — facteur multiplicatif des cotes après un test négatif."""
    se = _probabilite(sens, "sens")
    sp = _probabilite(spec, "spec")
    return _rapport(1.0 - se, sp, "rapport_vraisemblance_negatif")


def exactitude(VP, VN, FP, FN):
    """Exactitude (accuracy) = (VP+VN)/(VP+VN+FP+FN)."""
    vp = _effectif(VP, "VP")
    vn = _effectif(VN, "VN")
    fp = _effectif(FP, "FP")
    fn = _effectif(FN, "FN")
    return _rapport(vp + vn, vp + vn + fp + fn, "exactitude")
