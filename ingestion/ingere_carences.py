"""
INGESTION SANTÉ — vitamine -> maladie de carence  -> datasets/lecteur/carence_vitamine.jsonl (OFFLINE).

SOURCE : médecine de référence. Faits STABLES et CERTAINS (carences classiques). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_CARENCES = [
    ("vitamine c", "le scorbut"),
    ("vitamine d", "le rachitisme"),
    ("vitamine b1", "le béribéri"),
    ("vitamine b3", "la pellagre"),
    ("vitamine a", "la cécité nocturne"),
    ("vitamine b12", "l'anémie pernicieuse"),
    ("vitamine k", "des troubles de la coagulation"),
]

def ingere():
    print(f"== CARENCES VITAMINIQUES ({len(_CARENCES)}) ==")
    publie("carence_vitamine", "convention", "médecine de référence (vitamine -> maladie de carence)", _CARENCES)

if __name__ == "__main__":
    ingere()
