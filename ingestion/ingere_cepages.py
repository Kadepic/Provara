"""
INGESTION ŒNOLOGIE — cépage -> couleur du vin/raisin (blanc/rouge)  -> datasets/lecteur/couleur_cepage.jsonl (OFFLINE).

SOURCE : œnologie de référence. Faits STABLES et CERTAINS. FAUX=0 : on écarte les cépages gris/ambigus.
Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_COULEUR = {
    "blanc": ["chardonnay", "sauvignon", "riesling", "chenin", "muscat", "sémillon", "viognier",
              "gewurztraminer", "aligoté", "marsanne"],
    "rouge": ["merlot", "cabernet sauvignon", "pinot noir", "syrah", "gamay", "grenache", "malbec",
              "tempranillo", "sangiovese", "cabernet franc", "mourvèdre", "carignan"],
}

def ingere():
    paires = [(c, coul) for coul, ceps in _PAR_COULEUR.items() for c in ceps]
    print(f"== CÉPAGES -> COULEUR ({len(paires)}) ==")
    publie("couleur_cepage", "convention", "œnologie de référence (cépage -> couleur du vin)", paires)

if __name__ == "__main__":
    ingere()
