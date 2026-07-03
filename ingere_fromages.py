"""
INGESTION GASTRONOMIE — fromage -> pays d'origine  -> datasets/lecteur/pays_fromage.jsonl (OFFLINE).

SOURCE : gastronomie de référence (AOP/origines). Faits STABLES et CERTAINS NON CONTESTÉS. Fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_PAYS = {
    "France": ["camembert", "brie", "roquefort", "comté", "reblochon", "munster",
               "cantal", "morbier", "époisses"],
    "Suisse": ["gruyère", "emmental", "appenzell", "raclette", "tête de moine"],
    "Italie": ["mozzarella", "parmesan", "gorgonzola", "ricotta", "mascarpone", "pecorino", "provolone"],
    "Royaume-Uni": ["cheddar", "stilton"],
    "Pays-Bas": ["gouda", "edam"],
    "Grèce": ["feta"],
    "Espagne": ["manchego"],
}

def ingere():
    paires = [(f, p) for p, fromages in _PAR_PAYS.items() for f in fromages]
    print(f"== FROMAGES -> PAYS ({len(paires)}) ==")
    publie("pays_fromage", "convention", "gastronomie de référence (fromage -> pays d'origine)", paires)

if __name__ == "__main__":
    ingere()
