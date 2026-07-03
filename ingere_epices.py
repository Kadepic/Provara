"""
INGESTION GASTRONOMIE — épice -> pays/région d'origine  -> datasets/lecteur/origine_epice.jsonl (OFFLINE).

SOURCE : histoire des épices de référence. Faits STABLES et CERTAINS pour les origines NON CONTESTÉES.
FAUX=0 : on ÉCARTE les origines disputées (safran, paprika, gingembre=région floue). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_EPICES = [
    ("poivre", "Inde"),
    ("cannelle", "Sri Lanka"),
    ("muscade", "Indonésie"),
    ("clou de girofle", "Indonésie"),
    ("wasabi", "Japon"),
    ("vanille", "Mexique"),
    ("piment", "Mexique"),
    ("cardamome", "Inde"),
]

def ingere():
    print(f"== ÉPICES -> ORIGINE ({len(_EPICES)}) ==")
    publie("origine_epice", "convention", "histoire des épices (épice -> pays d'origine)", _EPICES)

if __name__ == "__main__":
    ingere()
