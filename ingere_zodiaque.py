"""
INGESTION ZODIAQUE — signe astrologique -> élément  -> datasets/lecteur/element_zodiaque.jsonl (OFFLINE).

SOURCE : convention astrologique occidentale (fixe). Faits STABLES et CERTAINS AU SEIN de cette convention
(comme les chiffres romains : une correspondance conventionnelle fixée). 12 signes, 4 éléments.

FAUX=0 — discipline : correspondance signe->élément FIXÉE par la convention (non disputée). signe -> UN
élément = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_zodiaque.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_SIGNES = [
    ("bélier", "feu"), ("lion", "feu"), ("sagittaire", "feu"),
    ("taureau", "terre"), ("vierge", "terre"), ("capricorne", "terre"),
    ("gémeaux", "air"), ("balance", "air"), ("verseau", "air"),
    ("cancer", "eau"), ("scorpion", "eau"), ("poissons", "eau"),
]

SRC = "convention astrologique occidentale (signe -> élément) — correspondance fixe"


def ingere():
    print(f"== ZODIAQUE — signe -> élément ({len(_SIGNES)}) ==")
    publie("element_zodiaque", "convention", SRC, _SIGNES)


if __name__ == "__main__":
    ingere()
