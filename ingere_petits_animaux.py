"""
INGESTION ZOOLOGIE/LANGUE — animal -> nom du petit  -> datasets/lecteur/petit_animal.jsonl (OFFLINE).

SOURCE : lexique français de référence. Faits STABLES et CERTAINS (noms standard des petits).

FAUX=0 — discipline : noms du petit NON CONTESTÉS du dictionnaire. animal -> UN petit = fonctionnel.
Clés = noms FR minuscules.

Usage : python3 ingere_petits_animaux.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PETITS = [
    ("chien", "chiot"), ("chat", "chaton"), ("vache", "veau"), ("cheval", "poulain"),
    ("mouton", "agneau"), ("chèvre", "chevreau"), ("cochon", "porcelet"), ("lapin", "lapereau"),
    ("poule", "poussin"), ("lion", "lionceau"), ("ours", "ourson"), ("loup", "louveteau"),
    ("cerf", "faon"), ("biche", "faon"), ("sanglier", "marcassin"), ("oie", "oison"),
    ("canard", "caneton"), ("aigle", "aiglon"), ("éléphant", "éléphanteau"), ("baleine", "baleineau"),
    ("renard", "renardeau"), ("lièvre", "levraut"), ("grenouille", "têtard"), ("chevreuil", "faon"),
    ("dinde", "dindonneau"), ("pigeon", "pigeonneau"), ("rat", "raton"), ("souris", "souriceau"),
]

SRC = "lexique français de référence (animal -> nom du petit)"


def ingere():
    print(f"== PETITS D'ANIMAUX — animal -> petit ({len(_PETITS)}) ==")
    publie("petit_animal", "convention", SRC, _PETITS)


if __name__ == "__main__":
    ingere()
