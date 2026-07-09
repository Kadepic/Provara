# -*- coding: utf-8 -*-
"""VALIDE les actes « ET SI » (monde contrefactuel, simulation avant) et « POURQUOI » (explication causale
PROUVÉE par recalcul) du pont grandeurs→moteurs (brique 3 du fil). FAUX=0 : avant/après vérifiés contre calcul
indépendant, fil réel JAMAIS modifié, °C jamais multiplié, prémisse fausse corrigée, zéro capture."""
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


def f4(v):
    return ("%.4f" % v).rstrip("0").rstrip(".").replace(".", ",")


sit = S.Situation()
sit.apprend(1, "Je conçois un échangeur à contre-courant ; le fluide chaud entre à 90 degrés et sort à 50 degrés ; le froid entre à 20 degrés et sort à 45 degrés.")
sit.apprend(3, "la puissance à passer est de 100 kW avec un coefficient global de 500 W/m2K")
d0 = 15 / math.log(45 / 30)                                          # DTLM réel (45/30, contre-courant)

# — ET SI : remplacement d'un slot -> DTLM ET surface re-propagés, avant/après exacts —
r = P.repond("et si le fluide froid sortait à 60 degrés, quel serait le DTLM ?", sit)
# monde hypothétique : ΔT1 = 90−60 = 30, ΔT2 = 50−20 = 30 -> DTLM = 30 (bornes égales)
check(r is not None and "hypothèse" in r and "DTLM ≈ 30 degrés" in r, "et-si slot : DTLM hypothétique = 30 exact")
check(r is not None and "au lieu de " + f4(round(d0, 4)) in r, "l'avant/après montre la valeur RÉELLE (%s)" % f4(round(d0, 4)))
check(r is not None and f4(round(100000 / (500 * 30.0), 4)) in r, "la surface est RE-PROPAGÉE dans le monde hypothétique (6,6667 m²)")
check(r is not None and "inchangé" in r, "il est DIT que le fil réel n'a pas bougé")
r2 = P.repond("quel est le DTLM ?", sit)
check(r2 is not None and f4(round(d0, 4)) in r2, "le fil RÉEL est intact après l'et-si (hypothèse jamais promue)")

# — nombre nu -> degrés implicites, supposition étiquetée —
r = P.repond("et si le froid sortait à 60 ?", sit)
check(r is not None and "DTLM ≈ 30 degrés" in r and "implicite" in r, "« sortait à 60 » nu -> degrés IMPLICITES étiquetés")

# — hypothèse physiquement impossible -> DIT —
r = P.repond("et si le fluide froid sortait à 95 degrés ?", sit)
check(r is not None and "impossible" in r, "hypothèse qui casse la physique (ΔT borne ≤ 0) -> « impossible » DIT")

# — et-si qui COMPLÈTE un fil troué : réponse + fil réel signalé incomplet —
sit2 = S.Situation()
sit2.apprend(1, "échangeur à contre-courant ; le fluide chaud entre à 90 degrés et sort à 50 degrés ; le froid entre à 20 degrés")
r = P.repond("et si le froid sortait à 45 degrés ?", sit2)
check(r is not None and f4(round(d0, 4)) in r and "n'a pas cette donnée" in r,
      "et-si complète un slot manquant -> calcul + « ton fil réel n'a pas cette donnée »")

# — multiplicateurs : puissance doublée -> surface doublée (exact) ; % ; température refusée (non-ratio) —
r = P.repond("et si on doublait la puissance, quelle surface ?", sit)
a0, a1 = 100000 / (500 * d0), 200000 / (500 * d0)
check(r is not None and f4(round(a1, 4)) in r and f4(round(a0, 4)) in r,
      "puissance ×2 -> surface %s au lieu de %s (avant/après exacts)" % (f4(round(a1, 4)), f4(round(a0, 4))))
r = P.repond("et si la puissance baissait de 20 %, quelle surface ?", sit)
check(r is not None and f4(round(80000 / (500 * d0), 4)) in r, "puissance −20 % -> surface re-propagée exacte")
r = P.repond("et si on doublait la température du fluide chaud ?", sit)
check(r is not None and "non-ratio" in r, "température ×2 -> REFUSÉ (échelle non-ratio), valeur cible demandée")
r = P.repond("et si on doublait le débit ?", sit)
check(r is not None and "je ne simule pas" in r.lower(), "débit ×2 -> honnête : aucun calcul fermé ne l'utilise")

# — et-si sur Q/U/DTLM par VALEUR —
r = P.repond("et si le DTLM était de 30, quelle surface ?", sit)
check(r is not None and f4(round(100000 / (500 * 30.0), 4)) in r, "« et si le DTLM était de 30 » -> surface exacte")
r = P.repond("et si le coefficient était de 1000 W/m2K, quelle surface ?", sit)
check(r is not None and f4(round(100000 / (1000 * d0), 4)) in r, "U remplacé par valeur -> surface exacte")

# — multiplicateur sans valeur réelle -> demande NOMMÉE —
sit3 = S.Situation()
sit3.apprend(1, "échangeur à contre-courant ; le fluide chaud entre à 90 degrés et sort à 50 degrés")
r = P.repond("et si on doublait la puissance ?", sit3)
check(r is not None and "RÉELLE" in r, "×2 sans puissance réelle connue -> demande nommée de la valeur à multiplier")

# — zéro capture des « et si » étrangers —
for q in ("et si on allait à la plage ?", "et si on doublait la mise ?", "et s'il pleuvait demain ?",
          "et si Napoléon avait gagné à Waterloo ?"):
    check(P.repond(q, sit) is None, "hors registre : %r -> None" % q)

# — POURQUOI : direction q± prouvée par recalcul (jamais affirmée à la main) —
r = P.repond("pourquoi la surface augmente quand le DTLM baisse ?", sit)
check(r is not None and "DÉNOMINATEUR" in r and "Preuve par recalcul" in r,
      "direction correcte -> mécanisme (formule) + preuve par recalcul")
check(r is not None and f4(round(100000 / (500 * (d0 * 0.8)), 4)) in r,
      "la preuve contient le point recalculé (ΔTlm ×0,8 -> A exacte)")

# — prémisse FAUSSE -> corrigée, jamais validée —
r = P.repond("pourquoi la surface augmente quand le DTLM augmente ?", sit)
check(r is not None and "Ce n'est pas ce qui se passe" in r and "DIMINUE" in r,
      "prémisse fausse (A monte avec ΔTlm) -> CORRIGÉE avec la direction réelle")

# — pourquoi le sens d'écoulement compte : les DEUX sens calculés sur les données —
r = P.repond("pourquoi le sens d'écoulement compte-t-il ?", sit)
d_co = 65 / math.log(70 / 5)                                         # co-courant : ΔT1 = 70, ΔT2 = 5
check(r is not None and f4(round(d0, 4)) in r and f4(round(d_co, 4)) in r,
      "sens d'écoulement : contre (%s) ET co (%s) calculés sur les données" % (f4(round(d0, 4)), f4(round(d_co, 4))))

# — ordre causal (« de quoi dépend ») —
r = P.repond("de quoi dépend la surface d'échange ?", sit)
check(r is not None and "Q = U·A·ΔTlm" in r and "ordre causal" in r, "dépendances de la surface = ordre causal complet")
r = P.repond("de quoi dépend le DTLM ?", sit)
check(r is not None and "sens" in r.lower() and "ΔT1" in r, "dépendances du DTLM : 4 températures + sens")

# — effet d'un slot sur le DTLM : MESURÉ par perturbation —
r = P.repond("pourquoi le DTLM baisse quand la sortie du fluide froid augmente ?", sit)
d_pert = 10 / math.log(40 / 30)                                      # tf_out 45->50 : ΔT1 = 40, ΔT2 = 30
check(r is not None and "PROUVÉ par recalcul" in r and f4(round(d_pert, 4)) in r and "baisse" in r,
      "effet slot->DTLM mesuré par perturbation (+5°) : %s -> il baisse" % f4(round(d_pert, 4)))

# — pourquoi sans données -> jamais une tendance affirmée sans preuve —
r = P.repond("pourquoi le DTLM baisse quand la sortie du fluide froid augmente ?", S.Situation())
check(r is not None and "sans preuve" in r, "sans données : demande des opérandes, ne déclare PAS la tendance")

# — zéro capture des « pourquoi » étrangers —
for q in ("pourquoi le ciel est bleu ?", "pourquoi Napoléon a perdu à Waterloo ?",
          "pourquoi la surface de la Belgique est petite si on la compare à la France ?",
          "pourquoi la puissance baisse quand le rendement baisse ?"):
    check(P.repond(q, sit) is None, "hors registre : %r -> None" % q[:50])

# — « pourquoi ? » NU sur la dernière réponse du pont (mécanisme) —
rd = P.repond("quel est le DTLM ?", sit)
r = P.pourquoi_dernier("pourquoi ?", rd, sit)
check(r is not None and "moyenne logarithmique" in r, "pourquoi ? nu sur une réponse DTLM -> mécanisme du log-mean")
rs = P.repond("quelle surface d'échange me faut-il pour 100 kW avec un coefficient global de 500 W/m2K ?", sit)
r = P.pourquoi_dernier("pourquoi ?", rs, sit)
check(r is not None and "Q = U·A·ΔTlm" in r, "pourquoi ? nu sur une réponse Surface -> définition de U + ordre causal")
rm = P.repond("quel est le DTLM ?", S.Situation())                   # réponse « il me manque… »
r = P.pourquoi_dernier("pourquoi ?", rm, sit)
check(r is not None and "je ne devine jamais" in r, "pourquoi ? nu sur une demande d'opérande -> principe FAUX=0 dit")
check(P.pourquoi_dernier("pourquoi ?", "Paris est la capitale de la France.", sit) is None,
      "dernière réponse étrangère au pont -> None (le pipeline continue)")
check(P.pourquoi_dernier("pourquoi le ciel est bleu ?", rd, sit) is None,
      "« pourquoi » CONTENTFUL étranger -> jamais traité comme un pourquoi nu")

# — l'hypothèse « si… » du fil ne fixe JAMAIS le sens d'écoulement du monde réel (correctif FAUX=0) —
sit5 = S.Situation()
sit5.apprend(1, "le fluide chaud entre à 90 degrés et sort à 50 degrés ; le froid entre à 20 degrés et sort à 45 degrés")
sit5.apprend(3, "si c'était à contre-courant, ce serait mieux")
r = P.repond("quel est le DTLM ?", sit5)
check(r is not None and "SENS d'écoulement" in r, "« si c'était à contre-courant » (hypothèse) ne fixe pas le sens réel")

print("=== valide_et_si_pourquoi : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
