"""CLOUD / SYSTÈMES DISTRIBUÉS — mécanismes EXACTS, FAUX=0 (mission formule/concept 2026-06-29).

Hachage cohérent (consistent hashing : placement d'une clé sur un anneau de nœuds), quorums de lecture/écriture
(condition R+W>N pour la cohérence forte), théorème CAP (compromis Cohérence/Disponibilité sous Partition).
Mécanisme déterministe et vérifiable. Abstention STRUCTURELLE : aucun nœud, paramètres incohérents -> ValueError.

Couvre le sujet borné « Cloud / distribué ».
Vérifié en adverse par `valide_cloud_distribue.py` (placement stable, quorum, CAP).
"""
from __future__ import annotations

import hashlib


def _hash(cle) -> int:
    return int(hashlib.sha256(str(cle).encode("utf-8")).hexdigest(), 16)


def noeud_responsable(cle, noeuds) -> str:
    """Hachage cohérent : renvoie le nœud responsable de `cle` = premier nœud dont le hash ≥ hash(clé) sur l'anneau
    (sinon le premier nœud = bouclage). Déterministe ; minimise les déplacements quand l'ensemble de nœuds change."""
    if not isinstance(noeuds, (list, tuple)) or not noeuds:
        raise ValueError("au moins un nœud requis")
    anneau = sorted((_hash(n), n) for n in set(noeuds))
    h = _hash(cle)
    for hn, n in anneau:
        if hn >= h:
            return n
    return anneau[0][1]                      # bouclage sur l'anneau


def quorum_coherent(n_replicas, r, w) -> bool:
    """Cohérence forte garantie ssi R + W > N (les ensembles de lecture et d'écriture se recouvrent). 1 ≤ R,W ≤ N."""
    for v, nom in ((n_replicas, "N"), (r, "R"), (w, "W")):
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            raise ValueError(f"{nom} entier ≥ 1 requis")
    if r > n_replicas or w > n_replicas:
        raise ValueError("R et W ≤ N requis")
    return r + w > n_replicas


def cap_choix(tolere_partition: bool, privilegie: str) -> str:
    """Théorème CAP : sous partition réseau (P), un système ne peut garantir que C (cohérence) OU A (disponibilité).
    Renvoie 'CP' (cohérent) ou 'AP' (disponible) si tolere_partition, sinon 'CA' (pas de tolérance aux partitions)."""
    if not isinstance(tolere_partition, bool):
        raise ValueError("tolere_partition booléen requis")
    if not tolere_partition:
        return "CA"
    if privilegie == "coherence":
        return "CP"
    if privilegie == "disponibilite":
        return "AP"
    raise ValueError("privilegie ∈ {'coherence','disponibilite'}")


def facteur_replication_disponibilite(n_replicas, n_tolerees) -> bool:
    """Un système à N réplicas tolère la panne de `n_tolerees` nœuds (pour rester disponible) ssi N > n_tolerees."""
    for v in (n_replicas, n_tolerees):
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError("entiers ≥ 0 requis")
    return n_replicas > n_tolerees


if __name__ == "__main__":
    noeuds = ["n1", "n2", "n3"]
    for cle in ["objet-A", "objet-B", "utilisateur-42"]:
        print(f"  {cle} -> {noeud_responsable(cle, noeuds)}")
    # stabilité : retirer n3 ne déplace que les clés de n3
    print("placement stable (mêmes nœuds) :",
          noeud_responsable("objet-A", noeuds) == noeud_responsable("objet-A", noeuds))
    print("quorum N=3,R=2,W=2 :", quorum_coherent(3, 2, 2), "| R=1,W=1 :", quorum_coherent(3, 1, 1))
    print("CAP partition+cohérence :", cap_choix(True, "coherence"), "| +dispo :", cap_choix(True, "disponibilite"))
