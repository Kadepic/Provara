# -*- coding: utf-8 -*-
"""VALIDE la roue ÉNERGIE E = P·t (3e instance du moteur de roues, 2026-07-09 jour) + le PONT INTER-ROUES
(puissance non énoncée -> fermée par la roue électrique P = U·I, chemins concaténés, jamais montrée comme
« donnée »). FAUX=0 : supposition « à puissance constante » DITE sur chaque réponse ; « h » nu jamais une
durée ; une durée seule n'ancre rien ; hypothèses jamais opérandes ; q± prouvé 2 points."""
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


# — P et t énoncés -> E, supposition DITE —
sit = S.Situation()
sit.apprend(1, "le radiateur consomme 2000 watts")
sit.apprend(3, "il tourne pendant 3 heures")
r = P.repond("quelle énergie consommée ?", sit)
check(r is not None and "6 kWh" in r and "E = P×t" in r and "puissance constante" in r,
      "P=2000 W, t=3 h -> E = 6 kWh, chemin E = P×t, supposition « puissance constante » DITE")

# — PONT INTER-ROUES : U/I énoncés (pas P) -> P = U×I puis E = P×t ; U/I jamais « donnés » de cette roue —
sit2 = S.Situation()
sit2.apprend(1, "la plaque est en 230 volts et tire 10 ampères")
sit2.apprend(3, "elle chauffe pendant 2 heures")
r = P.repond("quelle énergie ?", sit2)
check(r is not None and "4,6 kWh" in r and "P = U×I" in r and "E = P×t" in r,
      "pont élec->énergie : 230 V × 10 A pendant 2 h -> 4,6 kWh, dérivation P = U×I ; E = P×t montrée")
check(r is not None and "donné : durée = 2 h" in r,
      "le P ponté n'est JAMAIS montré comme « donné » (seule la durée est une énoncée de cette roue)")

# — ET-SI PONTÉ (bug e2e n4 2026-07-09 : la question et-si partait en réponse PLATE sans cadre hypothèse) —
r = P.repond("et si elle chauffait pendant 4 heures, quelle énergie ?", sit2)
check(r is not None and "Dans ton hypothèse" in r and "9,2 kWh" in r and "au lieu de 4,6" in r,
      "et-si PONTÉ (fil U/I sans P) : cadré hypothèse, 9,2 au lieu de 4,6 kWh, pont dans les chemins")
check(r is not None and "P = U×I" in r, "le chemin du pont amont est montré dans l'et-si")

# — conversions : minutes -> heures ; consommation = alias —
sit3 = S.Situation()
sit3.apprend(1, "le four fait 2000 w et cuit pendant 30 minutes")
r = P.repond("quelle consommation ?", sit3)
check(r is not None and "1 kWh" in r, "2000 W × 30 min -> 1 kWh (conversion minutes, alias consommation)")

# — durée dans la QUESTION —
sit4 = S.Situation()
sit4.apprend(1, "l'appareil tire 500 watts")
r = P.repond("quelle énergie consommée en 4 heures ?", sit4)
check(r is not None and "2 kWh" in r, "durée dans la question : 500 W × 4 h -> 2 kWh")

# — manquant demandé NOMMÉMENT —
sit5 = S.Situation()
sit5.apprend(1, "la pompe tourne pendant 5 heures")
r = P.repond("quelle énergie ?", sit5)
check(r is not None and "il me manque" in r and "watts" in r,
      "durée seule + question énergie -> la puissance demandée nommément")

# — hypothèse jamais opérande —
sit6 = S.Situation()
sit6.apprend(1, "le radiateur consomme 2000 watts")
sit6.apprend(3, "si ça tournait 5 heures, ce serait long")
r = P.repond("quelle énergie consommée ?", sit6)
check(r is not None and "il me manque" in r, "durée sous « si » = hypothèse -> jamais un opérande")

# — zéro capture : durée seule, fil vide, question hors contexte —
check(P.repond("quelle énergie ?", S.Situation()) is None, "fil vide -> None")
sit7 = S.Situation()
sit7.apprend(1, "je pars dans 2 heures")
check(P.repond("et si on partait dans 3 heures ?", sit7) is None,
      "« et si on partait dans 3 heures ? » (durée seule, aucun contexte énergie) -> None")
sit8 = S.Situation()
sit8.apprend(1, "le fluide chaud entre à 90 degrés et sort à 50 degrés")
check(P._energie("quelle énergie ?", sit8) is None, "fil thermo sans P/E/durée -> None (pas d'ancrage)")

# — ET-SI : simulation avant, fil intact —
r = P.repond("et si ça tournait 6 heures, quelle énergie ?", sit)
check(r is not None and "12 kWh" in r and "au lieu de 6 kWh" in r and "inchangé" in r,
      "et-si t=6 h -> 12 kWh au lieu de 6, fil réel inchangé")
r2 = P.repond("quelle énergie consommée ?", sit)
check(r2 is not None and "6 kWh" in r2, "le fil réel est intact après l'et-si énergie")

# — POURQUOI q± : preuve 2 points, constante DITE —
r = P.repond("pourquoi l'énergie augmente quand la durée augmente ?", sit)
check(r is not None and "PROUVÉ" in r and "7,2" in r and "puissance constante" in r,
      "dir vraie : preuve 2 points (3 h -> 6 kWh ; 3,6 h -> 7,2 kWh), puissance DITE constante")
r = P.repond("pourquoi l'énergie baisse quand la puissance augmente ?", sit)
check(r is not None and "Ce n'est pas ce qui se passe" in r and "AUGMENTE" in r,
      "prémisse fausse -> corrigée (elle AUGMENTE)")
r = P.repond("de quoi dépend l'énergie ?", sit)
check(r is not None and "E = P·t" in r and "1 kWh = 1000 W" in r, "dep énergie : la définition + le kWh expliqué")

# — « pourquoi ? » nu sur une réponse énergie -> la définition expliquée —
rd = P.repond("quelle énergie consommée ?", sit)
r = P.pourquoi_dernier("pourquoi ?", rd, sit)
check(r is not None and "E = P·t" in r and "DÉFINITION" in r,
      "pourquoi ? nu sur une réponse énergie -> E = P·t expliqué")

print("=== valide_roue_energie : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
