"""
INGESTION GÉO — océan -> rang par superficie  -> datasets/lecteur/rang_ocean.jsonl (OFFLINE).

SOURCE : géographie de référence. Faits STABLES et CERTAINS (5 océans, ordre de taille). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_OCEANS = [
    ("océan pacifique", "1"),
    ("océan atlantique", "2"),
    ("océan indien", "3"),
    ("océan austral", "4"),
    ("océan arctique", "5"),
]

def ingere():
    print(f"== OCÉANS — rang par superficie ({len(_OCEANS)}) ==")
    publie("rang_ocean", "physique", "géographie de référence (océan -> rang par superficie)", _OCEANS)

if __name__ == "__main__":
    ingere()
