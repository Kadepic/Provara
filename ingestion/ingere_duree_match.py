"""
INGESTION SPORT — sport -> durée réglementaire d'un match  -> datasets/lecteur/duree_match.jsonl (OFFLINE).

SOURCE : règlements sportifs. Faits STABLES et CERTAINS. FAUX=0 : on écarte les sports à durée variable
(tennis) ou ambiguë selon la ligue (basket NBA 48 vs FIBA 40). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_DUREE = [
    ("football", "90 minutes"),
    ("football américain", "60 minutes"),
    ("rugby à xv", "80 minutes"),
    ("handball", "60 minutes"),
    ("hockey sur glace", "60 minutes"),
    ("water-polo", "32 minutes"),
]

def ingere():
    print(f"== DURÉE DES MATCHS ({len(_DUREE)}) ==")
    publie("duree_match", "convention", "règlements sportifs (sport -> durée réglementaire)", _DUREE)

if __name__ == "__main__":
    ingere()
