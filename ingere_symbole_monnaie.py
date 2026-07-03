"""
INGESTION ÉCONOMIE — monnaie -> symbole monétaire -> datasets/lecteur/symbole_monnaie.jsonl (OFFLINE).

SOURCE : symboles monétaires Unicode officiels. Faits STABLES et CERTAINS.

FAUX=0 — discipline :
  * UNIQUEMENT les monnaies à symbole DISTINCTIF et NON AMBIGU (on ÉCARTE les « $ » partagés par de
    nombreux dollars, et les monnaies sans symbole dédié -> code à 3 lettres).
  * monnaie -> UN symbole = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_symbole_monnaie.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_MONNAIES = [
    ("euro", "€"),
    ("livre sterling", "£"),
    ("yen", "¥"),
    ("yuan", "¥"),
    ("won", "₩"),
    ("roupie indienne", "₹"),
    ("rouble", "₽"),
    ("lira turque", "₺"),
    ("naira", "₦"),
    ("baht", "฿"),
    ("dong", "₫"),
    ("hryvnia", "₴"),
    ("peso philippin", "₱"),
    ("shekel", "₪"),
    ("dollar", "$"),
    ("cent", "¢"),
]

SRC = "symboles monétaires Unicode officiels — faits certains"


def ingere():
    print(f"== ÉCONOMIE — monnaie -> symbole ({len(_MONNAIES)}) ==")
    publie("symbole_monnaie", "convention", SRC, _MONNAIES)


if __name__ == "__main__":
    ingere()
