"""
INGESTION CHIMIE — composé -> formule brute (extension de `formule_chimique`)  (OFFLINE).

SOURCE : nomenclature chimique de référence. Faits STABLES et CERTAINS (formules brutes textbook).

FAUX=0 — discipline :
  * ÉTEND l'amorce `formule_chimique` (eau, CO2, CH4, glucose, NaCl…) SANS recouvrement -> aucune
    contradiction (extension sans contradiction). Uniquement des formules brutes NON contestées.
  * composé -> UNE formule = fonctionnel. Clés = noms FR minuscules ; le lecteur normalise.

Usage : python3 ingere_composes.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (composé, formule brute) — AUCUN recouvrement avec l'amorce _FORMULE_CHIMIQUE de lecteur.py.
_COMPOSES = [
    ("éthanol", "C2H6O"),
    ("méthanol", "CH4O"),
    ("acide sulfurique", "H2SO4"),
    ("hydroxyde de sodium", "NaOH"),
    ("dihydrogène", "H2"),
    ("acide nitrique", "HNO3"),
    ("carbonate de calcium", "CaCO3"),
    ("saccharose", "C12H22O11"),
    ("acide acétique", "C2H4O2"),
    ("dioxyde de soufre", "SO2"),
    ("sulfure d'hydrogène", "H2S"),
    ("chlorure de potassium", "KCl"),
    ("oxyde de fer (III)", "Fe2O3"),
    ("hydroxyde de potassium", "KOH"),
    ("acide phosphorique", "H3PO4"),
    ("nitrate de potassium", "KNO3"),
    ("bicarbonate de sodium", "NaHCO3"),
    ("benzène", "C6H6"),
    ("acétone", "C3H6O"),
    ("propane", "C3H8"),
    ("butane", "C4H10"),
    ("éthylène", "C2H4"),
    ("acétylène", "C2H2"),
    ("urée", "CH4N2O"),
    ("oxyde de calcium", "CaO"),
    ("acide fluorhydrique", "HF"),
    ("chlorure de calcium", "CaCl2"),
    ("sulfate de cuivre", "CuSO4"),
]

SRC = "nomenclature chimique de référence (formule brute) — extension de formule_chimique"


def ingere():
    print(f"== CHIMIE — composé -> formule ({len(_COMPOSES)} composés, extension) ==")
    publie("formule_chimique", "physique", SRC, _COMPOSES)


if __name__ == "__main__":
    ingere()
