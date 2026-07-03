"""
INGESTION GÉOLOGIE — roche -> type (magmatique/sédimentaire/métamorphique)  (OFFLINE).

SOURCE : géologie de référence. Faits STABLES et CERTAINS (classification non contestée).

FAUX=0 — discipline : roches à classification NON CONTESTÉE. Valeurs ∈ {magmatique, sédimentaire,
métamorphique}. roche -> UN type = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_roches.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_TYPE = {
    "magmatique": ["granite", "basalte", "obsidienne", "pierre ponce", "gabbro", "rhyolite", "andésite"],
    "sédimentaire": ["calcaire", "grès", "argile", "craie", "sel gemme", "charbon", "conglomérat", "gypse"],
    "métamorphique": ["marbre", "ardoise", "gneiss", "schiste", "quartzite", "micaschiste"],
}

SRC = "géologie de référence (roche -> type) — classification établie"


def ingere():
    paires = [(r, t) for t, roches in _PAR_TYPE.items() for r in roches]
    print(f"== ROCHES — roche -> type ({len(paires)}) ==")
    publie("type_roche", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
