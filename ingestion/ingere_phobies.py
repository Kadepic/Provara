"""
INGESTION PHOBIES — phobie -> objet de la peur  -> datasets/lecteur/objet_phobie.jsonl (OFFLINE).

SOURCE : terminologie médicale/étymologique de référence. Faits STABLES et CERTAINS (sens établi).

FAUX=0 — discipline : phobies à sens étymologique NON CONTESTÉ. phobie -> UN objet = fonctionnel.
Clés = noms FR minuscules.

Usage : python3 ingere_phobies.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PHOBIES = [
    ("arachnophobie", "les araignées"),
    ("claustrophobie", "les espaces clos"),
    ("agoraphobie", "les espaces ouverts et la foule"),
    ("acrophobie", "les hauteurs"),
    ("aquaphobie", "l'eau"),
    ("aérophobie", "l'avion"),
    ("ophidiophobie", "les serpents"),
    ("cynophobie", "les chiens"),
    ("ailurophobie", "les chats"),
    ("nyctophobie", "l'obscurité"),
    ("thanatophobie", "la mort"),
    ("hémophobie", "le sang"),
    ("pyrophobie", "le feu"),
    ("zoophobie", "les animaux"),
    ("coulrophobie", "les clowns"),
    ("trypanophobie", "les piqûres et aiguilles"),
    ("entomophobie", "les insectes"),
    ("ornithophobie", "les oiseaux"),
    ("astraphobie", "les éclairs et le tonnerre"),
    ("xénophobie", "les étrangers"),
    ("dentophobie", "le dentiste"),
]

SRC = "terminologie médicale/étymologique de référence (phobie -> objet)"


def ingere():
    print(f"== PHOBIES — phobie -> objet ({len(_PHOBIES)}) ==")
    publie("objet_phobie", "convention", SRC, _PHOBIES)


if __name__ == "__main__":
    ingere()
