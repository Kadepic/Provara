"""
INGESTION CULTURE — danse -> pays d'origine  -> datasets/lecteur/pays_danse.jsonl (OFFLINE).

SOURCE : culture de référence. Faits STABLES et CERTAINS (origine non contestée).

FAUX=0 : danses à origine NON CONTESTÉE. danse -> UN pays = fonctionnel. Clés FR minuscules.

Usage : python3 ingere_danses.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_DANSES = [
    ("tango", "Argentine"),
    ("flamenco", "Espagne"),
    ("samba", "Brésil"),
    ("capoeira", "Brésil"),
    ("valse", "Autriche"),
    ("polka", "République tchèque"),
    ("sirtaki", "Grèce"),
    ("haka", "Nouvelle-Zélande"),
    ("french cancan", "France"),
    ("rumba", "Cuba"),
    ("fandango", "Espagne"),
    ("czardas", "Hongrie"),
]

SRC = "culture de référence (danse -> pays d'origine)"


def ingere():
    print(f"== DANSES -> PAYS ({len(_DANSES)}) ==")
    publie("pays_danse", "convention", SRC, _DANSES)


if __name__ == "__main__":
    ingere()
