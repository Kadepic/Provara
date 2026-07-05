# -*- coding: utf-8 -*-
"""BANC SYNONYMES FAMILIERS — un mot familier/argotique (bagnole, toubib, fric…) est COMPRIS via le réseau
JeuxDeMots embarqué (module `synonymes`) : définition, is-a, chaînage. FAUX=0 : la réponse reste un fait vérifié
et la reformulation est SIGNALÉE (« bagnole → voiture »). Ce banc verrouille une fonctionnalité vitrine.

Usage : LECTEUR_DATASETS_DIR=… python3 tests/banc_synonymes.py   (base complète ou échantillon)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import repond as R          # noqa: E402
import conversation         # noqa: E402

# (question avec mot familier, extrait attendu dans la réponse — insensible à la casse).
CAS = [
    ("qu'est-ce qu'une bagnole ?", "voiture"),
    ("une bagnole c'est quoi ?", "voiture"),
    ("un toubib c'est quoi ?", "médecin"),
    ("c'est quoi un toubib ?", "médecin"),
    ("le fric c'est quoi ?", "argent"),
    ("une bagnole est-elle une voiture ?", "oui"),
    ("une bagnole est-elle un véhicule ?", "véhicule"),   # chaînage bagnole -> voiture -> véhicule (seed)
    ("une voiture est-elle un véhicule ?", "véhicule"),
]


def run():
    mem = conversation.MemoireConversation(racine=None)
    ok, echecs = 0, []
    for i, (q, attendu) in enumerate(CAS):
        try:
            rep = R.repond(mem, "syn-%d" % i, q, pleine=True) or ""
        except Exception as e:
            rep = "EXCEPTION %r" % e
        if attendu.lower() in rep.lower():
            ok += 1
        else:
            echecs.append((q, rep.replace("\n", " ")[:80]))
    print("\nSYNONYMES FAMILIERS COMPRIS : %d/%d" % (ok, len(CAS)))
    if echecs:
        print("ÉCHECS :")
        for q, rep in echecs:
            print("  ✗ %s\n      -> %s" % (q, rep))
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(run())
