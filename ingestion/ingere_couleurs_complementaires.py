"""
INGESTION COULEURS — couleur -> couleur complémentaire  -> datasets/lecteur/couleur_complementaire.jsonl (OFFLINE).

SOURCE : théorie des couleurs (cercle chromatique RYB classique). Faits STABLES et CERTAINS.
FAUX=0 : paires complémentaires classiques NON CONTESTÉES. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAIRES = [
    ("rouge", "vert"),
    ("vert", "rouge"),
    ("bleu", "orange"),
    ("orange", "bleu"),
    ("jaune", "violet"),
    ("violet", "jaune"),
]

def ingere():
    print(f"== COULEURS COMPLÉMENTAIRES ({len(_PAIRES)}) ==")
    publie("couleur_complementaire", "convention", "théorie des couleurs (cercle RYB) — paires complémentaires", _PAIRES)

if __name__ == "__main__":
    ingere()
