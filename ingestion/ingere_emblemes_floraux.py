"""
INGESTION CULTURE — pays -> emblème floral national  -> datasets/lecteur/embleme_floral.jsonl (OFFLINE).

SOURCE : symboles nationaux de référence. Faits STABLES et CERTAINS (emblèmes NON CONTESTÉS). Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_EMBLEMES = [
    ("angleterre", "la rose"),
    ("écosse", "le chardon"),
    ("irlande", "le trèfle"),
    ("pays de galles", "la jonquille"),
    ("pays-bas", "la tulipe"),
    ("japon", "le cerisier"),
    ("inde", "le lotus"),
    ("canada", "la feuille d'érable"),
    ("chine", "la pivoine"),
]

def ingere():
    print(f"== EMBLÈMES FLORAUX ({len(_EMBLEMES)}) ==")
    publie("embleme_floral", "convention", "symboles nationaux (pays -> emblème floral)", _EMBLEMES)

if __name__ == "__main__":
    ingere()
