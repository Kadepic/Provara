"""
INGESTION MÉTÉO — degré Beaufort -> appellation du vent  -> datasets/lecteur/beaufort_description.jsonl (OFFLINE).

SOURCE : échelle de Beaufort officielle (0 à 12). Faits STABLES et CERTAINS. Fonctionnel.
articles=False (les degrés sont des chiffres).
"""
from __future__ import annotations
from ingere_wikidata import publie

_BEAUFORT = [
    ("0", "calme"), ("1", "très légère brise"), ("2", "légère brise"), ("3", "petite brise"),
    ("4", "jolie brise"), ("5", "bonne brise"), ("6", "vent frais"), ("7", "grand frais"),
    ("8", "coup de vent"), ("9", "fort coup de vent"), ("10", "tempête"),
    ("11", "violente tempête"), ("12", "ouragan"),
]

def ingere():
    print(f"== ÉCHELLE DE BEAUFORT ({len(_BEAUFORT)}) ==")
    publie("beaufort_description", "convention", "échelle de Beaufort officielle (degré -> appellation)", _BEAUFORT, articles=False)

if __name__ == "__main__":
    ingere()
