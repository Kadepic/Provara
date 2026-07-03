"""
INGESTION MUSIQUE — instrument à cordes -> nombre de cordes  -> datasets/lecteur/nombre_cordes.jsonl (OFFLINE).

SOURCE : facture instrumentale de référence. Faits STABLES et CERTAINS (instruments standard).
FAUX=0 : on garde les instruments à nombre de cordes FIXE et standard (harpe/sitar variables -> exclus).
Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_INSTRUMENTS = [
    ("violon", "4"), ("alto", "4"), ("violoncelle", "4"), ("contrebasse", "4"),
    ("guitare", "6"), ("guitare basse", "4"), ("mandoline", "8"), ("banjo", "5"),
    ("ukulélé", "4"), ("balalaïka", "3"),
]

def ingere():
    print(f"== NOMBRE DE CORDES ({len(_INSTRUMENTS)}) ==")
    publie("nombre_cordes", "convention", "facture instrumentale (instrument -> nombre de cordes)", _INSTRUMENTS)

if __name__ == "__main__":
    ingere()
