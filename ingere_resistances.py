"""
INGESTION ÉLECTRONIQUE — couleur d'anneau de résistance -> chiffre (0-9)  -> datasets/lecteur/valeur_couleur_resistance.jsonl (OFFLINE).

SOURCE : code des couleurs CEI 60062 (résistances). Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_COULEURS = [
    ("noir", "0"), ("marron", "1"), ("rouge", "2"), ("orange", "3"), ("jaune", "4"),
    ("vert", "5"), ("bleu", "6"), ("violet", "7"), ("gris", "8"), ("blanc", "9"),
]

def ingere():
    print(f"== CODE COULEUR RÉSISTANCES ({len(_COULEURS)}) ==")
    publie("valeur_couleur_resistance", "convention", "code des couleurs CEI 60062 (couleur -> chiffre)", _COULEURS)

if __name__ == "__main__":
    ingere()
