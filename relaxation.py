"""
RELAXATION DE CONTRAINTE / RÉSOLUTION DE CONTRADICTION — brique Vague 5 (esprit TRIZ). Dépend de contrainte.py.

POURQUOI : le geste d'invention par excellence. Un problème sur-contraint (aucun design ne satisfait tout) devient
soluble si on identifie la contrainte à LEVER (ou à repenser). « Sans grosse sortie d'air » est une contrainte ; savoir
qu'en la relâchant l'espace de design se rouvre est exactement ce qu'un humain, fixé, ne fait pas spontanément.

MODÈLE : sur un CSP INSATISFIABLE, cherche le PLUS PETIT sous-ensemble de contraintes dont le retrait rend le problème
SATISFIABLE (ensemble de correction minimal). Recherche par taille croissante (1, 2, …), déterministe.

FAUX=0 :
  • Le sous-ensemble renvoyé rend RÉELLEMENT le CSP satisfiable — VÉRIFIÉ en résolvant le CSP réduit (dont la solution
    est elle-même re-vérifiée par contrainte.py). Jamais une relaxation « supposée » suffisante.
  • MINIMAL : aucun sous-ensemble plus petit ne suffit (recherche par taille croissante).
  • Si le CSP est déjà satisfiable -> [] (rien à relâcher). Recherche bornée -> terminante.
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

from itertools import combinations

from contrainte import CSP


def _csp_sans(csp: CSP, indices_retires: set) -> CSP:
    """Reconstruit un CSP identique privé des contraintes d'indices donnés."""
    reduit = CSP()
    for nom in csp._ordre:
        reduit.variable(nom, csp._domaines[nom])
    for i, c in enumerate(csp._contraintes):
        if i not in indices_retires:
            reduit.contrainte(c.portee, c.predicat, c.nom)
    return reduit


def relache_minimal(csp: CSP, taille_max: int = None):
    """Plus petit ensemble de contraintes à retirer pour rendre `csp` satisfiable. Renvoie
    {contraintes_a_relacher: [noms], solution: dict} ou None si même en tout relâchant ça reste UNSAT (domaines
    vides), ou {[], solution} si déjà satisfiable. Déterministe."""
    sol = csp.resout()
    if sol is not None:
        return {"contraintes_a_relacher": [], "solution": sol}
    n = len(csp._contraintes)
    hi = n if taille_max is None else min(taille_max, n)
    for k in range(1, hi + 1):
        for combo in combinations(range(n), k):
            reduit = _csp_sans(csp, set(combo))
            sol = reduit.resout()                # re-vérifie la solution (FAUX=0)
            if sol is not None:
                return {"contraintes_a_relacher": [csp._contraintes[i].nom for i in combo],
                        "solution": sol}
    return None                                  # même sans aucune contrainte, insoluble (domaine vide) -> honnête


def conflit(csp: CSP):
    """Les noms des contraintes du plus petit ensemble en conflit (celui à relâcher). [] si satisfiable, None si
    structurellement insoluble."""
    r = relache_minimal(csp)
    return None if r is None else r["contraintes_a_relacher"]
