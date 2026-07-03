"""
INGESTION ZOOLOGIE/LANGUE — animal -> cri (nom du cri) -> datasets/lecteur/cri_animal.jsonl (OFFLINE).

SOURCE : lexique français de référence (noms des cris d'animaux). Faits STABLES et CERTAINS.

FAUX=0 — discipline : UNIQUEMENT les noms de cris standard NON CONTESTÉS du dictionnaire. On ÉCARTE
les animaux à cri multiple/ambigu. animal -> UN cri = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_cris_animaux.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_CRIS = [
    ("chien", "aboiement"),
    ("chat", "miaulement"),
    ("vache", "meuglement"),
    ("cheval", "hennissement"),
    ("mouton", "bêlement"),
    ("chèvre", "bêlement"),
    ("cochon", "grognement"),
    ("âne", "braiement"),
    ("lion", "rugissement"),
    ("loup", "hurlement"),
    ("éléphant", "barrissement"),
    ("serpent", "sifflement"),
    ("grenouille", "coassement"),
    ("abeille", "bourdonnement"),
    ("corbeau", "croassement"),
    ("hibou", "hululement"),
    ("pigeon", "roucoulement"),
    ("canard", "cancanement"),
    ("souris", "couinement"),
    ("poule", "gloussement"),
    ("coq", "cocorico"),
    ("dindon", "glouglottement"),
    ("oie", "cacardement"),
    ("cigale", "stridulation"),
    ("tigre", "feulement"),
    ("ours", "grognement"),
    ("cerf", "brame"),
    ("éléphant de mer", "barrissement"),
    ("hirondelle", "gazouillis"),
    ("colombe", "roucoulement"),
]

SRC = "lexique français de référence (cri d'animal) — noms standard"


def ingere():
    print(f"== CRIS D'ANIMAUX — animal -> cri ({len(_CRIS)}) ==")
    publie("cri_animal", "convention", SRC, _CRIS)


if __name__ == "__main__":
    ingere()
