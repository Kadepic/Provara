"""
INGESTION GÉO — grande ville (NON capitale) -> pays  -> datasets/lecteur/pays_ville.jsonl (OFFLINE).

SOURCE : géographie de référence. Faits STABLES et CERTAINS. Complète `pays_de_capitale` avec des villes
majeures non capitales. ville -> UN pays = fonctionnel. Clés = noms FR minuscules.

FAUX=0 — discipline : villes à pays NON CONTESTÉ. On évite les homonymes ambigus.

Usage : python3 ingere_villes.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_VILLES = [
    ("new york", "États-Unis"), ("los angeles", "États-Unis"), ("chicago", "États-Unis"),
    ("san francisco", "États-Unis"), ("miami", "États-Unis"), ("boston", "États-Unis"),
    ("barcelone", "Espagne"), ("séville", "Espagne"), ("bilbao", "Espagne"),
    ("milan", "Italie"), ("naples", "Italie"), ("venise", "Italie"), ("florence", "Italie"),
    ("turin", "Italie"), ("munich", "Allemagne"), ("hambourg", "Allemagne"),
    ("francfort", "Allemagne"), ("cologne", "Allemagne"),
    ("marseille", "France"), ("lyon", "France"), ("toulouse", "France"), ("nice", "France"),
    ("bordeaux", "France"), ("nantes", "France"), ("strasbourg", "France"),
    ("sydney", "Australie"), ("melbourne", "Australie"), ("brisbane", "Australie"),
    ("shanghai", "Chine"), ("shenzhen", "Chine"), ("chengdu", "Chine"),
    ("mumbai", "Inde"), ("bangalore", "Inde"), ("calcutta", "Inde"), ("chennai", "Inde"),
    ("rio de janeiro", "Brésil"), ("são paulo", "Brésil"), ("belo horizonte", "Brésil"),
    ("casablanca", "Maroc"), ("marrakech", "Maroc"), ("fès", "Maroc"),
    ("istanbul", "Turquie"), ("izmir", "Turquie"),
    ("saint-pétersbourg", "Russie"), ("novossibirsk", "Russie"),
    ("montréal", "Canada"), ("toronto", "Canada"), ("vancouver", "Canada"),
    ("osaka", "Japon"), ("kyoto", "Japon"), ("yokohama", "Japon"),
    ("manchester", "Royaume-Uni"), ("liverpool", "Royaume-Uni"), ("birmingham", "Royaume-Uni"),
    ("anvers", "Belgique"), ("rotterdam", "Pays-Bas"), ("porto", "Portugal"),
    ("guadalajara", "Mexique"), ("monterrey", "Mexique"),
]

SRC = "géographie de référence (grande ville non capitale -> pays)"


def ingere():
    print(f"== VILLES — ville -> pays ({len(_VILLES)}) ==")
    publie("pays_ville", "physique", SRC, _VILLES)


if __name__ == "__main__":
    ingere()
