"""
INGESTION CORPS HUMAIN — os -> région du corps  -> datasets/lecteur/region_os.jsonl (OFFLINE).

SOURCE : anatomie de référence. Faits STABLES et CERTAINS. os -> UNE région = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_OS = [
    ("fémur", "la cuisse"), ("tibia", "la jambe"), ("péroné", "la jambe"),
    ("rotule", "le genou"), ("crâne", "la tête"), ("mandibule", "la mâchoire"),
    ("humérus", "le bras"), ("radius", "l'avant-bras"), ("cubitus", "l'avant-bras"),
    ("clavicule", "l'épaule"), ("omoplate", "l'épaule"), ("sternum", "le thorax"),
    ("côte", "le thorax"), ("vertèbre", "la colonne vertébrale"), ("bassin", "le bassin"),
    ("phalange", "les doigts"), ("métacarpe", "la main"), ("métatarse", "le pied"),
    ("calcanéum", "le talon"),
]

def ingere():
    print(f"== OS -> RÉGION ({len(_OS)}) ==")
    publie("region_os", "convention", "anatomie de référence (os -> région du corps)", _OS)

if __name__ == "__main__":
    ingere()
