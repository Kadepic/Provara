"""
entrainement.py — Physiologie de l'entraînement : formules ÉTABLIES (méthodes, efficacité).

Sujet borné « Entraînement (méthodes, efficacité) ». On n'invente AUCUNE valeur : on implémente le
MÉCANISME EXACT des formules reconnues de physiologie de l'effort, qui transforment des entrées mesurées
(charge soulevée, âge, fréquences cardiaques) en grandeurs dérivées. Le résultat est donc EXACT au sens
« la formule est appliquée correctement », arrondi 2 décimales (précision honnête).

Formules / faits sourcés :

  • un_rep_max_epley(poids, repetitions) = poids · (1 + repetitions/30)
      Estimation du 1RM (one-rep max, charge maximale sur une répétition) — formule d'Epley (1985).
      Ex. 100 kg pour 5 reps -> 100·(1 + 5/30) = 100·(35/30) ≈ 116.67 kg.

  • frequence_cardiaque_max(age) = 220 − age
      Fréquence cardiaque maximale prédite par l'âge — formule de Haskell & Fox (1971).
      Ex. 30 ans -> 220 − 30 = 190 bpm.

  • zone_cible_karvonen(fc_repos, age, intensite)
        = fc_repos + intensite · ( (220 − age) − fc_repos )
      Fréquence cardiaque cible par la méthode de Karvonen (réserve de fréquence cardiaque, HRR).
      HRR = FCmax − FCrepos ; cible = FCrepos + intensité · HRR. À intensité 0 -> FCrepos, à 1 -> FCmax.
      Ex. FCrepos 60, 30 ans, intensité 0.7 -> 60 + 0.7·(190 − 60) = 60 + 91 = 151 bpm.

  • vo2max_estime(fc_max, fc_repos) = 15.3 · (fc_max / fc_repos)
      Estimation de la VO2max (mL·kg⁻¹·min⁻¹) par le ratio des fréquences cardiaques —
      Uth, Sørensen, Overgaard & Pedersen (2004). Ex. FCmax 200, FCrepos 50 -> 15.3·4 = 61.2.

ABSTENTION STRUCTURELLE (faux positif INTERDIT — jamais un faux, toujours ValueError) :
  • poids <= 0, ou repetitions < 1, ou non fini                     -> ValueError (Epley).
  • age < 0 ou age > 120, ou non fini                               -> ValueError (FCmax, Karvonen).
  • intensite hors [0, 1], ou non finie                             -> ValueError (Karvonen).
  • fc_repos <= 0 ou fc_repos >= FCmax (réserve non strictement >0) -> ValueError (Karvonen).
  • fc_max <= 0, fc_repos <= 0, ou fc_max <= fc_repos               -> ValueError (VO2max).
  • toute entrée non numérique / booléenne / non finie             -> ValueError.

stdlib uniquement, fonctions pures déterministes.
"""

import math

__all__ = [
    "un_rep_max_epley",
    "frequence_cardiaque_max",
    "zone_cible_karvonen",
    "vo2max_estime",
    "AGE_MAX",
    "FCMAX_CONST_HASKELL",
    "COEFF_UTH_VO2MAX",
]

# ── Constantes / bornes sourcées ──
AGE_MAX = 120.0               # borne d'âge humain plausible (au-delà -> abstention).
FCMAX_CONST_HASKELL = 220.0   # constante de la formule de Haskell & Fox (FCmax = 220 − âge).
COEFF_UTH_VO2MAX = 15.3       # coefficient de l'estimation VO2max d'Uth et al. (2004).

_DECIMALES = 2


def _reel_fini(x, nom):
    """Convertit en float fini ; rejette booléens et non-numériques -> ValueError (jamais un faux)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen interdit : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _arrondi(x):
    """Arrondi déterministe à 2 décimales (précision honnête)."""
    return round(float(x), _DECIMALES)


def un_rep_max_epley(poids, repetitions):
    """
    1RM estimé par la formule d'Epley : poids · (1 + repetitions/30).

    poids       : charge soulevée, > 0 (mêmes unités que la sortie, kg en pratique).
    repetitions : nombre de répétitions effectuées, >= 1.
    poids <= 0, repetitions < 1, ou valeur non finie/non numérique -> ValueError.
    """
    p = _reel_fini(poids, "poids")
    r = _reel_fini(repetitions, "repetitions")
    if p <= 0.0:
        raise ValueError(f"poids non strictement positif : {p}")
    if r < 1.0:
        raise ValueError(f"repetitions < 1 : {r}")
    return _arrondi(p * (1.0 + r / 30.0))


def frequence_cardiaque_max(age):
    """
    Fréquence cardiaque maximale prédite par l'âge (Haskell & Fox) : 220 − age, en bpm.

    age : âge en années, dans [0, 120].
    age < 0, age > 120, ou valeur non finie/non numérique -> ValueError.
    """
    a = _reel_fini(age, "age")
    if a < 0.0 or a > AGE_MAX:
        raise ValueError(f"age hors [0, {AGE_MAX}] : {a}")
    return _arrondi(FCMAX_CONST_HASKELL - a)


def zone_cible_karvonen(fc_repos, age, intensite):
    """
    Fréquence cardiaque cible (bpm) par la méthode de Karvonen (réserve de FC) :
        fc_repos + intensite · ( (220 − age) − fc_repos ).

    fc_repos  : fréquence cardiaque de repos en bpm, > 0 et strictement < FCmax (220 − age).
    age       : âge en années, dans [0, 120].
    intensite : fraction de la réserve visée, dans [0, 1].
    age hors [0,120], intensite hors [0,1], fc_repos <= 0 ou >= FCmax,
    ou toute valeur non finie/non numérique -> ValueError.
    """
    fr = _reel_fini(fc_repos, "fc_repos")
    a = _reel_fini(age, "age")
    i = _reel_fini(intensite, "intensite")
    if a < 0.0 or a > AGE_MAX:
        raise ValueError(f"age hors [0, {AGE_MAX}] : {a}")
    if i < 0.0 or i > 1.0:
        raise ValueError(f"intensite hors [0, 1] : {i}")
    fc_max = FCMAX_CONST_HASKELL - a
    if fr <= 0.0:
        raise ValueError(f"fc_repos non strictement positif : {fr}")
    if fr >= fc_max:
        raise ValueError(f"fc_repos {fr} >= FCmax {fc_max} (réserve non strictement positive)")
    return _arrondi(fr + i * (fc_max - fr))


def vo2max_estime(fc_max, fc_repos):
    """
    VO2max estimée (mL·kg⁻¹·min⁻¹) par le ratio des fréquences cardiaques — Uth et al. (2004) :
        15.3 · (fc_max / fc_repos).

    fc_max   : fréquence cardiaque maximale en bpm, > 0.
    fc_repos : fréquence cardiaque de repos en bpm, > 0 et strictement < fc_max.
    fc_max <= 0, fc_repos <= 0, fc_max <= fc_repos, ou valeur non finie/non numérique -> ValueError.
    """
    fm = _reel_fini(fc_max, "fc_max")
    fr = _reel_fini(fc_repos, "fc_repos")
    if fm <= 0.0:
        raise ValueError(f"fc_max non strictement positif : {fm}")
    if fr <= 0.0:
        raise ValueError(f"fc_repos non strictement positif : {fr}")
    if fm <= fr:
        raise ValueError(f"fc_max {fm} <= fc_repos {fr} (ratio physiologiquement impossible)")
    return _arrondi(COEFF_UTH_VO2MAX * (fm / fr))
