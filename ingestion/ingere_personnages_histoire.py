"""
INGESTION HISTOIRE — personnage historique -> fonction/rôle  -> datasets/lecteur/fonction_personnage.jsonl (OFFLINE).

SOURCE : histoire de référence. Faits STABLES et CERTAINS (titre/rôle principal). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PERSOS = [
    ("napoléon bonaparte", "empereur des Français"),
    ("jules césar", "dictateur romain"),
    ("cléopâtre", "reine d'Égypte"),
    ("louis xiv", "roi de France"),
    ("abraham lincoln", "président des États-Unis"),
    ("gandhi", "leader de l'indépendance indienne"),
    ("winston churchill", "Premier ministre britannique"),
    ("charles de gaulle", "président de la République française"),
    ("vercingétorix", "chef gaulois"),
    ("christophe colomb", "navigateur"),
    ("nelson mandela", "président de l'Afrique du Sud"),
    ("staline", "dirigeant de l'Union soviétique"),
    ("mao zedong", "dirigeant de la Chine"),
    ("jeanne d'arc", "héroïne française de la guerre de Cent Ans"),
    ("alexandre le grand", "roi de Macédoine"),
    ("toutânkhamon", "pharaon d'Égypte"),
    ("george washington", "premier président des États-Unis"),
    ("élisabeth ii", "reine du Royaume-Uni"),
]

def ingere():
    print(f"== PERSONNAGES HISTORIQUES -> FONCTION ({len(_PERSOS)}) ==")
    publie("fonction_personnage", "passe", "histoire de référence (personnage -> fonction)", _PERSOS)

if __name__ == "__main__":
    ingere()
