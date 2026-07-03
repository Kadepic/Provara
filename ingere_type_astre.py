"""
INGESTION ASTRONOMIE — astre -> type  -> datasets/lecteur/type_astre.jsonl (OFFLINE).

SOURCE : astronomie de référence. Faits STABLES et CERTAINS. astre -> UN type = fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_ASTRES = [
    ("soleil", "étoile"), ("sirius", "étoile"), ("bételgeuse", "étoile"), ("proxima du centaure", "étoile"),
    ("lune", "satellite naturel"), ("titan", "satellite naturel"), ("ganymède", "satellite naturel"),
    ("terre", "planète"), ("mars", "planète"), ("jupiter", "planète"), ("saturne", "planète"),
    ("pluton", "planète naine"), ("cérès", "planète naine"), ("éris", "planète naine"),
    ("halley", "comète"),
    ("voie lactée", "galaxie"), ("andromède", "galaxie"),
]

def ingere():
    print(f"== TYPE D'ASTRE ({len(_ASTRES)}) ==")
    publie("type_astre", "physique", "astronomie de référence (astre -> type)", _ASTRES)

if __name__ == "__main__":
    ingere()
