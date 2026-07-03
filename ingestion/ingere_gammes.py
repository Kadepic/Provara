"""
INGESTION MUSIQUE — gamme -> nombre de notes  -> datasets/lecteur/nombre_notes_gamme.jsonl (OFFLINE).

SOURCE : théorie musicale de référence. Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_GAMMES = [
    ("gamme majeure", "7"), ("gamme mineure", "7"), ("gamme pentatonique", "5"),
    ("gamme chromatique", "12"), ("gamme par tons", "6"), ("gamme diatonique", "7"),
]

def ingere():
    print(f"== GAMMES -> NB NOTES ({len(_GAMMES)}) ==")
    publie("nombre_notes_gamme", "convention", "théorie musicale (gamme -> nombre de notes)", _GAMMES)

if __name__ == "__main__":
    ingere()
