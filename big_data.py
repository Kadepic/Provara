"""BIG DATA — primitives de traitement à l'échelle, FAUX=0 (mission formule/concept 2026-06-29).

Modèle MapReduce (map -> regroupement par clé -> reduce), échantillonnage par réservoir (taille fixe, déterministe
ici via un flux d'indices), filtre de Bloom (test d'appartenance probabiliste : faux négatif IMPOSSIBLE, faux positif
possible — propriété GARANTIE). Mécanisme déterministe et vérifiable. Abstention STRUCTURELLE : paramètres invalides
-> ValueError.

Couvre le sujet borné « Big data ».
Vérifié en adverse par `valide_big_data.py` (word-count MapReduce, Bloom sans faux négatif).
"""
from __future__ import annotations

import collections
import hashlib


def mapreduce(donnees, fonction_map, fonction_reduce) -> dict:
    """Exécute un MapReduce : `fonction_map(item)` -> liste de (clé, valeur) ; regroupement par clé ;
    `fonction_reduce(clé, [valeurs])` -> valeur agrégée. Renvoie {clé: valeur réduite}. Déterministe."""
    if not callable(fonction_map) or not callable(fonction_reduce):
        raise ValueError("fonction_map et fonction_reduce doivent être appelables")
    groupes = collections.defaultdict(list)
    for item in donnees:
        for cle, valeur in fonction_map(item):
            groupes[cle].append(valeur)
    return {cle: fonction_reduce(cle, valeurs) for cle, valeurs in groupes.items()}


def compte_mots(documents) -> dict:
    """Word-count classique via MapReduce : compte les occurrences de chaque mot sur un corpus de documents."""
    return mapreduce(
        documents,
        lambda doc: [(mot.lower(), 1) for mot in doc.split()],
        lambda cle, valeurs: sum(valeurs),
    )


class FiltreBloom:
    """Filtre de Bloom : test d'appartenance compact. Faux négatif IMPOSSIBLE (si ajouté -> toujours détecté),
    faux positif possible. `taille` bits, `k` fonctions de hachage."""

    def __init__(self, taille: int, k: int = 3):
        if not isinstance(taille, int) or isinstance(taille, bool) or taille <= 0:
            raise ValueError("taille > 0 requise")
        if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            raise ValueError("k > 0 requis")
        self.taille = taille
        self.k = k
        self.bits = 0

    def _positions(self, element):
        for i in range(self.k):
            h = int(hashlib.sha256(f"{i}:{element}".encode("utf-8")).hexdigest(), 16)
            yield h % self.taille

    def ajoute(self, element):
        for p in self._positions(element):
            self.bits |= (1 << p)

    def contient(self, element) -> bool:
        """True si `element` PEUT être présent (ou faux positif) ; False = CERTAINEMENT absent (pas de faux négatif)."""
        return all((self.bits >> p) & 1 for p in self._positions(element))


def echantillon_reservoir(flux, taille: int, indices_choisis):
    """Échantillonnage par réservoir DÉTERMINISTE (pour vérifiabilité) : garde les éléments dont l'indice ∈
    `indices_choisis` (ensemble), simulant un tirage. Renvoie au plus `taille` éléments. (Le tirage aléatoire réel
    se ferait avec un RNG ; ici on rend le mécanisme testable.)"""
    if not isinstance(taille, int) or isinstance(taille, bool) or taille <= 0:
        raise ValueError("taille > 0 requise")
    choisis = set(indices_choisis)
    out = []
    for i, x in enumerate(flux):
        if i in choisis and len(out) < taille:
            out.append(x)
    return out


if __name__ == "__main__":
    docs = ["le chat dort", "le chien court", "le chat court"]
    print("word-count :", compte_mots(docs))
    b = FiltreBloom(1024, 4)
    for m in ["pomme", "banane", "cerise"]:
        b.ajoute(m)
    print("Bloom 'pomme' (ajouté) :", b.contient("pomme"), "| 'kiwi' (absent) :", b.contient("kiwi"))
    print("réservoir indices {0,2} :", echantillon_reservoir(["a", "b", "c", "d"], 2, {0, 2}))
