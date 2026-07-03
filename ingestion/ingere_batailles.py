"""
INGESTION HISTOIRE — bataille -> guerre/conflit  -> datasets/lecteur/guerre_bataille.jsonl (OFFLINE).

SOURCE : histoire militaire de référence. Faits STABLES et CERTAINS. bataille -> UN conflit = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_BATAILLES = [
    ("waterloo", "les guerres napoléoniennes"),
    ("austerlitz", "les guerres napoléoniennes"),
    ("trafalgar", "les guerres napoléoniennes"),
    ("iéna", "les guerres napoléoniennes"),
    ("verdun", "la Première Guerre mondiale"),
    ("la marne", "la Première Guerre mondiale"),
    ("la somme", "la Première Guerre mondiale"),
    ("stalingrad", "la Seconde Guerre mondiale"),
    ("normandie", "la Seconde Guerre mondiale"),
    ("el alamein", "la Seconde Guerre mondiale"),
    ("midway", "la Seconde Guerre mondiale"),
    ("hastings", "la conquête normande de l'Angleterre"),
    ("azincourt", "la guerre de Cent Ans"),
    ("crécy", "la guerre de Cent Ans"),
    ("marignan", "les guerres d'Italie"),
    ("gettysburg", "la guerre de Sécession"),
    ("gergovie", "la guerre des Gaules"),
    ("alésia", "la guerre des Gaules"),
]

def ingere():
    print(f"== BATAILLES -> GUERRE ({len(_BATAILLES)}) ==")
    publie("guerre_bataille", "passe", "histoire militaire (bataille -> conflit)", _BATAILLES)

if __name__ == "__main__":
    ingere()
