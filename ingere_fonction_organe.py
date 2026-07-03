"""
INGESTION CORPS HUMAIN — organe -> fonction principale  -> datasets/lecteur/fonction_organe.jsonl (OFFLINE).

SOURCE : physiologie de référence. Faits STABLES et CERTAINS (fonction principale non contestée).

FAUX=0 — discipline : fonction PRINCIPALE univoque. organe -> UNE fonction = fonctionnel.
Clés = noms FR minuscules.

Usage : python3 ingere_fonction_organe.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_FONCTIONS = [
    ("cœur", "pomper le sang"),
    ("poumon", "permettre la respiration"),
    ("estomac", "digérer les aliments"),
    ("rein", "filtrer le sang et produire l'urine"),
    ("cerveau", "commander le corps et la pensée"),
    ("foie", "filtrer les toxines et stocker l'énergie"),
    ("peau", "protéger le corps"),
    ("oreille", "permettre l'audition"),
    ("œil", "permettre la vision"),
    ("langue", "percevoir le goût"),
    ("nez", "permettre l'odorat"),
    ("intestin", "absorber les nutriments"),
    ("vessie", "stocker l'urine"),
    ("pancréas", "réguler la glycémie et aider la digestion"),
    ("rate", "filtrer le sang et soutenir l'immunité"),
    ("moelle épinière", "transmettre les influx nerveux"),
    ("diaphragme", "permettre la respiration"),
]

SRC = "physiologie de référence (organe -> fonction principale)"


def ingere():
    print(f"== FONCTION ORGANE — organe -> fonction ({len(_FONCTIONS)}) ==")
    publie("fonction_organe", "convention", SRC, _FONCTIONS)


if __name__ == "__main__":
    ingere()
