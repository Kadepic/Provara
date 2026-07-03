"""
INGESTION COULEURS — couleur secondaire -> mélange (synthèse soustractive)  (OFFLINE).

SOURCE : théorie des couleurs (synthèse soustractive classique). Faits STABLES et CERTAINS.

FAUX=0 : mélanges classiques NON CONTESTÉS (peinture / synthèse soustractive). couleur -> UN mélange.
Clés = noms FR minuscules.

Usage : python3 ingere_couleurs_secondaires.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_MELANGES = [
    ("orange", "rouge et jaune"),
    ("vert", "bleu et jaune"),
    ("violet", "rouge et bleu"),
]

SRC = "théorie des couleurs (synthèse soustractive) — mélanges classiques"


def ingere():
    print(f"== COULEURS SECONDAIRES — couleur -> mélange ({len(_MELANGES)}) ==")
    publie("melange_couleur", "convention", SRC, _MELANGES)


if __name__ == "__main__":
    ingere()
