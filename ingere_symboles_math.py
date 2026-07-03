"""
INGESTION MATHÉMATIQUES — opération/concept -> symbole  -> datasets/lecteur/symbole_math.jsonl (OFFLINE).

SOURCE : notation mathématique standard. Faits STABLES et CERTAINS.

FAUX=0 : on clé par le NOM (le symbole seul est réduit à "" par la normalisation -> inutilisable comme clé).
nom -> UN symbole = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_symboles_math.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_SYMBOLES = [
    ("addition", "+"), ("soustraction", "−"), ("multiplication", "×"), ("division", "÷"),
    ("égalité", "="), ("différent", "≠"), ("inférieur", "<"), ("supérieur", ">"),
    ("inférieur ou égal", "≤"), ("supérieur ou égal", "≥"), ("racine carrée", "√"),
    ("somme", "∑"), ("produit", "∏"), ("intégrale", "∫"), ("infini", "∞"),
    ("pourcentage", "%"), ("appartient", "∈"), ("inclus", "⊂"), ("pour tout", "∀"),
    ("il existe", "∃"), ("ensemble vide", "∅"), ("plus ou moins", "±"),
    ("perpendiculaire", "⊥"), ("angle", "∠"), ("parallèle", "∥"),
]

SRC = "notation mathématique standard (concept -> symbole)"


def ingere():
    print(f"== SYMBOLES MATH — concept -> symbole ({len(_SYMBOLES)}) ==")
    publie("symbole_math", "convention", SRC, _SYMBOLES)


if __name__ == "__main__":
    ingere()
