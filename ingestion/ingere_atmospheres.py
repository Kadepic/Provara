"""
INGESTION ASTRONOMIE — corps -> présence d'une atmosphère significative (oui/non)  (OFFLINE).

SOURCE : astronomie de référence. Faits STABLES et CERTAINS. Mercure/Lune = exosphère négligeable -> non.
Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ATMO = [
    ("mercure", "non"), ("vénus", "oui"), ("terre", "oui"), ("mars", "oui"),
    ("jupiter", "oui"), ("saturne", "oui"), ("uranus", "oui"), ("neptune", "oui"),
    ("lune", "non"), ("titan", "oui"),
]

def ingere():
    print(f"== ATMOSPHÈRE DES CORPS ({len(_ATMO)}) ==")
    publie("atmosphere_planete", "physique", "astronomie de référence (corps -> atmosphère significative oui/non)", _ATMO)

if __name__ == "__main__":
    ingere()
