"""
INGESTION SPORT — sport -> saison olympique (été / hiver)  -> datasets/lecteur/saison_olympique.jsonl (OFFLINE).

SOURCE : programme olympique de référence. Faits STABLES et CERTAINS. sport -> UNE saison = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_SAISON = {
    "été": ["natation", "athlétisme", "basketball", "aviron", "escrime", "judo", "boxe",
            "gymnastique", "tennis", "volley-ball", "handball", "cyclisme sur route", "tir à l'arc",
            "haltérophilie", "plongeon", "water-polo"],
    "hiver": ["ski alpin", "ski de fond", "patinage artistique", "hockey sur glace", "biathlon",
              "curling", "snowboard", "bobsleigh", "luge", "saut à ski", "patinage de vitesse"],
}

def ingere():
    paires = [(s, sa) for sa, sports in _PAR_SAISON.items() for s in sports]
    print(f"== SAISON OLYMPIQUE ({len(paires)}) ==")
    publie("saison_olympique", "convention", "programme olympique (sport -> été/hiver)", paires)

if __name__ == "__main__":
    ingere()
