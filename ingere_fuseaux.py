"""
INGESTION GÉO — heure locale d'une ville/région -> décalage UTC (heure standard, hors heure d'été)  (OFFLINE).

SOURCE : fuseaux horaires de référence. Faits STABLES et CERTAINS (heure STANDARD). Fonctionnel.
FAUX=0 : on clé par « heure de <ville> » (non ambigu) et on donne l'heure standard (pas l'heure d'été).
"""
from __future__ import annotations
from ingere_wikidata import publie

_FUSEAUX = [
    ("heure de londres", "UTC+0"),
    ("heure de paris", "UTC+1"),
    ("heure de berlin", "UTC+1"),
    ("heure d'athènes", "UTC+2"),
    ("heure de moscou", "UTC+3"),
    ("heure de l'inde", "UTC+5:30"),
    ("heure de pékin", "UTC+8"),
    ("heure de tokyo", "UTC+9"),
    ("heure de sydney", "UTC+10"),
    ("heure de new york", "UTC-5"),
    ("heure de chicago", "UTC-6"),
    ("heure de los angeles", "UTC-8"),
]

def ingere():
    print(f"== FUSEAUX HORAIRES ({len(_FUSEAUX)}) ==")
    publie("decalage_fuseau", "convention", "fuseaux horaires de référence (heure standard -> décalage UTC)", _FUSEAUX)

if __name__ == "__main__":
    ingere()
