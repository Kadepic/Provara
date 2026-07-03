"""
INGESTION HISTOIRE — souverain -> surnom  -> datasets/lecteur/surnom_roi.jsonl (OFFLINE).

SOURCE : histoire de référence. Faits STABLES et CERTAINS (surnoms consacrés).
FAUX=0 : surnoms NON CONTESTÉS. souverain -> UN surnom = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ROIS = [
    ("louis xiv", "le Roi-Soleil"),
    ("louis ix", "Saint Louis"),
    ("philippe iv", "le Bel"),
    ("philippe ii", "Auguste"),
    ("louis vi", "le Gros"),
    ("charles le chauve", "le Chauve"),
    ("pépin le bref", "le Bref"),
    ("henri iv", "le Bon Roi Henri (le Vert-Galant)"),
    ("charles le téméraire", "le Téméraire"),
    ("guillaume le conquérant", "le Conquérant"),
    ("richard cœur de lion", "Cœur de Lion"),
    ("ivan le terrible", "le Terrible"),
    ("pierre le grand", "le Grand"),
    ("catherine ii", "la Grande"),
    ("soliman", "le Magnifique"),
    ("alexandre iii de macédoine", "le Grand"),
]

def ingere():
    print(f"== SURNOMS DE SOUVERAINS ({len(_ROIS)}) ==")
    publie("surnom_roi", "convention", "histoire de référence (souverain -> surnom)", _ROIS)

if __name__ == "__main__":
    ingere()
