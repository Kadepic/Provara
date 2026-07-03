"""
INGESTION BOTANIQUE — fruit -> arbre qui le produit  -> datasets/lecteur/arbre_fruit.jsonl (OFFLINE).

SOURCE : botanique de référence. Faits STABLES et CERTAINS.

FAUX=0 : correspondances NON CONTESTÉES. fruit -> UN arbre = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_fruits_arbres.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_FRUITS = [
    ("pomme", "pommier"), ("poire", "poirier"), ("cerise", "cerisier"), ("prune", "prunier"),
    ("pêche", "pêcher"), ("abricot", "abricotier"), ("orange", "oranger"), ("citron", "citronnier"),
    ("olive", "olivier"), ("noix", "noyer"), ("châtaigne", "châtaignier"), ("amande", "amandier"),
    ("figue", "figuier"), ("raisin", "vigne"), ("banane", "bananier"), ("datte", "dattier"),
    ("noisette", "noisetier"), ("mandarine", "mandarinier"), ("pamplemousse", "pamplemoussier"),
    ("kaki", "plaqueminier"), ("coing", "cognassier"), ("nèfle", "néflier"),
]

SRC = "botanique de référence (fruit -> arbre)"


def ingere():
    print(f"== FRUITS -> ARBRES ({len(_FRUITS)}) ==")
    publie("arbre_fruit", "convention", SRC, _FRUITS)


if __name__ == "__main__":
    ingere()
