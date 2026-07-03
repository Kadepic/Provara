"""
INGESTION BIOLOGIE — animal -> régime alimentaire  -> datasets/lecteur/regime_alimentaire.jsonl (OFFLINE).

SOURCE : biologie de référence. Faits STABLES et CERTAINS pour les cas NON AMBIGUS.

FAUX=0 — discipline : UNIQUEMENT les animaux à régime NON CONTESTÉ (on ÉCARTE les cas discutés :
renard, écureuil…). Valeurs ∈ {carnivore, herbivore, omnivore}. animal -> UN régime = fonctionnel.

Usage : python3 ingere_regime_alimentaire.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_REGIME = {
    "carnivore": ["lion", "tigre", "loup", "requin", "crocodile", "aigle", "guépard", "léopard",
                  "hyène", "orque", "faucon", "lynx", "panthère", "jaguar", "phoque"],
    "herbivore": ["vache", "mouton", "chèvre", "cheval", "lapin", "girafe", "éléphant", "zèbre",
                  "cerf", "gazelle", "hippopotame", "rhinocéros", "panda", "koala", "kangourou",
                  "bison", "chameau", "âne", "antilope", "buffle"],
    "omnivore": ["cochon", "sanglier", "rat", "ours", "singe", "chimpanzé", "poule", "corbeau",
                 "hérisson", "raton laveur", "souris", "canard"],
}

SRC = "biologie de référence (régime alimentaire) — cas non ambigus"


def ingere():
    paires = [(a, reg) for reg, animaux in _PAR_REGIME.items() for a in animaux]
    print(f"== RÉGIME ALIMENTAIRE — {len(paires)} animaux ==")
    publie("regime_alimentaire", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
