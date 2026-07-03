"""
INGESTION CHIMIE — ion -> charge  -> datasets/lecteur/charge_ion.jsonl (OFFLINE).

SOURCE : chimie de référence. Faits STABLES et CERTAINS. FAUX=0 : on clé par le NOM de l'ion
(le symbole avec +/- est réduit à "" par normalise). ion -> UNE charge = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_IONS = [
    ("ion sodium", "+1"), ("ion potassium", "+1"), ("ion ammonium", "+1"),
    ("ion hydrogène", "+1"), ("ion argent", "+1"),
    ("ion calcium", "+2"), ("ion magnésium", "+2"), ("ion fer ii", "+2"),
    ("ion cuivre ii", "+2"), ("ion zinc", "+2"),
    ("ion aluminium", "+3"), ("ion fer iii", "+3"),
    ("ion chlorure", "-1"), ("ion hydroxyde", "-1"), ("ion nitrate", "-1"),
    ("ion fluorure", "-1"),
    ("ion oxyde", "-2"), ("ion sulfate", "-2"), ("ion carbonate", "-2"),
    ("ion phosphate", "-3"),
]

def ingere():
    print(f"== CHARGE DES IONS ({len(_IONS)}) ==")
    publie("charge_ion", "physique", "chimie de référence (ion -> charge)", _IONS)

if __name__ == "__main__":
    ingere()
