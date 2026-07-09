# -*- coding: utf-8 -*-
"""GRAPHE DES ROUES — la graine du GAP-ENGINE v2 (étape ③ du plan validé Yohan 2026-07-10).

L'invention, dans ce cadre : chercher des CHEMINS de grandeurs faisables dans le graphe des mécanismes
vérifiés — et quand il n'y en a PAS, NOMMER le pont manquant (« il manquerait une relation reliant X et Y ») :
l'aveu du gap est la graine d'invention (on sait exactement QUELLE relation chercher/bâtir).

Machine-natif : nœuds = grandeurs canoniques des roues ; arêtes = les roues elles-mêmes (une roue relie
toutes ses grandeurs entre elles — 2 connues ferment le reste). BFS pur stdlib. FAUX=0 : le graphe REFLÈTE
les roues réellement câblées (source unique : pont_grandeurs._ROUES), jamais une relation supposée.
"""
from __future__ import annotations

import collections

import pont_grandeurs as _P


def roues() -> tuple:
    """Les roues câblées (source unique de vérité : le pont)."""
    return _P._ROUES


def grandeurs(les_roues=None) -> dict:
    """{grandeur: [noms de roues qui la portent]} — l'index du graphe."""
    idx: dict = {}
    for r in (les_roues if les_roues is not None else roues()):
        for d in r["dims"]:
            idx.setdefault(d, []).append(r["nom"])
    return idx


def chemins(source: str, cible: str, les_roues=None, max_pas: int = 6):
    """Le plus court CHEMIN de `source` vers `cible` à travers les roues (BFS sur les roues, une roue relie
    toutes ses grandeurs). -> liste de roues traversées [(nom, devise, grandeur_d_entree), …], ou None si
    aucun pont n'existe (= un GAP nommable), ou "?" si une grandeur est inconnue du graphe."""
    rs = list(les_roues if les_roues is not None else roues())
    idx = grandeurs(rs)
    if source not in idx or cible not in idx:
        return "?"
    # BFS : état = grandeur atteinte ; transition = toute roue portant cette grandeur ouvre ses autres dims.
    vus = {source}
    file_ = collections.deque([(source, [])])
    while file_:
        g, chemin = file_.popleft()
        if len(chemin) >= max_pas:
            continue
        for r in rs:
            if g not in r["dims"]:
                continue
            etape = chemin + [(r["nom"], r["devise"], g)]
            if cible in r["dims"]:
                return etape
            for d in r["dims"]:
                if d not in vus:
                    vus.add(d)
                    file_.append((d, etape))
    return None


def composantes(les_roues=None) -> list:
    """Les ÎLOTS du graphe (composantes connexes de grandeurs). Un seul îlot = tout se relie ; plusieurs =
    les ponts MANQUANTS entre îlots sont les gaps structurels (à nommer, jamais à inventer en silence)."""
    rs = list(les_roues if les_roues is not None else roues())
    idx = grandeurs(rs)
    restants = set(idx)
    out = []
    while restants:
        depart = min(restants)                            # déterministe
        ilot = {depart}
        file_ = collections.deque([depart])
        while file_:
            g = file_.popleft()
            for r in rs:
                if g in r["dims"]:
                    for d in r["dims"]:
                        if d in restants and d not in ilot:
                            ilot.add(d)
                            file_.append(d)
        out.append(tuple(sorted(ilot)))
        restants -= ilot
    return sorted(out, key=len, reverse=True)


def gaps(les_roues=None) -> list:
    """Les PONTS MANQUANTS entre îlots : [(grandeur d'un îlot, grandeur d'un autre), …] — un par paire
    d'îlots (représentants), vide si le graphe est connexe. C'est la sortie « invention » : chaque paire
    NOMME une relation qui n'existe pas encore dans les roues."""
    comps = composantes(les_roues)
    return [(comps[i][0], comps[j][0]) for i in range(len(comps)) for j in range(i + 1, len(comps))]
