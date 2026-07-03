"""
PIB, CROISSANCE — identités de la comptabilité nationale (mécanisme EXACT, jamais une valeur-pays inventée).

Posture FAUX=0 (même esprit que `physique` / `chimie`) :
  • Le MÉCANISME est une IDENTITÉ COMPTABLE exacte (définition du PIB par les dépenses, taux de croissance,
    PIB par habitant, PIB réel via le déflateur). On NE stocke AUCUNE valeur-pays « inventée » : on calcule
    sur les composantes fournies par l'appelant.
  • La sortie est ARRONDIE (6 décimales) — déterministe, pas de bruit de représentation flottante.
  • Entrée invalide (non numérique, NaN/inf, population ≤ 0, déflateur ≤ 0, base de croissance ≤ 0)
    -> ValueError. On S'ABSTIENT, jamais un faux.

Les quatre fonctions sont pures et déterministes. Aucune ne devine une donnée manquante.
"""
from __future__ import annotations

import math

_DECIMALES = 6


def _num(x, nom: str) -> float:
    """Exige un réel fini (rejette bool, NaN, inf, non-numérique) -> ValueError sinon."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : booléen interdit")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : type non numérique ({type(x).__name__})")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} : valeur non finie (NaN/inf)")
    return xf


def _arr(x: float) -> float:
    """Arrondi déterministe à 6 décimales (normalise -0.0 en 0.0)."""
    r = round(x, _DECIMALES)
    return 0.0 if r == 0.0 else r


def pib_depenses(consommation: float, investissement: float, depenses_publiques: float,
                 exportations: float, importations: float) -> float:
    """PIB par l'approche des dépenses : PIB = C + I + G + (X − M).

    Identité comptable exacte. Les composantes peuvent être de signe quelconque (les exportations nettes
    X − M et la variation de stocks dans I peuvent être négatives) : la somme reste exacte.
    """
    c = _num(consommation, "consommation")
    i = _num(investissement, "investissement")
    g = _num(depenses_publiques, "depenses_publiques")
    x = _num(exportations, "exportations")
    m = _num(importations, "importations")
    return _arr(c + i + g + (x - m))


def taux_croissance(pib_initial: float, pib_final: float) -> float:
    """Taux de croissance en % : (final − initial) / initial · 100.

    La base `pib_initial` doit être strictement positive (un PIB nul ou négatif ne fournit pas de base
    de croissance définie) -> ValueError sinon.
    """
    i = _num(pib_initial, "pib_initial")
    f = _num(pib_final, "pib_final")
    if i <= 0:
        raise ValueError("pib_initial doit être strictement positif")
    return _arr((f - i) / i * 100.0)


def pib_par_habitant(pib: float, population: float) -> float:
    """PIB par habitant : PIB / population.

    population ≤ 0 -> ValueError (division impossible / sans sens).
    """
    p = _num(pib, "pib")
    pop = _num(population, "population")
    if pop <= 0:
        raise ValueError("population doit être strictement positive")
    return _arr(p / pop)


def pib_reel(pib_nominal: float, deflateur: float) -> float:
    """PIB réel : nominal · 100 / déflateur (déflateur en base 100).

    déflateur ≤ 0 -> ValueError.
    """
    n = _num(pib_nominal, "pib_nominal")
    d = _num(deflateur, "deflateur")
    if d <= 0:
        raise ValueError("deflateur doit être strictement positif")
    return _arr(n * 100.0 / d)
