"""
INGESTION ASTRONOMIE — planète -> période de révolution + distance au Soleil  (OFFLINE).

SOURCE : valeurs de référence NASA (textbook, arrondies). Faits STABLES et CERTAINS.
FAUX=0 : valeurs arrondies standard non contestées. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

# (planète, période de révolution, distance moyenne au Soleil en millions de km)
_PLANETES = [
    ("mercure", "88 jours", "58"),
    ("vénus", "225 jours", "108"),
    ("terre", "365 jours", "150"),
    ("mars", "687 jours", "228"),
    ("jupiter", "12 ans", "778"),
    ("saturne", "29 ans", "1430"),
    ("uranus", "84 ans", "2870"),
    ("neptune", "165 ans", "4500"),
]

def ingere():
    print(f"== ORBITES — révolution + distance au Soleil ({len(_PLANETES)}) ==")
    publie("periode_revolution_planete", "physique", "NASA (période de révolution, arrondie)",
           [(n, p) for n, p, _ in _PLANETES])
    publie("distance_soleil", "physique", "NASA (distance moyenne au Soleil, millions de km)",
           [(n, d) for n, _, d in _PLANETES])

if __name__ == "__main__":
    ingere()
