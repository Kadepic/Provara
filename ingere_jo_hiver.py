"""
INGESTION SPORT — année -> ville hôte des JO d'hiver  -> datasets/lecteur/ville_jo_hiver.jsonl (OFFLINE).

SOURCE : histoire olympique CIO. Faits STABLES et CERTAINS. Fonctionnel. articles=False (clés = années).
(relation distincte de ville_jo_ete -> mêmes années possibles sans conflit.)
"""
from __future__ import annotations
from ingere_wikidata import publie

_JO = [
    ("1924", "Chamonix"), ("1928", "Saint-Moritz"), ("1932", "Lake Placid"),
    ("1936", "Garmisch-Partenkirchen"), ("1948", "Saint-Moritz"), ("1952", "Oslo"),
    ("1956", "Cortina d'Ampezzo"), ("1960", "Squaw Valley"), ("1964", "Innsbruck"),
    ("1968", "Grenoble"), ("1972", "Sapporo"), ("1976", "Innsbruck"), ("1980", "Lake Placid"),
    ("1984", "Sarajevo"), ("1988", "Calgary"), ("1992", "Albertville"), ("1994", "Lillehammer"),
    ("1998", "Nagano"), ("2002", "Salt Lake City"), ("2006", "Turin"), ("2010", "Vancouver"),
    ("2014", "Sotchi"), ("2018", "Pyeongchang"), ("2022", "Pékin"),
]

def ingere():
    print(f"== JO HIVER -> VILLE HÔTE ({len(_JO)}) ==")
    publie("ville_jo_hiver", "passe", "histoire olympique CIO (année -> ville hôte des JO d'hiver)", _JO, articles=False)

if __name__ == "__main__":
    ingere()
