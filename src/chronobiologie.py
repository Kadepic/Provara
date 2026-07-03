"""
chronobiologie.py — Rythmes circadiens et cycles de sommeil (faits établis + arithmétique).

Mécanismes EXACTS / faits sourcés (chronobiologie humaine) :

  • periode_circadienne() = ~24.2 h
      Période intrinsèque (free-running) de l'horloge circadienne humaine mesurée en
      isolement temporel. Czeisler et al., Science 1999 : 24.18 ± 0.04 h. Renvoie 24.2 h.
      C'est un FAIT (légèrement > 24 h), pas une entrée libre -> aucun argument.

  • nombre_cycles_sommeil(duree_min, cycle_min=90) = duree_min / cycle_min
      Un cycle de sommeil complet (NREM N1→N2→N3 puis REM) dure ≈ 90 min.
      Ex. 8 h = 480 min / 90 ≈ 5.33 cycles. Pure arithmétique exacte.

  • duree_pour_cycles(n_cycles, cycle_min=90) = n_cycles * cycle_min
      Inverse : durée (min) pour n cycles complets. Ex. 5 cycles -> 450 min = 7.5 h.

  • phase_circadienne(heure) : classification de l'heure d'horloge (0 ≤ heure < 24) selon
      la phase circadienne dominante, convention de chronobiologie humaine (sujet diurne) :
        - [2, 4)            -> 'pic_melatonine'  (sécrétion de mélatonine maximale, ~2-4 h ;
                                                  proche du nadir de température corporelle)
        - [22, 24) ∪ [0, 6) -> 'nuit'            (phase d'obscurité / repos, hors pic)
        - [6, 22)           -> 'jour'            (phase d'éveil / activité)
      Le pic de mélatonine est un sous-intervalle de la nuit : il est testé en premier.

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • duree_min < 0, ou non fini -> ValueError.
  • cycle_min <= 0, ou non fini -> ValueError.
  • n_cycles < 0, ou non fini -> ValueError.
  • heure hors [0, 24), ou non finie -> ValueError.

stdlib uniquement, fonctions pures déterministes.
"""

import math

__all__ = [
    "periode_circadienne",
    "nombre_cycles_sommeil",
    "duree_pour_cycles",
    "phase_circadienne",
    "PERIODE_CIRCADIENNE_H",
    "CYCLE_SOMMEIL_MIN",
]

# ── Faits sourcés (constantes) ──
# Période intrinsèque de l'horloge circadienne humaine (Czeisler 1999 : 24.18 h).
PERIODE_CIRCADIENNE_H = 24.2
# Durée conventionnelle d'un cycle de sommeil complet.
CYCLE_SOMMEIL_MIN = 90.0


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def periode_circadienne():
    """
    Période intrinsèque (free-running) de l'horloge circadienne humaine, en heures.

    FAIT établi : ≈ 24.2 h (légèrement supérieure à 24 h ; Czeisler et al. 1999, 24.18 ± 0.04 h).
    Aucun argument. Renvoie un float constant.
    """
    return PERIODE_CIRCADIENNE_H


def nombre_cycles_sommeil(duree_min, cycle_min=90):
    """
    Nombre (fractionnaire) de cycles de sommeil pour une durée donnée.

    = duree_min / cycle_min, un cycle ≈ 90 min.
    Ex. 480 min (8 h) / 90 ≈ 5.333 cycles.

    duree_min : durée de sommeil en minutes, >= 0.
    cycle_min : durée d'un cycle en minutes, > 0 (défaut 90).
    duree_min < 0, cycle_min <= 0, ou valeurs non finies -> ValueError.
    """
    d = _reel_fini(duree_min, "duree_min")
    c = _reel_fini(cycle_min, "cycle_min")
    if d < 0.0:
        raise ValueError(f"duree_min négative : {d}")
    if c <= 0.0:
        raise ValueError(f"cycle_min non strictement positif : {c}")
    return d / c


def duree_pour_cycles(n_cycles, cycle_min=90):
    """
    Durée de sommeil (minutes) couvrant n cycles complets.

    = n_cycles * cycle_min. Ex. 5 cycles * 90 = 450 min (7.5 h).

    n_cycles : nombre de cycles, >= 0.
    cycle_min : durée d'un cycle en minutes, > 0 (défaut 90).
    n_cycles < 0, cycle_min <= 0, ou valeurs non finies -> ValueError.
    """
    n = _reel_fini(n_cycles, "n_cycles")
    c = _reel_fini(cycle_min, "cycle_min")
    if n < 0.0:
        raise ValueError(f"n_cycles négatif : {n}")
    if c <= 0.0:
        raise ValueError(f"cycle_min non strictement positif : {c}")
    return n * c


def phase_circadienne(heure):
    """
    Classe l'heure d'horloge (0 ≤ heure < 24) selon la phase circadienne dominante.

    Convention chronobiologique (sujet diurne) :
      [2, 4)            -> 'pic_melatonine'
      [22, 24) ∪ [0, 6) -> 'nuit'   (hors pic)
      [6, 22)           -> 'jour'

    heure hors [0, 24) ou non finie -> ValueError.
    """
    h = _reel_fini(heure, "heure")
    if h < 0.0 or h >= 24.0:
        raise ValueError(f"heure hors [0, 24) : {h}")
    # Le pic de mélatonine est un sous-intervalle de la nuit -> testé en premier.
    if 2.0 <= h < 4.0:
        return "pic_melatonine"
    if h >= 22.0 or h < 6.0:
        return "nuit"
    return "jour"
