# -*- coding: utf-8 -*-
"""VALIDE le GRAPHE DES ROUES (étape ③ — graine du gap-engine v2). FAUX=0 : le graphe REFLÈTE les roues
réellement câblées (source unique _ROUES) ; chemins PROUVÉS de bout en bout ; gap = NOMMÉ, jamais comblé en
silence ; grandeur inconnue = dit + inventaire honnête."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import situation as S
import pont_grandeurs as P
import graphe_roues as G

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — structure : le graphe reflète les roues ; connexité mesurée, pas déclarée —
idx = G.grandeurs()
check(len(G.roues()) == len(P._ROUES) and len(idx) >= 25,
      "le graphe reflète _ROUES (%d roues, %d grandeurs)" % (len(G.roues()), len(idx)))
comps = G.composantes()
check(len(comps) == 1, "TOUTES les roues se relient (1 composante) — mesuré : %d îlot(s)" % len(comps))
check(G.gaps() == [], "graphe connexe -> zéro gap structurel (aujourd'hui)")

# — chemins : direct, multi-roues, réflexif —
ch = G.chemins("tension", "puissance")
check(ch is not None and ch != "?" and len(ch) == 1 and ch[0][0] == "électrique",
      "tension -> puissance : 1 roue (électrique)")
ch = G.chemins("section", "consommation")
check(ch is not None and ch != "?" and 2 <= len(ch) <= 4,
      "section -> consommation : chemin multi-roues trouvé (%s)" % (ch and [e[0] for e in ch]))
check(G.chemins("température", "masse") == "?", "grandeur hors graphe -> « ? » (jamais un faux chemin)")

# — gap PROUVÉ par isolation : élec + hydro seules = 2 îlots, le pont manquant est NOMMÉ —
sub = [P._ROUE_ELEC, P._ROUE_HYDRO]
check(len(G.composantes(sub)) == 2 and len(G.gaps(sub)) == 1,
      "isolation élec/hydro : 2 îlots, 1 gap NOMMÉ (%s)" % G.gaps(sub))
check(G.chemins("tension", "débit", sub) is None, "aucun pont élec->hydro dans le sous-ensemble -> None")

# — capacité NL « comment relier X et Y ? » —
r = P.repond("comment relier la section et la consommation ?", S.Situation())
check(r is not None and "hydraulique" in r and "consommation carburant" in r and "étape" in r,
      "NL : chemin narratif avec les roues traversées")
r = P.repond("comment relier la masse et la température ?", S.Situation())
check(r is not None and "Aucune de mes roues" in r and "température" in r,
      "NL : grandeur inconnue -> dit + inventaire (jamais un faux pont)")
check(P.repond("comment vas-tu ?", S.Situation()) is None, "zéro capture du social")

print("=== valide_graphe_roues : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
