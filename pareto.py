"""
OPTIMISATION MULTI-OBJECTIF / FRONT DE PARETO — brique Vague 5.

POURQUOI : un vrai design arbitre des objectifs CONCURRENTS (coût, performance, énergie, sûreté) — il n'y a pas un
scalaire à maximiser mais des COMPROMIS. Le front de Pareto = les designs qu'aucun autre ne domine (pas d'amélioration
d'un objectif sans dégrader un autre). C'est l'ensemble des choix rationnels ; choisir dedans est un arbitrage explicite.

MODÈLE : des candidats, chacun avec un vecteur d'objectifs + un SENS par objectif (« min » ou « max »). a DOMINE b
si a est au moins aussi bon sur TOUS les objectifs ET strictement meilleur sur AU MOINS UN.

FAUX=0 :
  • Un candidat est sur le front SSI aucun autre ne le domine — calcul EXACT de la dominance (pas d'heuristique).
  • Aucun compromis fabriqué : on ne renvoie que des candidats fournis, jamais un point interpolé inventé.
  • Déterministe (ordre d'entrée préservé pour les ex æquo).
Stdlib pur, souverain.
"""
from __future__ import annotations


def _meilleur_ou_egal(va, vb, sens):
    return va >= vb if sens == "max" else va <= vb


def _strictement_meilleur(va, vb, sens):
    return va > vb if sens == "max" else va < vb


def domine(a, b, sens) -> bool:
    """a domine b : au moins aussi bon partout ET strictement meilleur quelque part. `a`,`b` = tuples d'objectifs ;
    `sens` = tuple de 'min'/'max' de même longueur."""
    au_moins = all(_meilleur_ou_egal(a[i], b[i], sens[i]) for i in range(len(sens)))
    strict = any(_strictement_meilleur(a[i], b[i], sens[i]) for i in range(len(sens)))
    return au_moins and strict


def front(candidats, sens):
    """Front de Pareto : sous-liste des candidats NON dominés. `candidats` = liste de (etiquette, objectifs) ;
    `sens` = tuple 'min'/'max'. Ordre d'entrée préservé. Déterministe, exact."""
    cand = list(candidats)
    resultat = []
    for i, (eti, obj) in enumerate(cand):
        domine_par_un_autre = False
        for j, (_, obj2) in enumerate(cand):
            if j != i and domine(obj2, obj, sens):
                domine_par_un_autre = True
                break
        if not domine_par_un_autre:
            resultat.append((eti, obj))
    return resultat


def domines(candidats, sens):
    """Les candidats DOMINÉS (le complément du front) — les choix qu'on peut écarter sans regret."""
    f = front(candidats, sens)
    etiquettes_front = {e for e, _ in f}
    return [(e, o) for e, o in candidats if e not in etiquettes_front]
