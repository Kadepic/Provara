"""
INGESTION FÊTES NATIONALES — pays -> date de la fête nationale  (OFFLINE).

SOURCE : connaissance civique de référence. Faits STABLES et CERTAINS (dates officielles).

FAUX=0 — discipline : UNIQUEMENT les dates officielles NON CONTESTÉES. pays -> UNE date = fonctionnel.
Valeur = date « jour mois » en clair. Clés = noms FR minuscules ; le lecteur normalise.

Usage : python3 ingere_fetes_nationales.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_FETES = [
    ("france", "14 juillet"),
    ("états-unis", "4 juillet"),
    ("canada", "1er juillet"),
    ("belgique", "21 juillet"),
    ("suisse", "1er août"),
    ("italie", "2 juin"),
    ("allemagne", "3 octobre"),
    ("espagne", "12 octobre"),
    ("portugal", "10 juin"),
    ("mexique", "16 septembre"),
    ("brésil", "7 septembre"),
    ("argentine", "9 juillet"),
    ("inde", "15 août"),
    ("chine", "1er octobre"),
    ("japon", "11 février"),
    ("australie", "26 janvier"),
    ("grèce", "25 mars"),
    ("irlande", "17 mars"),
    ("pays-bas", "27 avril"),
    ("suède", "6 juin"),
    ("norvège", "17 mai"),
    ("finlande", "6 décembre"),
    ("pologne", "3 mai"),
    ("autriche", "26 octobre"),
    ("russie", "12 juin"),
    ("luxembourg", "23 juin"),
    ("maroc", "30 juillet"),
    ("égypte", "23 juillet"),
]

SRC = "connaissance civique de référence (fête nationale) — dates officielles"


def ingere():
    print(f"== FÊTES NATIONALES — pays -> date ({len(_FETES)}) ==")
    publie("fete_nationale", "convention", SRC, _FETES)


if __name__ == "__main__":
    ingere()
