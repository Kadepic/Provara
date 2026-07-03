"""
INGESTION CIVISME — pays -> devise nationale  -> datasets/lecteur/devise_pays.jsonl (OFFLINE).

SOURCE : symboles nationaux de référence. Faits STABLES et CERTAINS (devises officielles).
FAUX=0 : devises officielles NON CONTESTÉES. pays -> UNE devise = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_DEVISES = [
    ("france", "Liberté, Égalité, Fraternité"),
    ("états-unis", "In God We Trust"),
    ("belgique", "L'union fait la force"),
    ("canada", "D'un océan à l'autre"),
    ("royaume-uni", "Dieu et mon droit"),
    ("suisse", "Un pour tous, tous pour un"),
    ("brésil", "Ordre et progrès"),
    ("espagne", "Plus Ultra"),
    ("pays-bas", "Je maintiendrai"),
    ("inde", "Seule la vérité triomphe"),
    ("grèce", "La liberté ou la mort"),
    ("monaco", "Avec l'aide de Dieu"),
]

def ingere():
    print(f"== DEVISES NATIONALES ({len(_DEVISES)}) ==")
    publie("devise_pays", "convention", "symboles nationaux (pays -> devise)", _DEVISES)

if __name__ == "__main__":
    ingere()
