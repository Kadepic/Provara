"""Procedes industriels : bilans de procede (mecanisme exact, deterministe).

Definitions etablies (genie des procedes) :
  - rendement = produit_reel / produit_theorique  (fraction dans [0,1])
  - bilan_matiere : conservation de la masse, Somme(entrees) == Somme(sorties)
    a une tolerance pres (loi de Lavoisier).
  - debit_production = quantite / temps
  - taux_conversion = reactif_consomme / reactif_initial  (fraction dans [0,1])

ABSTENTION STRUCTURELLE : valeurs negatives, denominateurs nuls, ou
incoherences physiques (reel > theorique, consomme > initial) -> ValueError.
Aucune valeur inventee : l'arithmetique est exacte, l'invalide leve.
"""

TOL = 1e-9


def _verifie_nombre(x, nom):
    """Rejette ce qui n'est pas un reel fini."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit etre un nombre reel : {x!r}")
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError(f"{nom} doit etre fini : {x!r}")


def rendement(produit_reel, produit_theorique):
    """Rendement = produit_reel / produit_theorique, dans [0,1].

    ValueError si negatif, si theorique nul, ou si reel > theorique
    (un rendement physique ne peut exceder 100 %).
    """
    _verifie_nombre(produit_reel, "produit_reel")
    _verifie_nombre(produit_theorique, "produit_theorique")
    if produit_reel < 0:
        raise ValueError("produit_reel ne peut etre negatif")
    if produit_theorique <= 0:
        raise ValueError("produit_theorique doit etre strictement positif")
    if produit_reel > produit_theorique + TOL:
        raise ValueError("produit_reel ne peut exceder produit_theorique")
    r = produit_reel / produit_theorique
    if r > 1.0:
        r = 1.0
    return r


def bilan_matiere(entrees, sorties, tol=1e-6):
    """Conservation de la masse : Somme(entrees) == Somme(sorties) a tol pres.

    Renvoie True si conserve, False sinon.
    ValueError si une liste est vide, non iterable, ou contient un negatif.
    """
    for nom, lst in (("entrees", entrees), ("sorties", sorties)):
        if not isinstance(lst, (list, tuple)):
            raise ValueError(f"{nom} doit etre une liste/tuple")
        if len(lst) == 0:
            raise ValueError(f"{nom} ne peut etre vide")
        for v in lst:
            _verifie_nombre(v, f"flux de {nom}")
            if v < 0:
                raise ValueError(f"un flux de {nom} ne peut etre negatif")
    _verifie_nombre(tol, "tol")
    if tol < 0:
        raise ValueError("tol ne peut etre negative")
    return abs(sum(entrees) - sum(sorties)) <= tol


def debit_production(quantite, temps):
    """Debit = quantite / temps. ValueError si negatif ou temps nul."""
    _verifie_nombre(quantite, "quantite")
    _verifie_nombre(temps, "temps")
    if quantite < 0:
        raise ValueError("quantite ne peut etre negative")
    if temps <= 0:
        raise ValueError("temps doit etre strictement positif")
    return quantite / temps


def taux_conversion(reactif_consomme, reactif_initial):
    """Taux de conversion = consomme / initial, dans [0,1].

    ValueError si negatif, si initial nul, ou si consomme > initial.
    """
    _verifie_nombre(reactif_consomme, "reactif_consomme")
    _verifie_nombre(reactif_initial, "reactif_initial")
    if reactif_consomme < 0:
        raise ValueError("reactif_consomme ne peut etre negatif")
    if reactif_initial <= 0:
        raise ValueError("reactif_initial doit etre strictement positif")
    if reactif_consomme > reactif_initial + TOL:
        raise ValueError("reactif_consomme ne peut exceder reactif_initial")
    t = reactif_consomme / reactif_initial
    if t > 1.0:
        t = 1.0
    return t
