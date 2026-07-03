# -*- coding: utf-8 -*-
"""VALIDE les capacités OUTILS câblées au chat (audit orphelines 2026-07-03) : grammaire, conjugaison, graphique,
distance, invention, audit de code. FAUX=0 : chaque handler répond dans son périmètre et s'abstient (None)
hors périmètre — jamais de réponse inventée, jamais de détournement d'une question normale.

Léger : on teste les handlers de repond.py directement. Les handlers LOURDS (distance/invention/audit) sont
vérifiés surtout pour leur SÛRETÉ de routage (None sur entrée non concernée) ; leur chemin complet est couvert
e2e par ailleurs."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import repond as R

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — GRAMMAIRE —
r = R._cap_grammaire("quelle est la nature du mot chat ?")
check(r and "nom" in r, "grammaire : nature de 'chat' -> nom")
r = R._cap_grammaire("nature grammaticale de rapidement")
check(r and "adverbe" in r, "grammaire : 'rapidement' -> adverbe")
r = R._cap_grammaire("analyse grammaticale : le chien dort")
check(r and "Type" in r, "grammaire : analyse de phrase")
check(R._cap_grammaire("quelle est la capitale de la France ?") is None, "grammaire : ne capte PAS une question factuelle")
r = R._cap_grammaire("nature du mot xyzqwerty")
check(r and ("pas certain" in r or "deviner" in r), "grammaire : mot inconnu -> abstention honnête")

# — CONJUGAISON —
r = R._cap_conjugaison("conjugue le verbe parler")
check(r and "parlons" in r and "parlent" in r, "conjugaison : parler au présent")
r = R._cap_conjugaison("conjugaison de finir")
check(r and "finissons" in r, "conjugaison : finir")
r = R._cap_conjugaison("conjugue manger")
check(r and ("abst" in r.lower() or "périmètre" in r or "perimetre" in r), "conjugaison : verbe hors périmètre -> abstention honnête")
check(R._cap_conjugaison("quelle heure est-il ?") is None, "conjugaison : ne capte pas une question quelconque")

# — GRAPHIQUE —
r = R._cap_graphique("trace un graphique en barres de 3, 5, 8, 2")
check(r and r.startswith("<svg"), "graphique : barres -> SVG")
r = R._cap_graphique("trace la courbe de 1, 4, 9, 16")
check(r and r.startswith("<svg"), "graphique : courbe -> SVG")
check(R._cap_graphique("trace de la route") is None, "graphique : pas de nombres -> None")
check(R._cap_graphique("quelle est la population du Japon ?") is None, "graphique : question sans intention graphique -> None")

# — INVENTION (léger : besoin.py) —
r = R._cap_invention("comment rafraîchir une pièce sans climatiseur ?")
check(r and ("BESOIN" in r or "but réel" in r or "but reel" in r.lower()), "invention : reformulation physique du besoin")
check(R._cap_invention("quelle est la capitale de l'Italie ?") is None, "invention : ne capte pas une question factuelle")
check(R._cap_invention("comment dire bonjour sans accent ?") is None, "invention : besoin hors catalogue physique -> None (pipeline continue)")

# — AUDIT CODE : sûreté de routage (None hors périmètre) —
check(R._cap_audit_code("bonjour comment vas-tu ?") is None, "audit code : message normal -> None")
check(R._cap_audit_code("parle-moi du code de la route") is None, "audit code : 'code' sans bloc -> None")

# — DISTANCE : sûreté de routage —
check(R._cap_distance("bonjour") is None, "distance : message normal -> None")

print("=== valide_capacites_chat : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
