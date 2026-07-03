"""
INGESTION MÉTROLOGIE — instrument -> grandeur mesurée  -> datasets/lecteur/mesure_instrument.jsonl (OFFLINE).

SOURCE : physique/métrologie de référence. Faits STABLES et CERTAINS (fonction de l'instrument).

FAUX=0 : instruments à grandeur NON CONTESTÉE. instrument -> UNE grandeur = fonctionnel. Clés FR minuscules.

Usage : python3 ingere_instruments_mesure.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_INSTRUMENTS = [
    ("thermomètre", "la température"),
    ("baromètre", "la pression atmosphérique"),
    ("hygromètre", "l'humidité"),
    ("anémomètre", "la vitesse du vent"),
    ("sismographe", "les séismes"),
    ("balance", "la masse"),
    ("chronomètre", "le temps"),
    ("voltmètre", "la tension électrique"),
    ("ampèremètre", "l'intensité électrique"),
    ("ohmmètre", "la résistance électrique"),
    ("podomètre", "le nombre de pas"),
    ("odomètre", "la distance parcourue"),
    ("tensiomètre", "la pression artérielle"),
    ("boussole", "la direction (le nord)"),
    ("luxmètre", "l'éclairement lumineux"),
    ("sonomètre", "le niveau sonore"),
    ("manomètre", "la pression d'un fluide"),
    ("dynamomètre", "la force"),
    ("altimètre", "l'altitude"),
    ("compteur geiger", "la radioactivité"),
    ("pèse-personne", "le poids"),
    ("pluviomètre", "les précipitations"),
]

SRC = "métrologie de référence (instrument -> grandeur mesurée)"


def ingere():
    print(f"== INSTRUMENTS DE MESURE ({len(_INSTRUMENTS)}) ==")
    publie("mesure_instrument", "convention", SRC, _INSTRUMENTS)


if __name__ == "__main__":
    ingere()
