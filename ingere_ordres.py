"""
INGESTION ORDRES CONVENTIONNELS — signe chinois / ceinture judo / arc-en-ciel -> rang  (OFFLINE).

SOURCE : conventions de référence (ordres fixes). Faits STABLES et CERTAINS. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_SIGNES = [
    ("rat", "1"), ("buffle", "2"), ("tigre", "3"), ("lapin", "4"), ("dragon", "5"),
    ("serpent", "6"), ("cheval", "7"), ("chèvre", "8"), ("singe", "9"), ("coq", "10"),
    ("chien", "11"), ("cochon", "12"),
]
_CEINTURES = [
    ("blanche", "1"), ("jaune", "2"), ("orange", "3"), ("verte", "4"),
    ("bleue", "5"), ("marron", "6"), ("noire", "7"),
]
_ARC = [
    ("rouge", "1"), ("orange", "2"), ("jaune", "3"), ("vert", "4"),
    ("bleu", "5"), ("indigo", "6"), ("violet", "7"),
]

def ingere():
    print("== ORDRES — signes chinois + ceintures judo + arc-en-ciel ==")
    publie("ordre_signe_chinois", "convention", "astrologie chinoise (signe -> rang 1..12)", _SIGNES)
    publie("ordre_ceinture_judo", "convention", "judo (ceinture -> rang de progression)", _CEINTURES)
    publie("ordre_arc_en_ciel", "convention", "arc-en-ciel (couleur -> rang, ROY-G-BIV)", _ARC)

if __name__ == "__main__":
    ingere()
