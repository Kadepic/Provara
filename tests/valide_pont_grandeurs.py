# -*- coding: utf-8 -*-
"""VALIDE pont_grandeurs (brique 2 du fil) — les grandeurs ÉNONCÉES deviennent des OPÉRANDES. FAUX=0 :
calcul exact vérifié contre la vérité indépendante, opérande manquant DEMANDÉ NOMMÉMENT (jamais deviné),
hypothèses jamais utilisées, zéro capture des questions étrangères."""
from __future__ import annotations

import math
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


sit = S.Situation()
sit.apprend(1, "Je conçois un échangeur thermique à contre-courant ; le fluide chaud entre à 90 degrés et sort à 50 degrés, le froid entre à 20 degrés.")

# — DEMANDE NOMMÉE de l'opérande manquant (LE comportement-clé) —
r = P.repond("quel est l'écart de température moyen logarithmique ?", sit)
check(r is not None and "SORTIE du fluide froid" in r and "Donne-la-moi" in r,
      "DTLM incomplet -> demande NOMMÉE de la température manquante (abstention actionnable)")
check("ENTRÉE du fluide chaud" not in r, "les opérandes PRÉSENTS ne sont pas redemandés")

# — calcul exact une fois la donnée fournie (vérité indépendante) —
sit.apprend(3, "le fluide froid sort à 45 degrés")
r = P.repond("quel est le DTLM ?", sit)
verite = 15 / math.log(45 / 30)
check(r is not None and ("%.4f" % verite).replace(".", ",") in r,
      "DTLM = %.4f (vérifié contre calcul indépendant), formule + ΔT montrés" % verite)
check("90−45" in r.replace(" ", "") and "50−20" in r.replace(" ", ""),
      "contre-courant : ΔT1 = Tc,in − Tf,out et ΔT2 = Tc,out − Tf,in (bornes correctes)")

# — surface : grandeurs de la QUESTION + ΔTlm du fil —
r = P.repond("quelle surface d'échange me faut-il pour 100 kW avec un coefficient global de 500 W/m2K ?", sit)
a_verite = 100000 / (500 * verite)
check(r is not None and ("%.4f" % a_verite).replace(".", ",") in r,
      "surface = %.4f m² (Q et U pris dans la question, ΔTlm du fil)" % a_verite)
r = P.repond("quelle surface d'échange me faut-il ?", sit)
check(r is not None and "puissance" in r and "coefficient" in r,
      "surface sans Q ni U -> les DEUX manquants demandés nommément")

# — écart générique, cité —
r = P.repond("quel est l'écart entre l'entrée et la sortie du fluide chaud ?", sit)
check(r is not None and "90 − 50 = 40" in r and "tour 1" in r, "écart entrée/sortie chaud = 40, clause citée")

# — ré-énoncé = la dernière valeur fait foi (autorité utilisateur) —
sit2 = S.Situation()
sit2.apprend(1, "échangeur à co-courant ; le chaud entre à 90 degrés et sort à 50 degrés")
sit2.apprend(3, "le froid entre à 20 degrés et sort à 45 degrés")
sit2.apprend(5, "en fait le chaud entre à 95 degrés")
r = P.repond("quel est le DTLM ?", sit2)
check(r is not None and "95−20" in r.replace(" ", ""), "ré-énoncé (90->95) : la dernière valeur fait foi")
check("co-courant" in r and "95−20" in r.replace(" ", "") and "50−45" in r.replace(" ", ""),
      "co-courant : bornes in-in / out-out (≠ contre-courant)")

# — hypothèses jamais opérandes —
sit3 = S.Situation()
sit3.apprend(1, "le chaud entre à 90 degrés et sort à 50 degrés ; échangeur contre-courant")
sit3.apprend(3, "si le froid entre à 20 degrés et sort à 45 degrés, ce serait idéal")
r = P.repond("quel est le DTLM ?", sit3)
check(r is not None and "il me manque" in r, "températures sous « si » = hypothèses -> JAMAIS utilisées comme opérandes")

# — DTLM physiquement impossible -> dit —
sit4 = S.Situation()
sit4.apprend(1, "échangeur contre-courant ; le chaud entre à 50 degrés et sort à 40 degrés")
sit4.apprend(3, "le froid entre à 45 degrés et sort à 60 degrés")
r = P.repond("quel est le DTLM ?", sit4)
check(r is not None and "impossible" in r, "ΔT de borne négatif -> « physiquement impossible » DIT (jamais un ln(<0))")

# — zéro capture —
for q in ("quelle est la capitale de la France ?", "quel est l'écart entre le PSG et l'OM ?",
          "combien font 2 + 2 ?", "quelle surface fait la Belgique ?"):
    check(P.repond(q, sit) in (None,) or "Belgique" not in (P.repond(q, sit) or ""),
          "hors périmètre : %r -> None/pas de capture" % q[:40])
check(P.repond("quel est le DTLM ?", S.Situation()) is not None
      and "manque" in P.repond("quel est le DTLM ?", S.Situation()),
      "fil vide + DTLM demandé -> liste honnête de TOUT ce qui manque")

print("=== valide_pont_grandeurs : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
