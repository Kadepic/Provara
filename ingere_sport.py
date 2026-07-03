"""
INGESTION SPORT — discipline -> nombre de joueurs par équipe (sur le terrain)  (OFFLINE).

SOURCE : règlements sportifs de référence. Faits STABLES et CERTAINS (effectif sur le terrain).

FAUX=0 — discipline :
  * Valeur = nombre de joueurs d'UNE équipe SUR LE TERRAIN (gardien inclus le cas échéant).
  * On lève l'ambiguïté du rugby : « rugby à xv » = 15, « rugby à xiii » = 13 (clés distinctes).
  * Faits non contestés uniquement. Clés = noms FR minuscules.

Usage : python3 ingere_sport.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (sport, joueurs par équipe sur le terrain)
_SPORTS = [
    ("football", 11),
    ("football américain", 11),
    ("basketball", 5),
    ("basket-ball", 5),
    ("volley-ball", 6),
    ("beach-volley", 2),
    ("handball", 7),
    ("rugby à xv", 15),
    ("rugby à xiii", 13),
    ("hockey sur glace", 6),
    ("hockey sur gazon", 11),
    ("water-polo", 7),
    ("baseball", 9),
    ("cricket", 11),
    ("netball", 7),
    ("polo", 4),
    ("kabaddi", 7),
]

SRC = "règlements sportifs de référence (effectif sur le terrain) — faits certains"


def ingere():
    print(f"== SPORT — {len(_SPORTS)} disciplines : joueurs par équipe ==")
    publie("joueurs_par_equipe", "convention", SRC, [(s, str(n)) for s, n in _SPORTS])


if __name__ == "__main__":
    ingere()
