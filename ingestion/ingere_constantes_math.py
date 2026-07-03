"""
INGESTION MATHÉMATIQUES — constante -> valeur numérique  -> datasets/lecteur/valeur_constante.jsonl (OFFLINE).

SOURCE : mathématiques (valeurs exactes tronquées). Faits STABLES et CERTAINS (constantes universelles).

FAUX=0 — discipline : valeurs tronquées à 8 décimales, VÉRIFIABLES indépendamment. constante -> UNE valeur.
Clés = noms FR minuscules ; le lecteur normalise.

Usage : python3 ingere_constantes_math.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_CONSTANTES = [
    ("pi", "3.14159265"),
    ("nombre pi", "3.14159265"),
    ("e", "2.71828183"),
    ("nombre d'euler", "2.71828183"),
    ("nombre d'or", "1.61803399"),
    ("racine carrée de deux", "1.41421356"),
    ("racine carrée de trois", "1.73205081"),
    ("racine carrée de cinq", "2.23606798"),
    ("constante d'euler-mascheroni", "0.57721566"),
    ("logarithme népérien de deux", "0.69314718"),
]

SRC = "mathématiques de référence (constante -> valeur, 8 décimales) — universel"


def ingere():
    print(f"== CONSTANTES MATH — constante -> valeur ({len(_CONSTANTES)}) ==")
    publie("valeur_constante", "physique", SRC, _CONSTANTES)


if __name__ == "__main__":
    ingere()
