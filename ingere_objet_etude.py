"""
INGESTION SCIENCES — discipline (« -logie/-graphie ») -> objet d'étude  (OFFLINE).

SOURCE : définitions de référence des disciplines. Faits STABLES et CERTAINS (objet d'étude par définition).

FAUX=0 — discipline : UNIQUEMENT les disciplines à objet d'étude UNIVOQUE (défini par l'étymologie/usage
établi). On ÉCARTE les disciplines à périmètre discuté. discipline -> UN objet = fonctionnel.
Clés = noms FR minuscules.

Usage : python3 ingere_objet_etude.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_OBJETS = [
    # médecine (spécialités à organe univoque)
    ("cardiologie", "le cœur"),
    ("neurologie", "le système nerveux"),
    ("dermatologie", "la peau"),
    ("pneumologie", "les poumons"),
    ("hépatologie", "le foie"),
    ("néphrologie", "les reins"),
    ("ophtalmologie", "les yeux"),
    ("hématologie", "le sang"),
    ("ostéologie", "les os"),
    ("myologie", "les muscles"),
    # sciences du vivant
    ("zoologie", "les animaux"),
    ("botanique", "les plantes"),
    ("entomologie", "les insectes"),
    ("ornithologie", "les oiseaux"),
    ("ichtyologie", "les poissons"),
    ("herpétologie", "les reptiles"),
    ("mycologie", "les champignons"),
    ("bactériologie", "les bactéries"),
    ("virologie", "les virus"),
    ("cytologie", "les cellules"),
    ("histologie", "les tissus"),
    # sciences de la Terre et de l'univers
    ("géologie", "les roches et la Terre"),
    ("sismologie", "les séismes"),
    ("volcanologie", "les volcans"),
    ("météorologie", "l'atmosphère et le temps"),
    ("hydrologie", "l'eau"),
    ("océanographie", "les océans"),
    ("astronomie", "les astres"),
    ("cosmologie", "l'univers"),
    # sciences humaines / autres
    ("sociologie", "la société"),
    ("psychologie", "le psychisme"),
    ("archéologie", "les vestiges anciens"),
    ("paléontologie", "les fossiles"),
    ("étymologie", "l'origine des mots"),
    ("graphologie", "l'écriture manuscrite"),
    ("musicologie", "la musique"),
]

SRC = "définitions de référence des disciplines (objet d'étude) — univoque"


def ingere():
    print(f"== DISCIPLINES — objet d'étude ({len(_OBJETS)}) ==")
    publie("objet_etude", "convention", SRC, _OBJETS)


if __name__ == "__main__":
    ingere()
