"""THÉORIE DES RÉSEAUX (appliquée) — métriques de graphes, FAUX=0 (mission formule/concept 2026-06-29).

Degré d'un sommet, degré moyen, densité (2|E|/(n(n−1))), centralité de degré normalisée, distribution des degrés,
coefficient de clustering local. Graphe non orienté = n sommets (0..n−1) + liste d'arêtes. Mécanisme EXACT.
Abstention STRUCTURELLE : sommet hors plage, arête mal formée -> ValueError.

Couvre le sujet borné « Théorie des réseaux (appliquée) ».
Vérifié en adverse par `valide_theorie_reseaux.py` (graphe complet densité 1, étoile, triangle…).
"""
from __future__ import annotations

import collections


def _adjacence(n, aretes):
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n (nb sommets) entier ≥ 0 attendu")
    adj = collections.defaultdict(set)
    for e in aretes:
        if len(e) != 2:
            raise ValueError(f"arête mal formée : {e!r}")
        u, v = e
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"sommet hors plage dans {e!r}")
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return adj


def degre(n, aretes, sommet) -> int:
    """Nombre de voisins du `sommet`."""
    adj = _adjacence(n, aretes)
    if not (0 <= sommet < n):
        raise ValueError("sommet hors plage")
    return len(adj[sommet])


def degre_moyen(n, aretes) -> float:
    """Degré moyen = 2|E|/n."""
    adj = _adjacence(n, aretes)
    if n == 0:
        raise ValueError("graphe vide")
    return sum(len(adj[i]) for i in range(n)) / n


def densite(n, aretes) -> float:
    """Densité = 2|E| / (n(n−1)) ∈ [0,1] (1 = graphe complet). n ≥ 2."""
    adj = _adjacence(n, aretes)
    if n < 2:
        raise ValueError("densité définie pour n ≥ 2")
    aretes_uniques = sum(len(adj[i]) for i in range(n)) // 2
    return 2 * aretes_uniques / (n * (n - 1))


def centralite_degre(n, aretes, sommet) -> float:
    """Centralité de degré normalisée = degré(sommet)/(n−1) ∈ [0,1]. n ≥ 2."""
    if n < 2:
        raise ValueError("centralité définie pour n ≥ 2")
    return degre(n, aretes, sommet) / (n - 1)


def distribution_degres(n, aretes) -> dict:
    """Distribution des degrés : {degré: nombre de sommets ayant ce degré}."""
    adj = _adjacence(n, aretes)
    dist = collections.Counter(len(adj[i]) for i in range(n))
    return dict(dist)


def clustering_local(n, aretes, sommet) -> float:
    """Coefficient de clustering local = (arêtes entre voisins) / (paires de voisins). 0 si degré < 2."""
    adj = _adjacence(n, aretes)
    if not (0 <= sommet < n):
        raise ValueError("sommet hors plage")
    voisins = adj[sommet]
    k = len(voisins)
    if k < 2:
        return 0.0
    liens = sum(1 for u in voisins for v in voisins if u < v and v in adj[u])
    return 2 * liens / (k * (k - 1))


if __name__ == "__main__":
    triangle = [(0, 1), (1, 2), (2, 0)]
    etoile = [(0, 1), (0, 2), (0, 3)]
    print("degré centre étoile :", degre(4, etoile, 0), "| feuille :", degre(4, etoile, 1))
    print("densité triangle :", densite(3, triangle), "| densité étoile :", densite(4, etoile))
    print("degré moyen étoile :", degre_moyen(4, etoile))
    print("centralité centre étoile :", centralite_degre(4, etoile, 0))
    print("distribution étoile :", distribution_degres(4, etoile))
    print("clustering triangle (sommet 0) :", clustering_local(3, triangle, 0))
    print("clustering étoile (centre) :", clustering_local(4, etoile, 0))
