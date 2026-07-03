"""
INGESTION RELIGIONS — religion -> jour saint hebdomadaire  -> datasets/lecteur/jour_saint_religion.jsonl (OFFLINE).

SOURCE : connaissance religieuse de référence. Faits STABLES et CERTAINS pour les religions à jour
hebdomadaire DÉFINI (on écarte celles sans jour unique). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_JOURS = [
    ("judaïsme", "samedi (shabbat)"),
    ("islam", "vendredi"),
    ("christianisme", "dimanche"),
    ("catholicisme", "dimanche"),
    ("protestantisme", "dimanche"),
]

def ingere():
    print(f"== JOURS SAINTS ({len(_JOURS)}) ==")
    publie("jour_saint_religion", "convention", "connaissance religieuse (religion -> jour saint)", _JOURS)

if __name__ == "__main__":
    ingere()
