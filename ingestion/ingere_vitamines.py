"""
INGESTION SANTÉ — vitamine -> nom chimique -> datasets/lecteur/nom_vitamine.jsonl  (OFFLINE).

SOURCE : biochimie de référence. Faits STABLES et CERTAINS (noms chimiques officiels des vitamines).

FAUX=0 — discipline : noms chimiques NON CONTESTÉS (nomenclature établie). vitamine -> UN nom = fonctionnel.
Clés = désignations FR minuscules (« vitamine c »). Le lecteur normalise.

Usage : python3 ingere_vitamines.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_VITAMINES = [
    ("vitamine a", "rétinol"),
    ("vitamine b1", "thiamine"),
    ("vitamine b2", "riboflavine"),
    ("vitamine b3", "niacine"),
    ("vitamine b5", "acide pantothénique"),
    ("vitamine b6", "pyridoxine"),
    ("vitamine b8", "biotine"),
    ("vitamine b9", "acide folique"),
    ("vitamine b12", "cobalamine"),
    ("vitamine c", "acide ascorbique"),
    ("vitamine d", "calciférol"),
    ("vitamine e", "tocophérol"),
    ("vitamine k", "phylloquinone"),
]

SRC = "biochimie de référence (nom chimique des vitamines) — nomenclature établie"


def ingere():
    print(f"== VITAMINES — vitamine -> nom chimique ({len(_VITAMINES)}) ==")
    publie("nom_vitamine", "convention", SRC, _VITAMINES)


if __name__ == "__main__":
    ingere()
