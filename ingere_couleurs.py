"""
INGESTION COULEURS — couleur -> code hexadécimal (sRGB) -> datasets/lecteur/code_hex_couleur.jsonl (OFFLINE).

SOURCE : modèle sRGB / couleurs nommées standard. Faits STABLES et CERTAINS pour les couleurs aux valeurs
canoniques (coins du cube RGB + quelques couleurs nommées standard non ambiguës).

FAUX=0 — discipline : UNIQUEMENT les couleurs à hex canonique NON CONTESTÉ. On ÉCARTE les teintes
ambiguës (« vert » : on prend le VERT PRIMAIRE additif #00FF00, valeur sRGB du canal vert plein).
couleur -> UN code = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_couleurs.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_COULEURS = [
    ("noir", "#000000"),
    ("blanc", "#FFFFFF"),
    ("rouge", "#FF0000"),
    ("vert", "#00FF00"),
    ("bleu", "#0000FF"),
    ("jaune", "#FFFF00"),
    ("cyan", "#00FFFF"),
    ("magenta", "#FF00FF"),
    ("gris", "#808080"),
    ("orange", "#FFA500"),
]

SRC = "modèle sRGB / couleurs nommées standard — valeurs canoniques"


def ingere():
    print(f"== COULEURS — couleur -> hex sRGB ({len(_COULEURS)}) ==")
    publie("code_hex_couleur", "convention", SRC, _COULEURS)


if __name__ == "__main__":
    ingere()
