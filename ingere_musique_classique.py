"""
INGESTION MUSIQUE CLASSIQUE — œuvre -> compositeur -> datasets/lecteur/compositeur_oeuvre.jsonl (OFFLINE).

SOURCE : histoire de la musique de référence. Faits STABLES et CERTAINS (paternité non contestée).

FAUX=0 — discipline : œuvres célèbres à compositeur NON CONTESTÉ. œuvre -> UN compositeur = fonctionnel.
Clés = titres FR minuscules ; le lecteur normalise.

Usage : python3 ingere_musique_classique.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_OEUVRES = [
    ("la flûte enchantée", "Wolfgang Amadeus Mozart"),
    ("les noces de figaro", "Wolfgang Amadeus Mozart"),
    ("don giovanni", "Wolfgang Amadeus Mozart"),
    ("requiem (mozart)", "Wolfgang Amadeus Mozart"),
    ("la neuvième symphonie", "Ludwig van Beethoven"),
    ("la cinquième symphonie", "Ludwig van Beethoven"),
    ("la lettre à élise", "Ludwig van Beethoven"),
    ("clair de lune (sonate)", "Ludwig van Beethoven"),
    ("les quatre saisons", "Antonio Vivaldi"),
    ("le boléro", "Maurice Ravel"),
    ("carmen", "Georges Bizet"),
    ("la traviata", "Giuseppe Verdi"),
    ("aïda", "Giuseppe Verdi"),
    ("nabucco", "Giuseppe Verdi"),
    ("le barbier de séville", "Gioachino Rossini"),
    ("le messie", "Georg Friedrich Haendel"),
    ("le lac des cygnes", "Piotr Ilitch Tchaïkovski"),
    ("casse-noisette", "Piotr Ilitch Tchaïkovski"),
    ("la belle au bois dormant (ballet)", "Piotr Ilitch Tchaïkovski"),
    ("les variations goldberg", "Jean-Sébastien Bach"),
    ("la passion selon saint matthieu", "Jean-Sébastien Bach"),
    ("la chevauchée des walkyries", "Richard Wagner"),
    ("tristan et isolde", "Richard Wagner"),
    ("le beau danube bleu", "Johann Strauss II"),
    ("la marche turque", "Wolfgang Amadeus Mozart"),
    ("le sacre du printemps", "Igor Stravinsky"),
    ("gymnopédies", "Erik Satie"),
    ("clair de lune (debussy)", "Claude Debussy"),
    ("la mer", "Claude Debussy"),
    ("rhapsody in blue", "George Gershwin"),
]

SRC = "histoire de la musique de référence (œuvre -> compositeur) — paternité non contestée"


def ingere():
    print(f"== MUSIQUE CLASSIQUE — œuvre -> compositeur ({len(_OEUVRES)}) ==")
    publie("compositeur_oeuvre", "convention", SRC, _OEUVRES)


if __name__ == "__main__":
    ingere()
