"""
demographie.py — Démographie (populations, faits) : indicateurs démographiques EXACTS.

Sujet PARTIELLEMENT factuel : on N'INVENTE PAS de valeurs-pays (population de tel pays, etc.).
On implémente les DÉFINITIONS / CALCULS démographiques standard — le MÉCANISME est exact, la
réponse est entièrement déterminée par les ENTRÉES observées (comptages, indices). Aucune donnée
de pays codée en dur, aucune estimation, aucune heuristique.

Mécanismes EXACTS (définitions de manuel de démographie / INED / ONU) :

  • taux_croissance_naturel(natalite, mortalite) = (natalité − mortalité) / 1000
      Taux d'accroissement naturel. natalité et mortalité sont des taux POUR MILLE (‰), c.-à-d.
      naissances (resp. décès) pour 1000 habitants. La différence /1000 donne le taux net annuel.
      Ex. (20 − 8) / 1000 = 0.012  (= +1.2 %/an).
      Le résultat PEUT être négatif (décroissance naturelle, décès > naissances) : c'est un fait réel,
      on ne le rejette pas. (INED, "taux d'accroissement naturel".)

  • densite_population(population, surface_km2) = population / surface_km2
      Densité = habitants par km². Ex. 1 000 000 / 500 = 2000 hab/km².
      surface_km2 doit être > 0 (dénominateur). population >= 0.

  • temps_doublement(taux_croissance_pct) = 70 / taux_croissance_pct
      "Règle des 70" : durée approchée (en années) pour qu'une population croissant au taux
      constant 'taux_croissance_pct' (en %) double. Dérive de ln(2)/ln(1+r) ≈ 70/(100·r).
      Ex. 70 / 2 = 35 ans à 2 %/an. Exige un taux > 0 (sans croissance, pas de doublement).

  • taux_dependance(jeunes, ages, actifs) = (jeunes + âgés) / actifs · 100
      Ratio de dépendance démographique : population dépendante (jeunes < 15 ans + âgés >= 65 ans)
      rapportée à la population en âge de travailler (15–64 ans), en %.
      Ex. (30 + 20) / 50 · 100 = 100  (autant de dépendants que d'actifs). actifs > 0 (dénominateur).

  • indice_fecondite(taux_par_age, largeur_classe=5) = largeur_classe · Σ(taux_par_age) / 1000
      Indice synthétique de fécondité (ISF / TFR) : nombre moyen d'enfants par femme si elle
      connaissait, à chaque âge, les taux de fécondité par âge (ASFR) de l'année courante.
      'taux_par_age' = séquence des taux de fécondité par classe d'âge, EXPRIMÉS POUR 1000 FEMMES.
      'largeur_classe' = amplitude (en années) de chaque classe d'âge (5 pour les groupes
      quinquennaux 15–19, 20–24, …, 45–49). C'est une SOMME exacte, pas une estimation.
      Ex. 7 classes quinquennales à 60 ‰ : 5 · (7·60) / 1000 = 2.1 enfants/femme (seuil de
      remplacement des générations). (ONU, "Total Fertility Rate".)

ABSTENTION STRUCTURELLE (faux positif INTERDIT — jamais un faux -> ValueError) :
  • surface_km2 <= 0, actifs <= 0, taux_croissance_pct <= 0, largeur_classe <= 0 -> ValueError ;
  • toute quantité négative (population, natalité, mortalité, jeunes, âgés, taux de fécondité) -> ValueError ;
  • séquence de taux vide / non itérable -> ValueError ;
  • toute valeur non finie (NaN, ±inf) ou non numérique -> ValueError.

Sorties arrondies à 6 décimales. stdlib uniquement. Fonctions pures déterministes.
"""

import math

__all__ = [
    "taux_croissance_naturel",
    "densite_population",
    "temps_doublement",
    "taux_dependance",
    "indice_fecondite",
]

_PRECISION = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    if isinstance(x, bool):  # True/False n'est pas une quantité démographique
        raise ValueError(f"{nom} booléen : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _non_negatif(x, nom):
    """float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} négatif : {v}")
    return v


def _positif(x, nom):
    """float fini > 0 (dénominateur / amplitude), sinon ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} non strictement positif : {v}")
    return v


def taux_croissance_naturel(natalite, mortalite):
    """
    Taux d'accroissement naturel = (natalité − mortalité) / 1000.

    natalité, mortalité : taux pour mille (‰), >= 0. Résultat possiblement négatif (décroissance).
    Valeur négative en entrée, non finie ou non numérique -> ValueError.
    """
    n = _non_negatif(natalite, "natalite")
    m = _non_negatif(mortalite, "mortalite")
    return round((n - m) / 1000.0, _PRECISION)


def densite_population(population, surface_km2):
    """
    Densité de population = population / surface_km2 (hab/km²).

    population  : nombre d'habitants, >= 0.
    surface_km2 : superficie, > 0 (dénominateur).
    population < 0, surface_km2 <= 0, valeurs non finies / non numériques -> ValueError.
    """
    p = _non_negatif(population, "population")
    s = _positif(surface_km2, "surface_km2")
    return round(p / s, _PRECISION)


def temps_doublement(taux_croissance_pct):
    """
    Temps de doublement (règle des 70) = 70 / taux_croissance_pct, en années.

    taux_croissance_pct : taux de croissance annuel en POURCENT, > 0 (sans croissance positive,
    pas de doublement -> abstention). taux <= 0, non fini / non numérique -> ValueError.
    """
    t = _positif(taux_croissance_pct, "taux_croissance_pct")
    return round(70.0 / t, _PRECISION)


def taux_dependance(jeunes, ages, actifs):
    """
    Ratio de dépendance démographique = (jeunes + âgés) / actifs · 100, en %.

    jeunes : population jeune (< 15 ans), >= 0.
    ages   : population âgée (>= 65 ans), >= 0.
    actifs : population en âge de travailler (15–64 ans), > 0 (dénominateur).
    Entrée négative, actifs <= 0, valeurs non finies / non numériques -> ValueError.
    """
    j = _non_negatif(jeunes, "jeunes")
    a = _non_negatif(ages, "ages")
    act = _positif(actifs, "actifs")
    return round((j + a) / act * 100.0, _PRECISION)


def indice_fecondite(taux_par_age, largeur_classe=5):
    """
    Indice synthétique de fécondité (ISF / TFR) = largeur_classe · Σ(taux_par_age) / 1000.

    taux_par_age   : séquence (non vide) de taux de fécondité par âge, POUR 1000 FEMMES, chacun >= 0.
    largeur_classe : amplitude en années de chaque classe d'âge, > 0 (5 pour groupes quinquennaux).
    Séquence vide / non itérable, taux négatif, largeur <= 0, valeur non finie / non numérique -> ValueError.
    """
    if isinstance(taux_par_age, (str, bytes)):
        raise ValueError(f"taux_par_age doit être une séquence de nombres, pas {type(taux_par_age).__name__}")
    try:
        taux = list(taux_par_age)
    except TypeError:
        raise ValueError(f"taux_par_age non itérable : {taux_par_age!r}")
    if not taux:
        raise ValueError("taux_par_age vide : aucun taux de fécondité fourni")
    largeur = _positif(largeur_classe, "largeur_classe")
    somme = 0.0
    for i, t in enumerate(taux):
        somme += _non_negatif(t, f"taux_par_age[{i}]")
    return round(largeur * somme / 1000.0, _PRECISION)
