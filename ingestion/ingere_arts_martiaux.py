"""
INGESTION SPORT — art martial -> pays d'origine  -> datasets/lecteur/pays_art_martial.jsonl (OFFLINE).

SOURCE : histoire des arts martiaux de référence. Faits STABLES et CERTAINS (origine NON CONTESTÉE).
FAUX=0 : on écarte les origines disputées (jiu-jitsu brésilien vs japonais -> on garde « jiu-jitsu »=Japon
traditionnel). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ARTS = [
    ("judo", "Japon"), ("karaté", "Japon"), ("aïkido", "Japon"), ("sumo", "Japon"),
    ("jiu-jitsu", "Japon"), ("kendo", "Japon"),
    ("taekwondo", "Corée du Sud"), ("hapkido", "Corée du Sud"),
    ("kung-fu", "Chine"), ("tai-chi", "Chine"), ("wing chun", "Chine"),
    ("muay-thaï", "Thaïlande"), ("krav-maga", "Israël"),
    ("savate", "France"), ("capoeira", "Brésil"),
]

def ingere():
    print(f"== ARTS MARTIAUX -> PAYS ({len(_ARTS)}) ==")
    publie("pays_art_martial", "convention", "histoire des arts martiaux (art -> pays d'origine)", _ARTS)

if __name__ == "__main__":
    ingere()
