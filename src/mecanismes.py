"""
CONCEPTION MÉCANIQUE — transmission de mouvement et de force (mandat Yohan : couvrir le borné « FORMULE »).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est EXACT — ce sont des identités cinématiques/statiques élémentaires, sans approximation :
        - train d'engrenages : rapport de réduction i = Z_menée / Z_menante (conservation du produit Z·ω) ;
        - vitesse de sortie : ω_s = ω_e · Z_menante / Z_menée (la roue menante entraîne la menée) ;
        - levier (loi de l'avantage mécanique) : AM = bras_force / bras_charge (moments à l'équilibre) ;
        - couple de sortie d'un réducteur idéal : C_s = C_e · i (la puissance se conserve, ω chute de i, C monte de i).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision HONNÊTE (on ne fabrique pas de décimales).
  • Pas de pertes : ces formules décrivent la transmission IDÉALE (rendement = 1), convention explicite du module.

GARANTIES (vérifiées en adverse par `valide_mecanismes.py`) :
  - nombre de dents ≤ 0, bras ≤ 0, rapport ≤ 0 -> ValueError (ABSTENTION structurelle, jamais un nombre absurde) ;
  - type non numérique (ou bool) -> ValueError ;
  - non-fini (inf/NaN) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

CAS DE RÉFÉRENCE (cf. validateur) : engrenage 10→40 dents -> rapport 4, vitesse ÷4, couple ×4 ; levier bras 4/1 -> AM=4.
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num_fini(x) -> bool:
    """True ssi x est un nombre réel fini (et PAS un bool — bool est sous-classe d'int)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> float:
    if not _num_fini(x):
        raise ValueError(f"{nom} doit être un nombre fini, reçu {x!r}")
    if x <= 0:
        raise ValueError(f"{nom} doit être strictement positif, reçu {x!r}")
    return float(x)


def _exige_fini(x, nom: str) -> float:
    if not _num_fini(x):
        raise ValueError(f"{nom} doit être un nombre fini, reçu {x!r}")
    return float(x)


# ── TRANSMISSIONS ────────────────────────────────────────────────────────────────────────────────────────────────

def rapport_engrenages(dents_menante, dents_menee) -> float:
    """Rapport de réduction i = Z_menée / Z_menante (>1 = réducteur). Dents ≤ 0 -> ValueError."""
    zme = _exige_positif(dents_menante, "dents_menante")
    zmd = _exige_positif(dents_menee, "dents_menee")
    return _sig(zmd / zme)


def vitesse_sortie(vitesse_entree, dents_men, dents_mene) -> float:
    """ω_sortie = ω_entree · Z_menante / Z_menée (la menante entraîne la menée). Dents ≤ 0 -> ValueError.

    La vitesse d'entrée peut être nulle ou négative (sens de rotation), mais doit être finie.
    """
    we = _exige_fini(vitesse_entree, "vitesse_entree")
    zme = _exige_positif(dents_men, "dents_men")
    zmd = _exige_positif(dents_mene, "dents_mene")
    return _sig(we * zme / zmd)


def avantage_mecanique_levier(bras_force, bras_charge) -> float:
    """Avantage mécanique d'un levier AM = bras_force / bras_charge (équilibre des moments). Bras ≤ 0 -> ValueError."""
    bf = _exige_positif(bras_force, "bras_force")
    bc = _exige_positif(bras_charge, "bras_charge")
    return _sig(bf / bc)


def couple_sortie(couple_entree, rapport) -> float:
    """Couple de sortie d'un réducteur idéal C_sortie = C_entree · rapport. Rapport ≤ 0 -> ValueError.

    Le couple d'entrée peut être nul ou négatif (sens), mais doit être fini ; le rapport est strictement positif.
    """
    ce = _exige_fini(couple_entree, "couple_entree")
    r = _exige_positif(rapport, "rapport")
    return _sig(ce * r)
