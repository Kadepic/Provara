"""
INGESTION SCIENCES — découverte/théorie -> auteur -> datasets/lecteur/auteur_decouverte.jsonl (OFFLINE).

SOURCE : histoire des sciences de référence. Faits STABLES et CERTAINS (attributions consensuelles).

FAUX=0 — discipline :
  * UNIQUEMENT des attributions NON CONTESTÉES (on ÉCARTE les paternités disputées : structure de l'ADN
    [Franklin], téléphone, radio, ampoule…).
  * découverte/théorie -> UN auteur principal = fonctionnel. Clés = libellés FR minuscules.

Usage : python3 ingere_sciences.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_DECOUVERTES = [
    ("gravitation universelle", "Isaac Newton"),
    ("lois du mouvement", "Isaac Newton"),
    ("relativité", "Albert Einstein"),
    ("théorie de l'évolution", "Charles Darwin"),
    ("tableau périodique", "Dmitri Mendeleïev"),
    ("pénicilline", "Alexander Fleming"),
    ("radioactivité", "Henri Becquerel"),
    ("loi de la chute des corps", "Galilée"),
    ("héliocentrisme", "Nicolas Copernic"),
    ("lois de l'hérédité", "Gregor Mendel"),
    ("vaccination", "Edward Jenner"),
    ("pasteurisation", "Louis Pasteur"),
    ("théorie des quanta", "Max Planck"),
    ("principe d'archimède", "Archimède"),
    ("psychanalyse", "Sigmund Freud"),
    ("électron", "Joseph John Thomson"),
    ("noyau atomique", "Ernest Rutherford"),
    ("expansion de l'univers", "Edwin Hubble"),
    ("conduction supraconductrice", "Heike Kamerlingh Onnes"),
    ("loi de la dilatation des gaz", "Joseph Louis Gay-Lussac"),
    ("polonium", "Marie Curie"),
    ("radium", "Marie Curie"),
    ("électromagnétisme (équations)", "James Clerk Maxwell"),
    ("induction électromagnétique", "Michael Faraday"),
]

SRC = "histoire des sciences de référence (découverte/théorie -> auteur) — attributions consensuelles"


def ingere():
    print(f"== SCIENCES — découverte -> auteur ({len(_DECOUVERTES)}) ==")
    publie("auteur_decouverte", "convention", SRC, _DECOUVERTES)


if __name__ == "__main__":
    ingere()
