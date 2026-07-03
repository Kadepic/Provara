# -*- coding: utf-8 -*-
"""VALIDE explications : explications de concepts/paradoxes du Palier 2, FAUX=0.

Vérifie que les concepts connus sont expliqués (contenu de la brique, non inventé) et qu'une question factuelle
ou un concept inconnu -> None (pas de détournement)."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import explications as E

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


cas = [
    ("explique le paradoxe des deux enveloppes", "deux enveloppes"),
    ("qu'est-ce que le paradoxe de Braess ?", "braess"),
    ("parle-moi du paradoxe d'Allais", "allais"),
    ("explique le paradoxe d'Ellsberg", "ellsberg"),
    ("c'est quoi le sophisme des coûts irrécupérables ?", "coûts"),
    ("explique le critère de Kelly", "kelly"),
    ("explique le paradoxe de Saint-Pétersbourg", "pétersbourg"),
    ("qu'est-ce que le paradoxe de Parrondo ?", "parrondo"),
]
for q, cle in cas:
    r = E.explique(q)
    check(r is not None and cle.split()[0][:4].lower() in r.lower(), "explique « %s »" % cle)

# NON détourné : question factuelle, salutation, concept inconnu
for q in ["quelle est la capitale de la France ?", "bonjour comment vas-tu ?",
          "explique-moi la photosynthèse", "explique le paradoxe de Zzzz"]:
    check(E.explique(q) is None, "ne détourne pas « %s »" % q)

# une explication a bien du CONTENU chiffré de la brique (pas une paraphrase creuse)
r = E.explique("explique le paradoxe de Braess")
check(r and any(c.isdigit() for c in r), "l'explication porte le calcul réel de la brique")

print("=== valide_explications : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
