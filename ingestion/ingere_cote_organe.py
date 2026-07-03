"""
INGESTION ANATOMIE — organe -> côté du corps  -> datasets/lecteur/cote_organe.jsonl (OFFLINE).

SOURCE : anatomie de référence. Faits STABLES et CERTAINS pour les organes nettement latéralisés. Fonctionnel.
FAUX=0 : on garde les organes au côté NON CONTESTÉ (foie/rate/appendice/cœur). Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_COTE = [
    ("foie", "à droite"),
    ("rate", "à gauche"),
    ("appendice", "à droite"),
    ("cœur", "à gauche"),
    ("vésicule biliaire", "à droite"),
]

def ingere():
    print(f"== CÔTÉ DES ORGANES ({len(_COTE)}) ==")
    publie("cote_organe", "convention", "anatomie de référence (organe -> côté du corps)", _COTE)

if __name__ == "__main__":
    ingere()
