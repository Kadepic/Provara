"""
INGESTION CORPS HUMAIN — organe sensoriel -> sens  -> datasets/lecteur/sens_organe.jsonl (OFFLINE).

SOURCE : physiologie de référence. Faits STABLES et CERTAINS (les 5 sens). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_SENS = [
    ("œil", "la vue"),
    ("oreille", "l'ouïe"),
    ("nez", "l'odorat"),
    ("langue", "le goût"),
    ("peau", "le toucher"),
]

def ingere():
    print(f"== ORGANE -> SENS ({len(_SENS)}) ==")
    publie("sens_organe", "convention", "physiologie de référence (organe sensoriel -> sens)", _SENS)

if __name__ == "__main__":
    ingere()
