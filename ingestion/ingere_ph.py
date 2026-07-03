"""
INGESTION CHIMIE — substance -> caractère acido-basique  -> datasets/lecteur/ph_substance.jsonl (OFFLINE).

SOURCE : chimie de référence. Faits STABLES et CERTAINS pour les cas NON AMBIGUS.
FAUX=0 : valeurs ∈ {acide, basique, neutre}. On écarte les cas limites (lait, sang, café). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PH = [
    ("citron", "acide"), ("vinaigre", "acide"), ("jus d'orange", "acide"),
    ("acide chlorhydrique", "acide"), ("acide sulfurique", "acide"), ("coca-cola", "acide"),
    ("eau pure", "neutre"), ("eau distillée", "neutre"),
    ("savon", "basique"), ("eau de javel", "basique"), ("bicarbonate de soude", "basique"),
    ("soude caustique", "basique"), ("ammoniaque", "basique"), ("eau savonneuse", "basique"),
]

def ingere():
    print(f"== pH DES SUBSTANCES ({len(_PH)}) ==")
    publie("ph_substance", "physique", "chimie de référence (substance -> acide/basique/neutre)", _PH)

if __name__ == "__main__":
    ingere()
