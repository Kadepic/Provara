"""
comptabilite.py — Comptabilité (règles) : équations et ratios comptables ÉTABLIS, exacts.

Mécanismes EXACTS / définitions standard (comptabilité générale, principe de la partie double).
Chaque fonction est une identité ou un ratio arithmétique exact entre des grandeurs observées
(montants monétaires, postes du bilan ou du compte de résultat). Aucune estimation, aucune
heuristique, aucune valeur inventée — seulement la RÈGLE.

  • equation_bilan(actif, passif, capitaux_propres) -> bool
      Équation fondamentale du bilan : Actif = Passif (dettes) + Capitaux propres.
      VÉRIFIE l'égalité (le bilan est équilibré) et renvoie True/False.
      Ex. Actif 100 = Passif 60 + Capitaux propres 40 -> True.
      (PCG / IFRS : identité comptable de base, "accounting equation".)

  • resultat_net(produits, charges) = produits - charges
      Résultat net de l'exercice : excédent des produits sur les charges.
      Ex. 150 - 120 = 30 (bénéfice). Peut être NÉGATIF (perte) si charges > produits.
      (Compte de résultat, PCG.)

  • fonds_roulement(actif_circulant, passif_circulant) = AC - PC
      Fonds de roulement net global : marge de sécurité financière à court terme.
      Ex. 100 - 60 = 40. Peut être NÉGATIF (besoin de financement) si PC > AC.
      (Analyse financière, équilibre du bilan.)

  • ratio_liquidite(actif_circulant, passif_circulant) = AC / PC
      Ratio de liquidité générale (current ratio) : capacité à couvrir les dettes
      à court terme avec les actifs à court terme.
      Ex. 100 / 50 = 2.0. (Analyse financière standard.)

  • partie_double(debits, credits) -> bool
      Principe de la partie double : toute écriture est équilibrée -> Σ débits = Σ crédits.
      Ex. débits [60, 40] et crédits [100] -> Σ = 100 = 100 -> True.
      (Luca Pacioli, 1494 ; fondement de la tenue de comptes.)

ABSTENTION STRUCTURELLE (faux positif INTERDIT, jamais un faux -> ValueError) :
  • Valeur négative (montant, poste) -> ValueError. Les comptages/montants comptables
    sont >= 0 ; seuls les RÉSULTATS dérivés (resultat_net, fonds_roulement) peuvent l'être.
  • passif_circulant <= 0 pour ratio_liquidite (dénominateur) -> ValueError.
  • partie_double : liste de débits ou de crédits vide / non-itérable -> ValueError.
  • Toute valeur non finie / non numérique -> ValueError.

Égalités comparées avec tolérance (rel 1e-9, abs 1e-6) : robustes au bruit flottant des
montants au centime, mais un écart réel (ex. d'un centime) reste détecté comme déséquilibre.
Sorties numériques arrondies à 6 décimales. stdlib uniquement, fonctions pures déterministes.
"""

import math

__all__ = [
    "equation_bilan",
    "resultat_net",
    "fonds_roulement",
    "ratio_liquidite",
    "partie_double",
]

_PRECISION = 6
_REL_TOL = 1e-9
_ABS_TOL = 1e-6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError (abstention)."""
    if isinstance(x, bool):
        # un booléen n'est pas un montant comptable
        raise ValueError(f"{nom} non numérique (booléen) : {x!r}")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _non_negatif(x, nom):
    """float fini >= 0 (montant/poste comptable), sinon ValueError."""
    v = _reel_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} négatif (montant comptable invalide) : {v}")
    return v


def _denominateur_positif(x, nom):
    """float fini > 0 (dénominateur), sinon ValueError."""
    v = _reel_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} non strictement positif (dénominateur) : {v}")
    return v


def _egal(a, b):
    """Égalité comptable robuste au bruit flottant (un écart réel reste détecté)."""
    return math.isclose(a, b, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)


def equation_bilan(actif, passif, capitaux_propres):
    """
    Équation du bilan : VÉRIFIE Actif = Passif + Capitaux propres -> bool.

    actif, passif, capitaux_propres : postes du bilan, >= 0.
    Renvoie True si le bilan est équilibré (à la tolérance flottante près), False sinon.
    Valeur négative / non finie / non numérique -> ValueError.
    """
    a = _non_negatif(actif, "actif")
    p = _non_negatif(passif, "passif")
    cp = _non_negatif(capitaux_propres, "capitaux_propres")
    return _egal(a, p + cp)


def resultat_net(produits, charges):
    """
    Résultat net = produits - charges.

    produits, charges : >= 0. Le résultat peut être négatif (perte).
    Valeur négative / non finie / non numérique -> ValueError.
    """
    pr = _non_negatif(produits, "produits")
    ch = _non_negatif(charges, "charges")
    return round(pr - ch, _PRECISION)


def fonds_roulement(actif_circulant, passif_circulant):
    """
    Fonds de roulement = actif circulant - passif circulant.

    actif_circulant, passif_circulant : >= 0. Le résultat peut être négatif.
    Valeur négative / non finie / non numérique -> ValueError.
    """
    ac = _non_negatif(actif_circulant, "actif_circulant")
    pc = _non_negatif(passif_circulant, "passif_circulant")
    return round(ac - pc, _PRECISION)


def ratio_liquidite(actif_circulant, passif_circulant):
    """
    Ratio de liquidité générale = actif circulant / passif circulant.

    actif_circulant : >= 0 ; passif_circulant : > 0 (dénominateur).
    passif_circulant <= 0, valeur négative / non finie / non numérique -> ValueError.
    """
    ac = _non_negatif(actif_circulant, "actif_circulant")
    pc = _denominateur_positif(passif_circulant, "passif_circulant")
    return round(ac / pc, _PRECISION)


def partie_double(debits, credits):
    """
    Principe de la partie double : VÉRIFIE Σ débits = Σ crédits -> bool.

    debits, credits : itérables (liste/tuple) NON vides de montants >= 0.
    Renvoie True si l'écriture est équilibrée (à la tolérance flottante près), False sinon.
    Itérable vide / non-itérable, montant négatif / non fini / non numérique -> ValueError.
    """
    if not isinstance(debits, (list, tuple)) or not isinstance(credits, (list, tuple)):
        raise ValueError("debits et credits doivent être des listes/tuples de montants")
    if len(debits) == 0 or len(credits) == 0:
        raise ValueError("une écriture en partie double exige au moins un débit et un crédit")
    somme_debits = sum(_non_negatif(d, f"debit[{i}]") for i, d in enumerate(debits))
    somme_credits = sum(_non_negatif(c, f"credit[{i}]") for i, c in enumerate(credits))
    return _egal(somme_debits, somme_credits)
