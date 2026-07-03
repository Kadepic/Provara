"""
PLANIFICATION MULTI-ÉTAPES — brique Vague 5. Enchaîner des actions vérifiées vers un but (assemblage, procédé).

POURQUOI : concevoir/fabriquer, c'est trouver une SUITE d'actions qui mène d'un état initial à un but. La machine
doit planifier : chercher dans l'espace des états atteignables la séquence d'opérateurs qui satisfait l'objectif.

MODÈLE : un état = un frozenset de littéraux (faits vrais). Un opérateur = (nom, préconditions, ajouts, retraits)
au sens STRIPS. Recherche en LARGEUR (BFS) = plan de longueur minimale, déterministe.

FAUX=0 :
  • Le plan RENVOYÉ est RE-JOUÉ depuis l'état initial et doit RÉELLEMENT atteindre le but (vérification finale) —
    jamais un plan qui « devrait » marcher.
  • Un opérateur ne s'applique que si ses préconditions sont satisfaites (jamais forcé).
  • Pas de plan atteignable -> None HONNÊTE (jamais une séquence fabriquée). Recherche BORNÉE (profondeur/états max)
    -> terminante ; si le budget est épuisé sans solution, on renvoie None (on ne prétend pas l'absence de solution
    au-delà du budget, on ne fabrique rien).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

from collections import deque


class Operateur:
    __slots__ = ("nom", "pre", "ajoute", "retire")

    def __init__(self, nom, pre=(), ajoute=(), retire=()):
        self.nom = nom
        self.pre = frozenset(pre)
        self.ajoute = frozenset(ajoute)
        self.retire = frozenset(retire)

    def applicable(self, etat: frozenset) -> bool:
        return self.pre <= etat

    def applique(self, etat: frozenset) -> frozenset:
        return (etat - self.retire) | self.ajoute


def _atteint(etat: frozenset, but: frozenset) -> bool:
    return but <= etat


def plan(etat_initial, but, operateurs, max_etats: int = 100000):
    """Plan (liste de noms d'opérateurs) de longueur minimale de `etat_initial` vers `but`, ou None. BFS déterministe.
    Le plan renvoyé est RE-VÉRIFIÉ (rejoué) avant d'être retourné (FAUX=0)."""
    depart = frozenset(etat_initial)
    but = frozenset(but)
    if _atteint(depart, but):
        return []
    vus = {depart}
    file = deque([(depart, [])])
    ops = list(operateurs)
    explores = 0
    while file and explores < max_etats:
        etat, chemin = file.popleft()
        explores += 1
        for op in ops:                           # ordre fixe -> déterminisme
            if op.applicable(etat):
                suiv = op.applique(etat)
                if suiv in vus:
                    continue
                nouveau_chemin = chemin + [op.nom]
                if _atteint(suiv, but):
                    if _verifie(depart, but, nouveau_chemin, ops):   # RE-JEU (FAUX=0)
                        return nouveau_chemin
                vus.add(suiv)
                file.append((suiv, nouveau_chemin))
    return None                                  # pas de plan (ou budget épuisé) -> honnête


def _verifie(depart, but, noms, operateurs) -> bool:
    """Rejoue la séquence depuis l'état initial ; True ssi chaque opérateur est applicable en séquence ET le but
    est atteint à la fin. C'est la garantie FAUX=0 : on ne renvoie pas un plan qui ne se déroule pas réellement."""
    par_nom = {}
    for op in operateurs:
        par_nom.setdefault(op.nom, op)
    etat = depart
    for nom in noms:
        op = par_nom.get(nom)
        if op is None or not op.applicable(etat):
            return False
        etat = op.applique(etat)
    return _atteint(etat, but)


def atteignable(etat_initial, but, operateurs, max_etats: int = 100000) -> bool:
    return plan(etat_initial, but, operateurs, max_etats) is not None
