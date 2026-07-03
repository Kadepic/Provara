"""
INGESTION ÉCONOMIE — monnaie -> subdivision (centième)  -> datasets/lecteur/subdivision_monnaie.jsonl (OFFLINE).

SOURCE : numismatique de référence. Faits STABLES et CERTAINS. monnaie -> UNE subdivision = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_SUBDIVISIONS = [
    ("euro", "centime"),
    ("dollar", "cent"),
    ("livre sterling", "penny"),
    ("rouble", "kopeck"),
    ("roupie indienne", "paisa"),
    ("real", "centavo"),
    ("won", "jeon"),
    ("rand", "cent"),
    ("peso mexicain", "centavo"),
    ("couronne suédoise", "öre"),
]

def ingere():
    print(f"== SUBDIVISIONS MONÉTAIRES ({len(_SUBDIVISIONS)}) ==")
    publie("subdivision_monnaie", "convention", "numismatique (monnaie -> subdivision)", _SUBDIVISIONS)

if __name__ == "__main__":
    ingere()
