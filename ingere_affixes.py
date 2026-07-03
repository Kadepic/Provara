"""
INGESTION LANGUE — préfixe/suffixe -> sens  -> datasets/lecteur/sens_prefixe.jsonl + sens_suffixe.jsonl (OFFLINE).

SOURCE : étymologie de référence (grec/latin). Faits STABLES et CERTAINS (sens établi). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PREFIXES = [
    ("hyper", "excès, au-dessus"), ("hypo", "insuffisance, en dessous"),
    ("mono", "un seul"), ("bi", "deux"), ("tri", "trois"), ("poly", "plusieurs"),
    ("anti", "contre"), ("péri", "autour"), ("intra", "à l'intérieur"), ("extra", "à l'extérieur"),
    ("sub", "sous"), ("super", "au-dessus"), ("post", "après"), ("pré", "avant"),
    ("néo", "nouveau"), ("paléo", "ancien"), ("micro", "petit"), ("macro", "grand"),
    ("auto", "soi-même"), ("télé", "à distance"), ("hémi", "moitié"), ("omni", "tout"),
    ("multi", "nombreux"), ("pseudo", "faux"),
]

_SUFFIXES = [
    ("-ite", "inflammation"), ("-ome", "tumeur"), ("-logie", "étude, science"),
    ("-phobie", "peur"), ("-phile", "qui aime"), ("-cide", "qui tue"),
    ("-vore", "qui mange"), ("-pathie", "maladie, souffrance"), ("-algie", "douleur"),
    ("-graphie", "écriture, description"), ("-scope", "instrument pour observer"),
    ("-thérapie", "traitement"),
]

def ingere():
    print(f"== AFFIXES — {len(_PREFIXES)} préfixes, {len(_SUFFIXES)} suffixes ==")
    publie("sens_prefixe", "convention", "étymologie de référence (préfixe -> sens)", _PREFIXES)
    publie("sens_suffixe", "convention", "étymologie de référence (suffixe -> sens)", _SUFFIXES, articles=False)

if __name__ == "__main__":
    ingere()
