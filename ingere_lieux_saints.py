"""
INGESTION RELIGIONS — religion -> ville/lieu saint principal  -> datasets/lecteur/lieu_saint_religion.jsonl (OFFLINE).

SOURCE : connaissance religieuse de référence. Faits STABLES et CERTAINS. religion -> UN lieu = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_LIEUX = [
    ("islam", "La Mecque"),
    ("judaïsme", "Jérusalem"),
    ("hindouisme", "Bénarès (Varanasi)"),
    ("bouddhisme", "Bodh-Gaya"),
    ("sikhisme", "Amritsar"),
    ("catholicisme", "Rome (le Vatican)"),
]

def ingere():
    print(f"== LIEUX SAINTS ({len(_LIEUX)}) ==")
    publie("lieu_saint_religion", "convention", "connaissance religieuse (religion -> lieu saint)", _LIEUX)

if __name__ == "__main__":
    ingere()
