# -*- coding: utf-8 -*-
"""VALIDE cinematique_nl (audit item 7 : problèmes à étapes du mouvement uniforme). FAUX=0 : temps/points
EXACTS (Fraction), dérivation montrée, motifs FERMÉS (distance + 2 vitesses + mot-clé), zéro capture."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import cinematique_nl as C

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — RENCONTRE (le problème canonique de l'audit) —
r = C.resout("deux trains distants de 300 km partent l'un vers l'autre à 80 et 70 km/h : quand se croisent-ils ?")
check(r is not None and "2 h" in r and "150" in r and "160 km du premier" in r and "140 km du second" in r,
      "trains 300/80/70 -> 2 h + points de croisement exacts + dérivation (80+70=150)")
r = C.resout("Deux trains séparés de 450 km roulent l'un vers l'autre à 100 km/h et 80 km/h. Où se rencontrent-ils ?")
check(r is not None and "2 h 30 min" in r and "250 km" in r, "450/100/80 -> 2 h 30 exactes (12/5 h, jamais 2.4999)")
r = C.resout("deux voitures partent l'un vers l'autre à 60 et 40 km/h, distance 150 km, quand se croisent-elles ?")
check(r is not None and "1 h 30 min" in r, "ordre inverse (vitesses avant distance) parsé aussi")

# — POURSUITE —
r = C.resout("un cycliste a une avance de 15 km ; il roule à 20 et l'autre à 30 km/h : quand le rattrape-t-il ?")
check(r is not None and "1 h 30 min" in r and "30 − 20" in r, "poursuite : 15 km d'écart, 30 vs 20 -> 1 h 30")
r = C.resout("écart de 10 km, ils roulent à 25 et 25 km/h — le second rattrape-t-il le premier ?")
check(r is not None and "jamais" in r, "vitesses ÉGALES -> « ne le rattrape pas » (jamais un temps infini/negatif)")

# — ZÉRO capture (FAUX=0) —
for t in ("quand le train de 14h37 arrive-t-il ?",
          "les deux trains se croisent où ?",                       # aucune donnée chiffrée
          "deux trains partent l'un vers l'autre à 80 et 70 km/h",   # pas de distance
          "à quelle heure les trains partent-ils ?",
          "pourquoi les trains se croisent-ils la nuit ?"):
    check(C.resout(t) is None, "piège : %r -> None" % t[:50])

# — câblage chat (cap) —
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
import repond as R
r = R._cap_cinematique("deux trains distants de 300 km partent l'un vers l'autre à 80 et 70 km/h : quand se croisent-ils ?")
check(r is not None and "2 h" in r, "cap chat câblé -> même réponse exacte")
check(R._cap_cinematique("j'aime les trains") is None, "cap chat : hors périmètre -> None")

print("=== valide_cinematique_nl : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
