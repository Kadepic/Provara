"""
INGESTION ANATOMIE — organe -> nombre dans le corps humain  -> datasets/lecteur/nombre_organe.jsonl (OFFLINE).

SOURCE : anatomie de référence. Faits STABLES et CERTAINS (organes uniques ou pairs). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ORGANES = [
    ("cœur", "1"), ("cerveau", "1"), ("foie", "1"), ("estomac", "1"), ("rate", "1"),
    ("pancréas", "1"), ("vessie", "1"), ("langue", "1"), ("nez", "1"),
    ("rein", "2"), ("poumon", "2"), ("œil", "2"), ("oreille", "2"),
    ("main", "2"), ("pied", "2"), ("bras", "2"), ("jambe", "2"), ("ovaire", "2"), ("testicule", "2"),
]

def ingere():
    print(f"== NOMBRE D'ORGANES ({len(_ORGANES)}) ==")
    publie("nombre_organe", "convention", "anatomie de référence (organe -> nombre dans le corps)", _ORGANES)

if __name__ == "__main__":
    ingere()
