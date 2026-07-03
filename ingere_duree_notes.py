"""
INGESTION MUSIQUE — figure de note -> durée (en temps, mesure 4/4)  -> datasets/lecteur/duree_note.jsonl (OFFLINE).

SOURCE : solfège de référence. Faits STABLES et CERTAINS (valeurs relatives fixes). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_NOTES = [
    ("ronde", "4 temps"),
    ("blanche", "2 temps"),
    ("noire", "1 temps"),
    ("croche", "un demi-temps"),
    ("double croche", "un quart de temps"),
]

def ingere():
    print(f"== DURÉE DES NOTES ({len(_NOTES)}) ==")
    publie("duree_note", "convention", "solfège de référence (figure -> durée en 4/4)", _NOTES)

if __name__ == "__main__":
    ingere()
