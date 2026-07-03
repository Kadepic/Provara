"""
INGESTION ÉCHECS — pièce -> déplacement + valeur  -> datasets/lecteur/*.jsonl (OFFLINE).

SOURCE : règles des échecs. Faits STABLES et CERTAINS (déplacements + valeurs conventionnelles standard).
FAUX=0 : règles non contestées. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

# (pièce, déplacement, valeur en points)
_PIECES = [
    ("pion", "avance d'une case (capture en diagonale)", "1"),
    ("cavalier", "en L (deux cases puis une perpendiculaire)", "3"),
    ("fou", "en diagonale", "3"),
    ("tour", "en ligne droite (lignes et colonnes)", "5"),
    ("dame", "dans toutes les directions", "9"),
    ("roi", "d'une case dans toutes les directions", "0"),
]

def ingere():
    print(f"== ÉCHECS — déplacement + valeur ({len(_PIECES)}) ==")
    publie("deplacement_piece", "convention", "règles des échecs (pièce -> déplacement)",
           [(p, d) for p, d, _ in _PIECES])
    # roi = 0 (inestimable) ; les autres = valeurs conventionnelles standard.
    publie("valeur_piece_echecs", "convention", "échecs (pièce -> valeur conventionnelle en points)",
           [(p, v) for p, _, v in _PIECES])

if __name__ == "__main__":
    ingere()
