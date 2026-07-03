"""
INGESTION FRANÇAIS — nombre -> écriture en lettres  -> datasets/lecteur/nombre_en_lettres.jsonl (OFFLINE).

SOURCE : orthographe française de référence. Faits STABLES et CERTAINS. nombre -> UNE écriture = fonctionnel.
Clés = chiffres (chaînes) ; articles=False (les chiffres ne sont pas des articles).
"""
from __future__ import annotations
from ingere_wikidata import publie

_NOMBRES = [
    ("0", "zéro"), ("1", "un"), ("2", "deux"), ("3", "trois"), ("4", "quatre"),
    ("5", "cinq"), ("6", "six"), ("7", "sept"), ("8", "huit"), ("9", "neuf"),
    ("10", "dix"), ("11", "onze"), ("12", "douze"), ("13", "treize"), ("14", "quatorze"),
    ("15", "quinze"), ("16", "seize"), ("17", "dix-sept"), ("18", "dix-huit"), ("19", "dix-neuf"),
    ("20", "vingt"), ("30", "trente"), ("40", "quarante"), ("50", "cinquante"),
    ("60", "soixante"), ("70", "soixante-dix"), ("80", "quatre-vingts"), ("90", "quatre-vingt-dix"),
    ("100", "cent"), ("1000", "mille"), ("1000000", "un million"),
]

def ingere():
    print(f"== NOMBRES EN LETTRES ({len(_NOMBRES)}) ==")
    publie("nombre_en_lettres", "convention", "orthographe française (nombre -> lettres)", _NOMBRES, articles=False)

if __name__ == "__main__":
    ingere()
