# -*- coding: utf-8 -*-
"""VALIDE situation (« tenir le fil ») — clauses verbatim tenues, grandeurs typées, rappel filtré, résumé
calculé, hypothèses étiquetées, ellipse d'unité en SUPPOSITION. FAUX=0 : toute restitution CITE sa clause
source + tour ; question ≠ assertion ; sujet jamais évoqué -> None (zéro à-côté)."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import situation as S

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


s = S.Situation()
s.apprend(1, "Je conçois un échangeur thermique à contre-courant ; le fluide chaud entre à 90 degrés et sort à 50, le froid entre à 20 degrés.")
s.apprend(3, "Le débit du fluide froid est de 2 kg/s.")
s.apprend(5, "Si je double le débit, la sortie devrait baisser.")
s.apprend(7, "quelle est la capitale de la France ?")
s.apprend(9, "ok merci")

# — rappel FILTRÉ, ancré (clause verbatim + tour) —
r = s.repond("reprends ce que je t'ai dit sur le fluide chaud")
check(r is not None and "90 degrés" in r and "(tour 1)" in r, "rappel filtré 'fluide chaud' -> clause verbatim + tour")
check("échangeur" not in (r or ""), "rappel filtré : les clauses hors sujet ne sont PAS mélangées")
r = s.repond("qu'est-ce que je t'ai dit sur le débit ?")
check(r is not None and "2 kg/s" in r and "[hypothèse]" in r,
      "rappel 'débit' -> la donnée ET l'hypothèse, l'hypothèse ÉTIQUETÉE (jamais promue en fait)")
check(s.repond("reprends ce que je t'ai dit sur les dauphins") is None, "sujet jamais évoqué -> None (zéro à-côté)")

# — résumé CALCULÉ depuis l'ancré —
r = s.repond("résume notre conversation")
check(r is not None and "échangeur" in r and "2 kg/s" in r and "Grandeurs relevées" in r,
      "résumé = clauses tenues + grandeurs typées")
check("capitale" not in r, "une QUESTION posée n'entre jamais dans le fil comme assertion")
check("ok merci" not in r, "une interjection n'entre pas dans le fil")
r2 = s.repond("fais-moi le point")
check(r2 is not None and "échangeur" in r2, "variante « fais-moi le point » -> résumé")

# — grandeurs typées + ellipse d'unité en SUPPOSITION étiquetée —
r = s.repond("quelles données je t'ai données ?")
check(r is not None and "90 degrés (température)" in r and "2 kg/s (débit)" in r,
      "grandeurs typées par dimension (température, débit)")
check("50 (degrés implicite)" in r, "ellipse « sort à 50 » -> tenue en unité IMPLICITE (supposition dite)")
gr = s.grandeurs_de("fluide chaud")
check(len(gr) == 3 and gr[0]["valeur"] == 90.0 and gr[1]["implicite"],
      "grandeurs_de(sujet) = interface du PONT vers les moteurs (3 valeurs du fluide, ellipse flaguée)")
check(s.grandeurs_de("dauphins") == [], "grandeurs_de(sujet inconnu) -> vide")

# — hypothèses jamais mélangées aux faits du pont —
check(all(not g["hypothese"] for g in s.grandeurs_de("fluide chaud")),
      "les grandeurs du fluide chaud ne portent pas le flag hypothèse")
check(all(g["hypothese"] for g in s.grandeurs_de("sortie")) or s.grandeurs_de("sortie") == [],
      "une grandeur énoncée SOUS « si » reste flaguée hypothèse")

# — zéro capture : questions normales -> None —
for q in ("quelle est la capitale de la France ?", "combien font 2 + 2 ?", "reprends ton souffle",
          "résumé du match d'hier ?"):
    check(s.repond(q) is None, "hors périmètre : %r -> None" % q)

# — conversation vide : réponses honnêtes —
v = S.Situation()
check(v.repond("résume notre conversation") is None, "fil vide -> None (le pipeline dira l'honnête)")
check(v.repond("quelles données je t'ai données ?") is not None and "aucune" in v.repond("quelles données je t'ai données ?"),
      "données sur fil vide -> « aucune grandeur » honnête")

# — rejeu depuis les tours (persistance/RGPD gratuits) —
tours = [{"role": "user", "seq": 1, "texte": "mon moteur tourne à 3000 tours et consomme 8 litres"},
         {"role": "ia", "seq": 2, "texte": "Noté."},
         {"role": "user", "seq": 3, "texte": "à quelle vitesse va-t-il ?"}]
s2 = S.depuis_tours(tours)
r = s2.repond("reprends ce que je t'ai dit sur le moteur")
check(r is not None and "8 litres" in r, "REJEU des tours -> fil reconstruit (8 litres retrouvés)")

print("=== valide_situation : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
