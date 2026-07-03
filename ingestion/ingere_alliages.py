"""
INGESTION MATÉRIAUX — alliage -> composition  -> datasets/lecteur/composition_alliage.jsonl (OFFLINE).

SOURCE : métallurgie de référence. Faits STABLES et CERTAINS (composition principale non contestée).

FAUX=0 — discipline : compositions principales NON CONTESTÉES. alliage -> UNE composition = fonctionnel.
Clés = noms FR minuscules.

Usage : python3 ingere_alliages.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_ALLIAGES = [
    ("bronze", "cuivre et étain"),
    ("laiton", "cuivre et zinc"),
    ("acier", "fer et carbone"),
    ("fonte", "fer et carbone"),
    ("électrum", "or et argent"),
    ("duralumin", "aluminium et cuivre"),
    ("maillechort", "cuivre, nickel et zinc"),
    ("inox", "fer, chrome et nickel"),
    ("soudure", "étain et plomb"),
]

SRC = "métallurgie de référence (alliage -> composition principale)"


def ingere():
    print(f"== ALLIAGES — alliage -> composition ({len(_ALLIAGES)}) ==")
    publie("composition_alliage", "physique", SRC, _ALLIAGES)


if __name__ == "__main__":
    ingere()
