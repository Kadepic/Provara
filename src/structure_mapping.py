"""
STRUCTURE-MAPPING (analogie inter-domaines) — brique Vague 4. Cœur de l'invention par TRANSFERT.

POURQUOI : « penser comme une machine » inclut voir qu'un mécanisme d'un domaine résout un problème analogue dans un
autre (le flux de chaleur ~ le flux électrique ~ le flux d'eau : mêmes lois de transport). Une analogie n'est PAS une
ressemblance de surface (mêmes mots) mais une correspondance de STRUCTURE : les relations se mettent en bijection.

MODÈLE : deux ensembles de relations (source, cible), chacune = (predicat, arg1, arg2, …). On cherche une application
des OBJETS (source→cible) qui préserve les PRÉDICATS (une relation source a une contrepartie cible de même prédicat et
d'arité, sous le mapping). Score = nb de relations mises en correspondance (systématicité).

FAUX=0 :
  • Une correspondance n'est retenue que si elle PRÉSERVE réellement la structure (prédicat + positions) — jamais un
    appariement forcé pour « faire joli ». Un objet source ne se mappe qu'à UN objet cible (fonction injective vérifiée).
  • Si aucune correspondance ne préserve la structure -> renvoie None (pas d'analogie), pas une analogie inventée.
  • Le score/couverture est factuel (relations réellement alignées), servant de confiance — l'analogie n'affirme rien
    au-delà de ce qui est structurellement aligné.
Stdlib pur, déterministe (recherche ordonnée), souverain.
"""
from __future__ import annotations

from itertools import permutations


def _objets(relations):
    obj = []
    vus = set()
    for r in relations:
        for a in r[1:]:
            if a not in vus:
                vus.add(a)
                obj.append(a)
    return obj


def _relations_sous(mapping, relations):
    """Image des relations source par le mapping objet->objet (prédicat conservé)."""
    out = set()
    for r in relations:
        out.add((r[0],) + tuple(mapping.get(a, a) for a in r[1:]))
    return out


def trouve(source, cible, max_objets: int = 8):
    """Cherche la meilleure correspondance structurelle source->cible. `source`/`cible` = listes de tuples
    (predicat, *args). Renvoie (mapping objet->objet, relations_alignees) de score maximal, ou None si rien n'aligne.
    Déterministe. Borné (au plus `max_objets` de chaque côté) pour rester frugal."""
    src_obj = _objets(source)
    cib_obj = _objets(cible)
    if not src_obj or len(src_obj) > max_objets or len(cib_obj) > max_objets:
        return None
    cible_set = set(cible)
    meilleur = None
    meilleur_score = 0
    # essaie toutes les injections des objets source vers les objets cible (borné) ; déterministe.
    k = min(len(src_obj), len(cib_obj))
    for cibles in permutations(cib_obj, len(src_obj)) if len(cib_obj) >= len(src_obj) else []:
        mapping = dict(zip(src_obj, cibles))
        img = _relations_sous(mapping, source)
        alignees = img & cible_set
        score = len(alignees)
        if score > meilleur_score:
            meilleur_score = score
            # on retrouve les relations SOURCE alignées (pré-image)
            src_alignees = [r for r in source if (r[0],) + tuple(mapping[a] for a in r[1:]) in cible_set]
            meilleur = (mapping, src_alignees)
    return meilleur if meilleur_score > 0 else None


def couverture(source, cible, max_objets: int = 8) -> float:
    """Fraction des relations source structurellement alignables sur la cible (0..1). 0 = pas d'analogie."""
    r = trouve(source, cible, max_objets)
    if r is None or not source:
        return 0.0
    return len(r[1]) / len(source)
