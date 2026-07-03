# -*- coding: utf-8 -*-
"""VALIDE le raisonnement COMPOSITIONNEL « X de Y de Z » (P1), FAUX=0.

On MOCKE le résolveur factuel (ia.donnee_nl) avec des faits contrôlés pour prouver le MÉCANISME indépendamment
des données : l'inner (Y de Z) est résolu en entité E, puis l'outer (X de E). Chaque maillon = lookup vérifié ;
si un maillon manque -> abstention (None), jamais une composition inventée."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import repond

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — faits contrôlés (base à 2 sauts) —
class _Fait:
    def __init__(self, v):
        self.valeur = v


_FAITS = {
    "capitale de france": "Paris",
    "population de paris": "2 100 000",
    "pays de paris": "France",
    "continent de france": "Europe",
    "monnaie de france": "euro",
}


class _MockIA:
    def donnee_nl(self, requete):
        import base_faits
        v = _FAITS.get(" ".join(requete.strip().lower().split()))
        return (base_faits.VERIFIE, _Fait(v)) if v else (base_faits.HORS, None)


# injecte le mock dans le cache d'ia de repond
import base_faits
repond._IA = _MockIA()
repond._VERIFIE = base_faits.VERIFIE
repond._ATTR_HEADS_CACHE = {"capitale", "population", "pays", "continent", "monnaie", "langue"}

# (1) composition à 2 sauts qui résout
r = repond._compose_relations("quelle est la population de la capitale de la France ?")
check(r is not None and r.startswith("2 100 000"), "population de la capitale de la France -> composée (2 100 000)")
check(r is not None and "capitale de France = Paris" in r, "la chaîne de dérivation est montrée")

r = repond._compose_relations("quel est le continent du pays de Paris ?")
check(r is not None and r.startswith("Europe"), "continent du pays de Paris -> Europe (composée)")

r = repond._compose_relations("quelle est la monnaie du pays de Paris ?")
check(r is not None and r.startswith("euro"), "monnaie du pays de Paris -> euro (composée)")

# (2) FAUX=0 : un maillon INCONNU -> abstention (None), jamais une invention
check(repond._compose_relations("quelle est la superficie de la capitale de la France ?") is None,
      "maillon outer manquant (superficie de Paris) -> None (abstention)")
check(repond._compose_relations("quelle est la population de la capitale de l'Atlantide ?") is None,
      "maillon inner manquant (capitale d'Atlantide) -> None")

# (3) détection : une question imbriquée est reconnue, une simple ne l'est pas
check(repond._est_relation_imbriquee("population de la capitale de la France"), "détecte l'imbrication")
check(not repond._est_relation_imbriquee("capitale de la France"), "une relation simple n'est PAS imbriquée")

# (4) non-imbriqué -> le composeur ne s'applique pas
check(repond._compose_relations("quelle est la capitale de la France ?") is None, "simple -> composeur inactif (None)")

print("=== valide_composition : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
