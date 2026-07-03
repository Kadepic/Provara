"""
INGESTION ASTRONOMIE — planète -> symbole astronomique  (OFFLINE).

SOURCE : symboles astronomiques traditionnels (UAI). Faits STABLES et CERTAINS.
FAUX=0 : on clé par le NOM de la planète (le symbole seul -> "" par normalise). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_SYMBOLES = [
    ("mercure", "☿"), ("vénus", "♀"), ("terre", "♁"), ("mars", "♂"),
    ("jupiter", "♃"), ("saturne", "♄"), ("uranus", "♅"), ("neptune", "♆"),
    ("soleil", "☉"), ("lune", "☽"),
]

def ingere():
    print(f"== SYMBOLES ASTRONOMIQUES ({len(_SYMBOLES)}) ==")
    publie("symbole_astro_planete", "convention", "symboles astronomiques traditionnels (astre -> symbole)", _SYMBOLES)

if __name__ == "__main__":
    ingere()
