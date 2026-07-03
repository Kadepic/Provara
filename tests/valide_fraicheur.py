# -*- coding: utf-8 -*-
"""VALIDE la route de FRAÎCHEUR (P3) : une question VOLATILE est reconnue pour préférer la source LIVE à la base
statique (qui peut être périmée). On teste le DÉTECTEUR (la route live exige le réseau, hors gate) : FAUX=0
inchangé (la source live reste vérifiée + attribuée ; repli base si indisponible)."""
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


for q in ["qui est le président actuel de la France ?",
          "quel est le dernier vainqueur du Tour de France ?",
          "quelle est la population en 2026 ?",
          "qui dirige actuellement l'entreprise ?",
          "quel est le classement récent ?",
          "who is the current CEO ?"]:
    check(repond._est_volatil(q), "volatil détecté : " + q)

for q in ["quelle est la capitale de la France ?",
          "qui a peint la Joconde ?",
          "quelle est la masse de l'électron ?",
          "quel est le numéro atomique du fer ?"]:
    check(not repond._est_volatil(q), "stable (non volatil) : " + q)

print("=== valide_fraicheur : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
