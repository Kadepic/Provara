# -*- coding: utf-8 -*-
"""VALIDE la TRADUCTION mot-à-mot assistée (P5), FAUX=0. Teste le repli DICTIONNAIRE CURÉ hors-ligne (la source
riche concept_du_mot exige la base complète, testée sur le .exe). Un mot inconnu est gardé tel quel + signalé,
jamais inventé."""
from __future__ import annotations
import os, sys
os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))
import traduction as T

ok = ko = 0
def check(c, label):
    global ok, ko
    if c: ok += 1
    else:
        ko += 1; print("  FAIL: " + label)

# FR -> EN
for src, att in [("le chat dort", "The cat sleeps"), ("la femme mange le pain", "The woman eats the bread"),
                 ("nous voulons voir le monde", "We want to see the world"), ("bonjour", "Hello")]:
    tr, _ = T.traduit(src, "en")
    check(tr == att, "FR->EN « %s » -> « %s » (obtenu « %s »)" % (src, att, tr))

# EN -> FR (noyau curé)
for src, att in [("the cat sleeps", "Le chat dort"), ("the dog", "Le chien")]:
    tr, _ = T.traduit(src, "fr")
    check(tr == att, "EN->FR « %s » -> « %s » (obtenu « %s »)" % (src, att, tr))

# FAUX=0 : mot inconnu gardé + signalé, jamais inventé
tr, inc = T.traduit("le xyzzq dort", "en")
check("xyzzq" in tr and "xyzzq" in inc, "mot inconnu gardé tel quel + signalé")

# ne traduit pas un mot en une lettre inventée
tr, inc = T.traduit("chat", "en")
check(tr.lower() == "cat", "mot simple chat -> cat")

print("=== valide_traduction : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
