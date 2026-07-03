"""
INGESTION CORPS HUMAIN — type de dent -> fonction  -> datasets/lecteur/fonction_dent.jsonl (OFFLINE).

SOURCE : anatomie dentaire de référence. Faits STABLES et CERTAINS. type -> UNE fonction = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_DENTS = [
    ("incisive", "couper les aliments"),
    ("canine", "déchirer les aliments"),
    ("prémolaire", "écraser les aliments"),
    ("molaire", "broyer les aliments"),
]

def ingere():
    print(f"== FONCTION DES DENTS ({len(_DENTS)}) ==")
    publie("fonction_dent", "convention", "anatomie dentaire (type de dent -> fonction)", _DENTS)

if __name__ == "__main__":
    ingere()
