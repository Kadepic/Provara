# -*- coding: utf-8 -*-
"""VALIDE apprentissage_patrons : apprendre les reformulations, FAUX=0.

On vérifie : apprentissage SEULEMENT si sujet partagé, ré-aiguillage correct, refus d'apprendre des paires sans
rapport (pas d'alias hasardeux), effacement (RGPD)."""
from __future__ import annotations

import os
import sys
import tempfile

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

os.environ["VERAX_PATRONS_DIR"] = tempfile.mkdtemp(prefix="verax_patrons_")

import apprentissage_patrons as A
A.oublie(None)   # part d'un état propre

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# (1) apprend quand SUJET PARTAGÉ
check(A.enregistre("c'est quoi le chef-lieu de la France ?", "quelle est la capitale de la France ?"),
      "apprend l'alias (sujet partagé « france »)")
check(A.alias("c'est quoi le chef-lieu de la France ?") == "quelle est la capitale de la France ?",
      "alias retrouvé")
check(A.nombre_appris() == 1, "1 alias appris")

# (2) N'APPREND PAS sans sujet partagé (pas d'alias hasardeux)
check(not A.enregistre("raconte-moi une blague", "quelle est la capitale du Japon ?"),
      "refuse d'apprendre sans sujet partagé")
check(A.alias("raconte-moi une blague") is None, "pas d'alias hasardeux")

# (3) N'APPREND PAS une paire identique
check(not A.enregistre("capitale de la France", "capitale de la France"), "refuse l'alias identique")

# (4) alias insensible à la casse/accents (normalise)
check(A.alias("C'EST QUOI LE CHEF-LIEU DE LA FRANCE ?") == "quelle est la capitale de la France ?",
      "alias insensible casse/accents")

# (5) persistance : recharger depuis le disque
A._CACHE = None
check(A.alias("c'est quoi le chef-lieu de la France ?") == "quelle est la capitale de la France ?",
      "alias persistant (relu du disque)")

# (6) effacement ciblé + global (RGPD)
A.enregistre("population de l'hexagone", "population de la France")
check(A.oublie("population de l'hexagone") == 1, "efface un alias ciblé")
check(A.alias("population de l'hexagone") is None, "alias ciblé effacé")
n = A.oublie(None)
check(n >= 1 and A.nombre_appris() == 0, "efface TOUT (RGPD)")

print("=== valide_apprentissage_patrons : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
