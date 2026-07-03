"""
INGESTION GEMMOLOGIE — pierre précieuse -> couleur caractéristique  -> datasets/lecteur/couleur_pierre.jsonl (OFFLINE).

SOURCE : gemmologie de référence. Faits STABLES et CERTAINS pour les pierres MONOCHROMES caractéristiques.
FAUX=0 : on ÉCARTE les pierres multicolores (opale, tourmaline, agate). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PIERRES = [
    ("rubis", "rouge"), ("saphir", "bleu"), ("émeraude", "vert"), ("diamant", "incolore"),
    ("améthyste", "violet"), ("topaze", "jaune"), ("grenat", "rouge"), ("jade", "vert"),
    ("péridot", "vert"), ("aigue-marine", "bleu"), ("citrine", "jaune"), ("onyx", "noir"),
    ("lapis-lazuli", "bleu"), ("malachite", "vert"), ("turquoise", "bleu-vert"),
    ("corail", "rouge"), ("jais", "noir"),
]

def ingere():
    print(f"== COULEUR DES PIERRES ({len(_PIERRES)}) ==")
    publie("couleur_pierre", "convention", "gemmologie de référence (pierre -> couleur caractéristique)", _PIERRES)

if __name__ == "__main__":
    ingere()
