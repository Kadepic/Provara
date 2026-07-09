# -*- coding: utf-8 -*-
"""VALIDE le pont ÉLECTRIQUE (②bis : généralisation hors-thermo, 2026-07-09 nuit) — la roue U = R·I / P = U·I
fermée depuis les grandeurs ÉNONCÉES. FAUX=0 : valeurs vérifiées contre calcul indépendant, dérivation MONTRÉE,
opérande manquant DEMANDÉ NOMMÉMENT, hypothèses jamais opérandes, zéro capture hors contexte électrique."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import situation as S
import pont_grandeurs as P

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — U et I énoncés -> P et R fermés, dérivation montrée —
sit = S.Situation()
sit.apprend(1, "le circuit est alimenté en 230 volts et le moteur tire 10 ampères")
r = P.repond("quelle est la puissance consommée ?", sit)
check(r is not None and "2 300" not in r and "2300 W" in r and "P = U×I" in r,
      "U=230, I=10 -> P = 2300 W, chemin P = U×I montré")
r = P.repond("quelle est la résistance du circuit ?", sit)
check(r is not None and "23 Ω" in r and "R = U/I" in r, "R = U/I = 23 Ω")

# — 2 autres paires : (P, U) -> I ; (R, I) -> U —
sit2 = S.Situation()
sit2.apprend(1, "la plaque fait 2 kv et consomme 4000 watts")
r = P.repond("quel courant ?", sit2)
check(r is not None and "2 A" in r and "I = P/U" in r, "P=4000 W, U=2 kV -> I = 2 A (kV converti)")
sit3 = S.Situation()
sit3.apprend(1, "la résistance est de 50 ohms et le courant de 3 ampères")
r = P.repond("quelle tension ?", sit3)
check(r is not None and "150 V" in r and "U = R×I" in r, "R=50 Ω, I=3 A -> U = 150 V")

# — dernière valeur fait foi (autorité utilisateur) —
sit.apprend(3, "en fait le moteur tire 5 ampères")
r = P.repond("quelle puissance ?", sit)
check(r is not None and "1150 W" in r, "ré-énoncé 10->5 A : P recalculée = 1150 W")

# — opérande manquant -> demandé NOMMÉMENT —
sit4 = S.Situation()
sit4.apprend(1, "l'alimentation délivre 12 volts")
r = P.repond("quelle puissance ?", sit4)
check(r is not None and "il me manque" in r and ("ampères" in r or "ohms" in r),
      "U seule -> le courant ou la résistance demandés nommément")

# — hypothèse jamais opérande —
sit5 = S.Situation()
sit5.apprend(1, "le circuit est en 24 volts")
sit5.apprend(3, "si le courant montait à 2 ampères, ce serait bien")
r = P.repond("quelle puissance ?", sit5)
check(r is not None and "il me manque" in r, "courant sous « si » = hypothèse -> jamais un opérande")

# — ET-SI électrique : simulation avant, avant/après —
r = P.repond("et si le moteur tirait 20 ampères, quelle puissance ?", sit)
check(r is not None and "4600 W" in r and "au lieu de 1150" in r and "inchangé" in r,
      "et-si I=20 A -> P = 4600 W au lieu de 1150, fil réel inchangé")
r2 = P.repond("quelle puissance ?", sit)
check(r2 is not None and "1150 W" in r2, "le fil réel est intact après l'et-si électrique")

# — zéro capture hors contexte électrique —
sit6 = S.Situation()
sit6.apprend(1, "le fluide chaud entre à 90 degrés et sort à 50 degrés")
for q in ("quelle puissance passe dans l'échangeur ?", "quelle est la résistance de la France ?",
          "quelle tension entre Paris et Berlin ?"):
    check(P.repond(q, sit6) is None, "sans grandeur électrique : %r -> None" % q[:45])
check(P._electrique("quelle intensité ?", S.Situation()) is None, "fil vide -> None (pas d'ancrage)")

# — « pourquoi ? » nu sur une réponse électrique -> la roue expliquée (loi d'Ohm + P = U·I) —
rd = P.repond("quelle est la résistance du circuit ?", sit)
r = P.pourquoi_dernier("pourquoi ?", rd, sit)
check(r is not None and "loi d'Ohm" in r and "P = U·I" in r,
      "pourquoi ? nu sur une réponse électrique -> les deux définitions de la roue expliquées")

print("=== valide_pont_electrique : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
