"""
INGESTION PHYSIOLOGIE — organe/glande -> hormone principale produite  -> datasets/lecteur/hormone_organe.jsonl (OFFLINE).

SOURCE : endocrinologie de référence. Faits STABLES et CERTAINS (hormone principale). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_HORMONES = [
    ("pancréas", "l'insuline"),
    ("thyroïde", "la thyroxine"),
    ("glande surrénale", "l'adrénaline"),
    ("ovaire", "les œstrogènes"),
    ("testicule", "la testostérone"),
    ("hypophyse", "l'hormone de croissance"),
]

def ingere():
    print(f"== HORMONES PAR GLANDE ({len(_HORMONES)}) ==")
    publie("hormone_organe", "convention", "endocrinologie de référence (glande -> hormone principale)", _HORMONES)

if __name__ == "__main__":
    ingere()
