"""
INGESTION LANGUE — signe de ponctuation (nom) -> symbole  -> datasets/lecteur/symbole_ponctuation.jsonl (OFFLINE).

SOURCE : typographie de référence. Faits STABLES et CERTAINS.
FAUX=0 : on clé par le NOM (le symbole seul -> "" par normalise). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PONCTUATION = [
    ("point", "."),
    ("virgule", ","),
    ("point-virgule", ";"),
    ("deux-points", ":"),
    ("point d'exclamation", "!"),
    ("point d'interrogation", "?"),
    ("apostrophe", "'"),
    ("trait d'union", "-"),
    ("parenthèse ouvrante", "("),
    ("parenthèse fermante", ")"),
    ("points de suspension", "…"),
    ("arobase", "@"),
    ("dièse", "#"),
    ("astérisque", "*"),
    ("barre oblique", "/"),
]

def ingere():
    print(f"== PONCTUATION — nom -> symbole ({len(_PONCTUATION)}) ==")
    publie("symbole_ponctuation", "convention", "typographie de référence (nom -> symbole)", _PONCTUATION)

if __name__ == "__main__":
    ingere()
