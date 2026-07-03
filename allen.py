"""
ALGÈBRE D'INTERVALLES D'ALLEN — référentiel TEMPOREL (brique représentation, 2026-07-02).

POURQUOI : situer des événements/faits dans le temps et raisonner sur leur ORDRE relatif (avant/pendant/chevauche…)
sans arithmétique floue. Entre deux intervalles propres [début, fin] (début < fin), il existe EXACTEMENT 13 relations
qualitatives possibles (Allen 1983), mutuellement exclusives et exhaustives. C'est le socle du raisonnement temporel :
« le mandat de X a-t-il chevauché celui de Y ? », « la cause précède-t-elle l'effet ? ».

FAUX=0 :
  • Les 13 relations sont MUTUELLEMENT EXCLUSIVES et EXHAUSTIVES : `relation(a,b)` rend TOUJOURS exactement une
    (jamais zéro, jamais deux) pour deux intervalles PROPRES — comparaisons exactes déterministes, aucune tolérance.
  • Intervalle mal formé (début ≥ fin, borne non comparable) -> ValueError (jamais un verdict faux sur un intervalle dégénéré).
  • L'inverse est exact : relation(a,b) est la relation-miroir de relation(b,a) (table involutive vérifiée).
Stdlib pur, déterministe, souverain. Bornes = tout type ordonné (nombres, dates ISO comparables comme str).
"""
from __future__ import annotations

# Les 13 relations (codes canoniques d'Allen) + leur inverse.
BEFORE = "before"; AFTER = "after"                 # b / bi : a entièrement avant b
MEETS = "meets"; MET_BY = "met_by"                 # m / mi : a.fin == b.début
OVERLAPS = "overlaps"; OVERLAPPED_BY = "overlapped_by"   # o / oi : chevauchement partiel
STARTS = "starts"; STARTED_BY = "started_by"       # s / si : même début
DURING = "during"; CONTAINS = "contains"           # d / di : a strictement inclus dans b
FINISHES = "finishes"; FINISHED_BY = "finished_by" # f / fi : même fin
EQUALS = "equals"                                  # eq : intervalles identiques

RELATIONS = (BEFORE, AFTER, MEETS, MET_BY, OVERLAPS, OVERLAPPED_BY,
             STARTS, STARTED_BY, DURING, CONTAINS, FINISHES, FINISHED_BY, EQUALS)

_INVERSE = {
    BEFORE: AFTER, AFTER: BEFORE, MEETS: MET_BY, MET_BY: MEETS,
    OVERLAPS: OVERLAPPED_BY, OVERLAPPED_BY: OVERLAPS, STARTS: STARTED_BY, STARTED_BY: STARTS,
    DURING: CONTAINS, CONTAINS: DURING, FINISHES: FINISHED_BY, FINISHED_BY: FINISHES, EQUALS: EQUALS,
}


def inverse(rel: str) -> str:
    """Relation-miroir : `inverse(relation(a,b)) == relation(b,a)`. ValueError si `rel` inconnue."""
    if rel not in _INVERSE:
        raise ValueError(f"relation d'Allen inconnue : {rel!r}")
    return _INVERSE[rel]


def _valide(intervalle):
    a1, a2 = intervalle
    if not (a1 < a2):                                # exige un intervalle PROPRE (durée non nulle, bornes ordonnées)
        raise ValueError(f"intervalle mal formé (début doit être < fin) : {intervalle!r}")
    return a1, a2


def relation(a, b) -> str:
    """Relation d'Allen de `a` vers `b`, chacun un couple (début, fin) propre. Rend EXACTEMENT une des 13
    (déterministe, exact). ValueError si un intervalle est mal formé. Bornes = tout type mutuellement ordonnable."""
    a1, a2 = _valide(a)
    b1, b2 = _valide(b)
    # arbre de décision EXHAUSTIF et EXCLUSIF sur les positions relatives des 4 bornes (comparaisons exactes)
    if a2 < b1:
        return BEFORE
    if a2 == b1:
        return MEETS
    if a1 > b2:
        return AFTER
    if a1 == b2:
        return MET_BY
    # ici les intervalles se recouvrent (a1 <= b2 et b1 <= a2, avec au moins un recouvrement strict)
    if a1 == b1:
        return EQUALS if a2 == b2 else (STARTS if a2 < b2 else STARTED_BY)
    if a2 == b2:
        return FINISHES if a1 > b1 else FINISHED_BY
    if a1 < b1:
        return CONTAINS if a2 > b2 else OVERLAPS      # a1<b1 : a commence avant b
    # a1 > b1
    return DURING if a2 < b2 else OVERLAPPED_BY        # a1>b1 : a commence après b


def avant(a, b) -> bool:
    """`a` est-il ENTIÈREMENT avant `b` (sans contact) ?"""
    return relation(a, b) == BEFORE


def chevauche(a, b) -> bool:
    """`a` et `b` partagent-ils un instant intérieur (toute relation sauf before/after/meets/met_by) ?"""
    return relation(a, b) not in (BEFORE, AFTER, MEETS, MET_BY)


def contient(a, b) -> bool:
    """`a` contient-il strictement `b` (b during a) ?"""
    return relation(a, b) == CONTAINS
