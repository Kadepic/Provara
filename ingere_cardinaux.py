"""
INGESTION GÉO — point cardinal -> point cardinal opposé  -> datasets/lecteur/oppose_cardinal.jsonl (OFFLINE).

SOURCE : géographie élémentaire. Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_OPPOSES = [
    ("nord", "sud"), ("sud", "nord"), ("est", "ouest"), ("ouest", "est"),
    ("nord-est", "sud-ouest"), ("sud-ouest", "nord-est"),
    ("nord-ouest", "sud-est"), ("sud-est", "nord-ouest"),
]

def ingere():
    print(f"== POINTS CARDINAUX OPPOSÉS ({len(_OPPOSES)}) ==")
    publie("oppose_cardinal", "convention", "géographie élémentaire (cardinal -> opposé)", _OPPOSES, articles=False)

if __name__ == "__main__":
    ingere()
