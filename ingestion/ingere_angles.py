"""
INGESTION GÉOMÉTRIE — type d'angle -> mesure  -> datasets/lecteur/mesure_angle.jsonl (OFFLINE).

SOURCE : géométrie élémentaire. Faits STABLES et CERTAINS (valeurs exactes). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ANGLES = [
    ("angle nul", "0°"),
    ("angle droit", "90°"),
    ("angle plat", "180°"),
    ("angle plein", "360°"),
]

def ingere():
    print(f"== MESURE DES ANGLES ({len(_ANGLES)}) ==")
    publie("mesure_angle", "convention", "géométrie élémentaire (type d'angle -> mesure)", _ANGLES)

if __name__ == "__main__":
    ingere()
