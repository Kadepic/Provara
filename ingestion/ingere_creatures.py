"""
INGESTION MYTHOLOGIE — créature légendaire -> mythologie d'origine  -> datasets/lecteur/origine_creature.jsonl (OFFLINE).

SOURCE : mythologies de référence. Faits STABLES et CERTAINS pour les créatures à origine NON CONTESTÉE.
FAUX=0 : on écarte les créatures multi-origines (sphinx, dragon, phénix, vampire). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_CREATURES = [
    ("minotaure", "grecque"), ("centaure", "grecque"), ("méduse", "grecque"),
    ("cyclope", "grecque"), ("pégase", "grecque"), ("cerbère", "grecque"),
    ("hydre de lerne", "grecque"), ("chimère", "grecque"), ("harpie", "grecque"),
    ("satyre", "grecque"), ("griffon", "grecque"),
    ("troll", "nordique"), ("kraken", "nordique"), ("elfe", "nordique"),
    ("nain", "nordique"), ("valkyrie", "nordique"),
    ("golem", "juive"), ("yéti", "himalayenne"), ("wendigo", "amérindienne"),
]

def ingere():
    print(f"== CRÉATURES -> MYTHOLOGIE ({len(_CREATURES)}) ==")
    publie("origine_creature", "convention", "mythologies de référence (créature -> origine)", _CREATURES)

if __name__ == "__main__":
    ingere()
