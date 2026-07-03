"""
INGESTION MÉTROLOGIE — unité impériale/anglo-saxonne -> équivalent métrique  -> datasets/lecteur/equivalent_metrique.jsonl (OFFLINE).

SOURCE : conversions officielles. Faits STABLES et CERTAINS. FAUX=0 : on précise les unités ambiguës
(gallon/pinte = américains, qui diffèrent des britanniques). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_UNITES = [
    ("mile", "1,609 km"),
    ("mile nautique", "1,852 km"),
    ("pouce", "2,54 cm"),
    ("pied", "30,48 cm"),
    ("yard", "0,914 m"),
    ("livre", "453,6 g"),
    ("once", "28,35 g"),
    ("gallon américain", "3,785 L"),
    ("pinte américaine", "0,473 L"),
    ("nœud", "1,852 km/h"),
    ("acre", "4047 m²"),
]

def ingere():
    print(f"== UNITÉS IMPÉRIALES -> MÉTRIQUE ({len(_UNITES)}) ==")
    publie("equivalent_metrique", "convention", "conversions officielles (unité impériale -> métrique)", _UNITES)

if __name__ == "__main__":
    ingere()
