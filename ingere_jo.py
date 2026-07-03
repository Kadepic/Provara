"""
INGESTION SPORT — année -> ville hôte des Jeux olympiques d'été  -> datasets/lecteur/ville_jo_ete.jsonl (OFFLINE).

SOURCE : histoire olympique de référence (CIO). Faits STABLES et CERTAINS. Fonctionnel.
On omet 1916/1940/1944 (annulés, guerres). articles=False (clés = années).
"""
from __future__ import annotations
from ingere_wikidata import publie

_JO = [
    ("1896", "Athènes"), ("1900", "Paris"), ("1904", "Saint-Louis"), ("1908", "Londres"),
    ("1912", "Stockholm"), ("1920", "Anvers"), ("1924", "Paris"), ("1928", "Amsterdam"),
    ("1932", "Los Angeles"), ("1936", "Berlin"), ("1948", "Londres"), ("1952", "Helsinki"),
    ("1956", "Melbourne"), ("1960", "Rome"), ("1964", "Tokyo"), ("1968", "Mexico"),
    ("1972", "Munich"), ("1976", "Montréal"), ("1980", "Moscou"), ("1984", "Los Angeles"),
    ("1988", "Séoul"), ("1992", "Barcelone"), ("1996", "Atlanta"), ("2000", "Sydney"),
    ("2004", "Athènes"), ("2008", "Pékin"), ("2012", "Londres"), ("2016", "Rio de Janeiro"),
    ("2020", "Tokyo"), ("2024", "Paris"),
]

def ingere():
    print(f"== JO ÉTÉ -> VILLE HÔTE ({len(_JO)}) ==")
    publie("ville_jo_ete", "passe", "histoire olympique CIO (année -> ville hôte des JO d'été)", _JO, articles=False)

if __name__ == "__main__":
    ingere()
