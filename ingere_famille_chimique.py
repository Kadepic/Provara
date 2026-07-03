"""
INGESTION CHIMIE — élément -> famille chimique (groupes nommés)  (OFFLINE).

SOURCE : tableau périodique de référence. Faits STABLES et CERTAINS (appartenance aux groupes nommés).

FAUX=0 — discipline :
  * UNIQUEMENT les familles à définition NON CONTESTÉE par le groupe :
    gaz noble (groupe 18), halogène (groupe 17), métal alcalin (groupe 1, hors hydrogène),
    métal alcalino-terreux (groupe 2). Les « métaux de transition » sont volontairement EXCLUS
    (bornes débattues selon la définition). Élément -> UNE famille = fonctionnel.
  * Complète `groupe_element` (numéro) et `categorie_element` (métal/non-métal) sans recouvrement.
  * Clés = noms FR minuscules.

Usage : python3 ingere_famille_chimique.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_FAMILLE = {
    "gaz noble": ["hélium", "néon", "argon", "krypton", "xénon", "radon"],
    "halogène": ["fluor", "chlore", "brome", "iode", "astate"],
    "métal alcalin": ["lithium", "sodium", "potassium", "rubidium", "césium", "francium"],
    "métal alcalino-terreux": ["béryllium", "magnésium", "calcium", "strontium", "baryum", "radium"],
}

SRC = "tableau périodique de référence (groupes nommés) — faits certains"


def ingere():
    paires = [(e, fam) for fam, elems in _PAR_FAMILLE.items() for e in elems]
    print(f"== CHIMIE — élément -> famille ({len(paires)} éléments, {len(_PAR_FAMILLE)} familles) ==")
    publie("famille_chimique", "physique", SRC, paires)


if __name__ == "__main__":
    ingere()
