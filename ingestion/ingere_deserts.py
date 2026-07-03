"""
INGESTION GÉO — désert -> continent  -> datasets/lecteur/continent_desert.jsonl (OFFLINE).

SOURCE : géographie de référence. Faits STABLES et CERTAINS. désert -> UN continent = fonctionnel.
Valeurs alignées sur la relation `continent`.
"""
from __future__ import annotations
from ingere_wikidata import publie

_DESERTS = [
    ("sahara", "Afrique"), ("kalahari", "Afrique"), ("namib", "Afrique"),
    ("gobi", "Asie"), ("désert d'arabie", "Asie"), ("thar", "Asie"), ("taklamakan", "Asie"),
    ("atacama", "Amérique du Sud"), ("patagonie", "Amérique du Sud"),
    ("mojave", "Amérique du Nord"), ("sonora", "Amérique du Nord"), ("chihuahua", "Amérique du Nord"),
    ("grand désert de victoria", "Océanie"),
]

def ingere():
    print(f"== DÉSERTS -> CONTINENT ({len(_DESERTS)}) ==")
    publie("continent_desert", "physique", "géographie de référence (désert -> continent)", _DESERTS)

if __name__ == "__main__":
    ingere()
