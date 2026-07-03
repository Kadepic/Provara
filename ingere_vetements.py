"""
INGESTION VÊTEMENTS — vêtement/accessoire -> partie du corps  -> datasets/lecteur/partie_corps_vetement.jsonl (OFFLINE).

SOURCE : usage courant de référence. Faits STABLES et CERTAINS (partie du corps portée).
FAUX=0 : associations univoques. vêtement -> UNE partie = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_VETEMENTS = [
    ("chapeau", "la tête"), ("casquette", "la tête"), ("bonnet", "la tête"),
    ("chaussure", "les pieds"), ("chaussette", "les pieds"), ("botte", "les pieds"),
    ("gant", "les mains"), ("moufle", "les mains"),
    ("écharpe", "le cou"), ("collier", "le cou"), ("cravate", "le cou"),
    ("lunettes", "les yeux"), ("ceinture", "la taille"),
    ("bague", "le doigt"), ("bracelet", "le poignet"), ("montre", "le poignet"),
    ("boucle d'oreille", "les oreilles"), ("pantalon", "les jambes"),
    ("soutien-gorge", "la poitrine"),
]

def ingere():
    print(f"== VÊTEMENTS -> PARTIE DU CORPS ({len(_VETEMENTS)}) ==")
    publie("partie_corps_vetement", "convention", "usage courant (vêtement -> partie du corps)", _VETEMENTS)

if __name__ == "__main__":
    ingere()
