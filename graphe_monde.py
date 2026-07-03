"""
GRAPHE RELATIONNEL TYPÉ (vue navigable du corpus) — promotion de la brique 🟡 (2026-07-02).

Le lecteur stocke des faits plats entité→valeur (rappel). Ce module les rend NAVIGABLES : une valeur
qui est elle-même une entité du corpus (clé d'une relation quelconque) devient une ARÊTE typée
entité —(relation)→ entité, et on peut parcourir en multi-sauts (voisins, chaînes, chemins).
C'est le maillon « traversée multi-sauts » du modèle du monde (cf. ARCHITECTURE_BRIQUES, couche
Représentation) — LAZY sur le lecteur (aucune matérialisation des 71 M de faits, frugalité).

INVARIANT FAUX=0 :
  • une arête n'existe que si le FAIT sous-jacent existe (lookup réel) — jamais d'arête inventée ;
  • un chemin rendu n'enchaîne que des arêtes réelles, re-vérifiables une à une (`verifie_chemin`) ;
  • parcours DÉTERMINISTE (ordre lexicographique) et TERMINANT (ensemble `vus` anti-cycle + bornes) ;
  • entité-cible ambiguë ou hors corpus -> None/[] honnête, jamais un chemin approximatif.
"""
from __future__ import annotations

import lecteur
from base_faits import normalise

_EST_ENTITE_CACHE: dict = {}


def _tables():
    return lecteur.LECTEUR.tables


def est_entite(nom: str) -> bool:
    """`nom` (normalisé) est-il une ENTITÉ du corpus (clé d'au moins une relation) ? Dérivé des données.
    Caché (le BFS re-teste les mêmes candidats) ; court-circuite à la 1re table qui contient."""
    if nom not in _EST_ENTITE_CACHE:
        _EST_ENTITE_CACHE[nom] = any(nom in t for t in _tables().values() if t is not None)
    return _EST_ENTITE_CACHE[nom]


def sortants(x: str, rels=None) -> list:
    """Arêtes SORTANTES de `x` : [(relation, valeur_normalisée, valeur_affichée)] pour chaque relation où
    `x` est clé. `rels` restreint aux relations données. Déterministe (tri lexicographique)."""
    out = []
    for rel in sorted(rels) if rels is not None else sorted(_tables().keys()):
        t = _tables().get(rel)
        if t is None:
            continue
        f = t.get(x)
        if f is not None:
            out.append((rel, normalise(str(f.valeur)), str(f.valeur)))
    return out


def voisins(x: str, rels=None) -> list:
    """Voisins-ENTITÉS de `x` (arêtes sortantes dont la valeur est elle-même une entité du corpus)."""
    return [(rel, v, aff) for rel, v, aff in sortants(x, rels) if est_entite(v)]


def chaine(x: str, rel: str, max_prof: int = 40) -> list:
    """Suit la CHAÎNE d'une relation hiérarchique depuis `x` (x → r(x) → r(r(x)) → …). Termine sur
    valeur-non-clé, profondeur max, ou CYCLE (détecté et coupé — jamais de boucle infinie). Renvoie la
    liste des maillons ATTEINTS (x exclu), tous des faits réels."""
    t = _tables().get(rel)
    if t is None:
        return []
    out, vus, cur = [], {x}, x
    for _ in range(max_prof):
        f = t.get(cur)
        if f is None:
            break
        v = normalise(str(f.valeur))
        if v in vus:                       # cycle réel dans les données -> on coupe (terminaison), sans inventer
            break
        vus.add(v)
        out.append(v)
        cur = v
    return out


def chemin(depart: str, arrivee: str, max_sauts: int = 3, rels=None) -> list | None:
    """Plus court CHEMIN (BFS) d'arêtes réelles entre deux entités : [(relation, noeud), …] menant de
    `depart` à `arrivee`, ou None (HORS honnête). Déterministe (exploration lexicographique), borné
    (`max_sauts`, MAX_VOISINS_PAR_REL par relation), cycle-sûr (ensemble `vus`)."""
    depart, arrivee = normalise(depart), normalise(arrivee)
    if depart == arrivee:
        return []
    frontiere = [(depart, [])]
    vus = {depart}
    for _ in range(max_sauts):
        suivante = []
        for noeud, acc in frontiere:
            for rel, v, _aff in voisins(noeud, rels):   # ≤1 voisin/relation (tables fonctionnelles) -> borné
                if v in vus:
                    continue
                pas = acc + [(rel, v)]
                if v == arrivee:
                    return pas
                vus.add(v)
                suivante.append((v, pas))
        frontiere = suivante
        if not frontiere:
            break
    return None


def verifie_chemin(depart: str, pas: list) -> bool:
    """Re-vérifie qu'un chemin n'enchaîne QUE des faits réels (chaque arête re-lookupée). Sound par
    construction : c'est le juge du graphe — un chemin qui ne re-vérifie pas est REJETÉ."""
    cur = normalise(depart)
    for rel, v in pas:
        t = _tables().get(rel)
        f = t.get(cur) if t is not None else None
        if f is None or normalise(str(f.valeur)) != v:
            return False
        cur = v
    return True
