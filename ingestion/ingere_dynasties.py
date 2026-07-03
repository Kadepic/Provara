"""
INGESTION HISTOIRE — dynastie -> pays principal  -> datasets/lecteur/pays_dynastie.jsonl (OFFLINE).

SOURCE : histoire de référence. Faits STABLES et CERTAINS (pays principal de la dynastie). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_DYNASTIES = [
    ("bourbon", "France"), ("capétiens", "France"), ("valois", "France"),
    ("habsbourg", "Autriche"), ("hohenzollern", "Allemagne"),
    ("tudor", "Angleterre"), ("plantagenêt", "Angleterre"), ("windsor", "Royaume-Uni"),
    ("romanov", "Russie"),
    ("ming", "Chine"), ("qing", "Chine"), ("han", "Chine"), ("tang", "Chine"),
    ("médicis", "Italie"), ("savoie", "Italie"),
]

def ingere():
    print(f"== DYNASTIES -> PAYS ({len(_DYNASTIES)}) ==")
    publie("pays_dynastie", "passe", "histoire de référence (dynastie -> pays principal)", _DYNASTIES)

if __name__ == "__main__":
    ingere()
