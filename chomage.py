"""
chomage.py — Marché du travail : indicateurs du Bureau International du Travail (BIT/ILO).

Mécanismes EXACTS / définitions normatives BIT (résolutions de la CIST — Conférence Internationale
des Statisticiens du Travail ; reprises par Eurostat / INSEE / OIT). Chaque indicateur est un RATIO
arithmétique exact entre des EFFECTIFS observés (nombres de personnes). Aucune estimation, aucune
heuristique, aucune valeur-pays inventée : seul le CALCUL est implémenté.

DÉFINITIONS (effectifs de personnes, comptages) :
  • population_active(actifs_occupes, chomeurs) = actifs_occupes + chomeurs
      Population active = « force de travail » au sens BIT = personnes en emploi (actifs occupés)
      PLUS personnes au chômage (sans emploi, disponibles, en recherche active). C'est une IDENTITÉ
      comptable : tout chômeur fait, par définition, partie de la population active.
      Ex. 22.5M occupés + 2.5M chômeurs = 25M actifs.

  • taux_chomage(chomeurs, population_active) = chomeurs / population_active * 100
      Part des chômeurs DANS la population active (et non dans la population totale) — définition BIT.
      Ex. 2.5M chômeurs / 25M actifs = 10 %.
      Un chômeur est nécessairement un actif -> 0 <= chomeurs <= population_active, taux dans [0, 100].

  • taux_activite(population_active, population_age_travailler) = population_active / PAT * 100
      Part de la population en âge de travailler (PAT, typiquement 15-64 ans) qui est active
      (occupée ou au chômage). Tout actif est en âge de travailler au sens de l'indicateur
      -> 0 <= population_active <= PAT, taux dans [0, 100].
      Ex. 30M actifs / 40M PAT = 75 %.

  • taux_emploi(actifs_occupes, population_age_travailler) = actifs_occupes / PAT * 100
      Part de la PAT qui occupe effectivement un emploi (« employment rate »).
      Tout occupé est compté dans la PAT -> 0 <= actifs_occupes <= PAT, taux dans [0, 100].
      Ex. 27M occupés / 40M PAT = 67.5 %.

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • population_active <= 0 (pas de force de travail -> taux de chômage indéfini) -> ValueError.
  • chomeurs < 0, ou chomeurs > population_active (taux > 100 %, impossible) -> ValueError.
  • effectif négatif (actifs_occupes, chomeurs, PAT, population_active) -> ValueError.
  • PAT <= 0 (dénominateur des taux d'activité/emploi nul) -> ValueError.
  • population_active > PAT, ou actifs_occupes > PAT (taux > 100 %, impossible) -> ValueError.
  • valeur non finie / non numérique -> ValueError.

Sorties arrondies à 6 décimales. stdlib uniquement, fonctions pures déterministes.
"""

import math

__all__ = [
    "population_active",
    "taux_chomage",
    "taux_activite",
    "taux_emploi",
]

_PRECISION = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen refusé : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _effectif(x, nom):
    """Effectif de personnes : float fini >= 0, sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} doit être >= 0 (effectif) : {v}")
    return v


def population_active(actifs_occupes, chomeurs):
    """Population active (force de travail) = actifs occupés + chômeurs (identité comptable BIT)."""
    occ = _effectif(actifs_occupes, "actifs_occupes")
    cho = _effectif(chomeurs, "chomeurs")
    return round(occ + cho, _PRECISION)


def taux_chomage(chomeurs, population_active):
    """Taux de chômage BIT = chômeurs / population active * 100 (en %)."""
    cho = _effectif(chomeurs, "chomeurs")
    act = _effectif(population_active, "population_active")
    if act <= 0.0:
        raise ValueError("population_active doit être > 0 (taux de chômage indéfini sinon)")
    if cho > act:
        raise ValueError(f"chomeurs ({cho}) > population_active ({act}) : taux > 100 % impossible")
    return round(cho / act * 100.0, _PRECISION)


def taux_activite(population_active, population_age_travailler):
    """Taux d'activité = population active / population en âge de travailler * 100 (en %)."""
    act = _effectif(population_active, "population_active")
    pat = _effectif(population_age_travailler, "population_age_travailler")
    if pat <= 0.0:
        raise ValueError("population_age_travailler doit être > 0")
    if act > pat:
        raise ValueError(
            f"population_active ({act}) > population_age_travailler ({pat}) : taux > 100 % impossible"
        )
    return round(act / pat * 100.0, _PRECISION)


def taux_emploi(actifs_occupes, population_age_travailler):
    """Taux d'emploi = actifs occupés / population en âge de travailler * 100 (en %)."""
    occ = _effectif(actifs_occupes, "actifs_occupes")
    pat = _effectif(population_age_travailler, "population_age_travailler")
    if pat <= 0.0:
        raise ValueError("population_age_travailler doit être > 0")
    if occ > pat:
        raise ValueError(
            f"actifs_occupes ({occ}) > population_age_travailler ({pat}) : taux > 100 % impossible"
        )
    return round(occ / pat * 100.0, _PRECISION)
