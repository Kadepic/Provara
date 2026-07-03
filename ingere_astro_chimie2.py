"""
INGESTION ASTRO + CHIMIE — élément -> couleur de flamme, planète -> plus grande lune  (OFFLINE).

SOURCE : chimie (test à la flamme) + astronomie de référence. Faits STABLES et CERTAINS.

FAUX=0 — discipline :
  * couleur_flamme : couleurs de test à la flamme NON CONTESTÉES (cas classiques de laboratoire).
  * plus_grande_lune : le plus grand satellite de chaque planète (fait certain, indépendant des
    découvertes de petites lunes). Clés/valeurs = noms FR.

Usage : python3 ingere_astro_chimie2.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_FLAMME = [
    ("sodium", "jaune"),
    ("potassium", "lilas"),
    ("lithium", "rouge"),
    ("calcium", "rouge orangé"),
    ("baryum", "vert"),
    ("cuivre", "vert"),
    ("strontium", "rouge écarlate"),
    ("césium", "bleu violet"),
]

_LUNES = [
    ("terre", "Lune"),
    ("mars", "Phobos"),
    ("jupiter", "Ganymède"),
    ("saturne", "Titan"),
    ("uranus", "Titania"),
    ("neptune", "Triton"),
    ("pluton", "Charon"),
]

SRC_F = "chimie de référence (test à la flamme) — couleurs classiques"
SRC_L = "astronomie de référence (plus grand satellite naturel) — certain"


def ingere():
    print(f"== ASTRO+CHIMIE — {len(_FLAMME)} couleurs de flamme, {len(_LUNES)} plus grandes lunes ==")
    publie("couleur_flamme", "physique", SRC_F, _FLAMME)
    publie("plus_grande_lune", "physique", SRC_L, _LUNES)


if __name__ == "__main__":
    ingere()
