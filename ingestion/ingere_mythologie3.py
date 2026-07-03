"""
INGESTION MYTHOLOGIE HINDOUE — ajoute les dieux hindous à `domaine_dieu` + `pantheon_dieu`  (OFFLINE).

⚠️ `publie` RÉÉCRIT le fichier -> on REPUBLIE la table COMPLÈTE (grecs+égyptiens+nordiques importés des
scripts précédents + hindous ajoutés). C'est le point délicat (cf. piège lot 8). Source : mythologies de
référence, attributions/panthéons canoniques. FAUX=0 : aucun nom hindou ne collisionne avec l'existant.

Usage : python3 ingere_mythologie3.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie
from ingere_mythologie import _DIEUX as _GRECS_FULL          # (grec, domaine, romain)
from ingere_mythologie2 import _EGYPTIENS, _NORDIQUES, _GRECS, _ROMAINS

# (dieu hindou, domaine principal)
_HINDOUS = [
    ("brahma", "création"),
    ("vishnou", "préservation du monde"),
    ("shiva", "destruction et transformation"),
    ("ganesh", "sagesse et obstacles"),
    ("lakshmi", "fortune et prospérité"),
    ("saraswati", "savoir et arts"),
    ("indra", "ciel et foudre"),
    ("agni", "feu"),
    ("surya", "soleil"),
    ("yama", "mort"),
    ("vayu", "vent"),
    ("kali", "destruction et temps"),
]


def ingere():
    print("== MYTHOLOGIE HINDOUE — ajout à domaine_dieu + pantheon_dieu (republication complète) ==")
    grecs_dom = [(d, dom) for d, dom, _ in _GRECS_FULL]
    domaine = grecs_dom + _EGYPTIENS + _NORDIQUES + _HINDOUS
    publie("domaine_dieu", "convention",
           "mythologie de référence (grecque/égyptienne/nordique/hindoue) — attributions canoniques", domaine)

    pantheon = ([(d, "grec") for d in _GRECS] + [(d, "romain") for d in _ROMAINS]
                + [(d, "égyptien") for d, _ in _EGYPTIENS] + [(d, "nordique") for d, _ in _NORDIQUES]
                + [(d, "hindou") for d, _ in _HINDOUS])
    publie("pantheon_dieu", "convention", "mythologie de référence (dieu -> panthéon)", pantheon)


if __name__ == "__main__":
    ingere()
