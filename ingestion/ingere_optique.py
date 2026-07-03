"""
INGESTION OPTIQUE — instrument d'optique -> usage  -> datasets/lecteur/usage_instrument_optique.jsonl (OFFLINE).

SOURCE : physique/optique de référence. Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_INSTRUMENTS = [
    ("microscope", "observer l'infiniment petit"),
    ("télescope", "observer les astres lointains"),
    ("lunette astronomique", "observer les astres"),
    ("jumelles", "observer de loin avec les deux yeux"),
    ("longue-vue", "observer au loin"),
    ("loupe", "agrandir les objets proches"),
    ("périscope", "voir par-dessus un obstacle"),
    ("lunettes de vue", "corriger la vision"),
]

def ingere():
    print(f"== USAGE INSTRUMENTS OPTIQUES ({len(_INSTRUMENTS)}) ==")
    publie("usage_instrument_optique", "convention", "optique de référence (instrument -> usage)", _INSTRUMENTS)

if __name__ == "__main__":
    ingere()
