# -*- coding: utf-8 -*-
"""VALIDE faits_conversation — mémoire conversationnelle à EXTRACTION (audit item 12). FAUX=0.

Couvre : extraction fermée (nom/âge/lieu), restitution ATTRIBUÉE, correction d'AUTORITÉ (verbale + nue sous
focus), perte de focus (garde), rejeu depuis les tours (persistance = les tours déjà stockés), zéro capture
des questions-monde, redite sans bruit, ambiguïté non devinée."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import faits_conversation as F

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — extraction + restitution attribuée —
fc = F.FaitsConversation()
r = fc.apprend("le chien s'appelle Rex")
check(r is not None and r[0] == "appris" and r[1]["valeur"] == "Rex", "déclaration nom -> fait extrait")
acc = fc.accuse(r)
check("le chien s'appelle Rex" in acc and "redemander" in acc, "accusé SPÉCIFIQUE (plus le « C'est noté » générique)")
rep = fc.repond("comment s'appelle le chien ?")
check(rep is not None and rep.startswith("Rex") and "toi qui me l'as dit" in rep,
      "restitution EXTRAITE (pas un écho verbatim) + attribution à l'utilisateur")
check(fc.repond("quel est le nom du chien ?") is not None, "variante « quel est le nom de »")
check(fc.repond("mon chien s'appelle comment ?") is not None, "article/possessif indifférents (chien == mon chien)")

# — correction d'autorité : Rex -> Max (LE flux de l'audit) —
r = fc.apprend("en fait c'est Max")
check(r is not None and r[0] == "corrige" and r[1]["valeur"] == "Max" and r[2] == "Rex",
      "correction NUE sous focus -> remplace (autorité utilisateur, sans exigence de source)")
rep = fc.repond("comment s'appelle le chien ?")
check(rep is not None and rep.startswith("Max") and "Rex" in rep and "autorité" in rep,
      "re-demande -> Max, l'historique et l'autorité de la correction sont DITS")
r = fc.apprend("non, il s'appelle Rox")
check(r is not None and r[1]["valeur"] == "Rox", "correction VERBALE pronominale (« il s'appelle X »)")

# — âge / lieu —
fc.apprend("ma fille a 7 ans")
rep = fc.repond("quel âge a ma fille ?")
check(rep is not None and rep.startswith("7 ans"), "âge extrait et restitué en années")
fc.apprend("mon frère habite à Lyon")
check((fc.repond("où habite mon frère ?") or "").startswith("Lyon"), "lieu extrait (habite/vit)")

# — GARDES (FAUX=0) —
fc2 = F.FaitsConversation()
fc2.apprend("le chat s'appelle Momo")
fc2.apprend("quelle est la capitale de la France ?")            # message étranger -> focus PERDU
check(fc2.apprend("en fait c'est Félix") is None,
      "correction nue SANS focus -> refusée (la correction-monde garde sa route)")
check((fc2.repond("comment s'appelle le chat ?") or "").startswith("Momo"), "Momo intact après la garde")
check(fc2.repond("comment s'appelle le président de la France ?") is None,
      "sujet jamais déclaré -> None (zéro capture d'une question-monde)")
check(fc2.repond("comment s'appelle le chien ?") is None, "autre sujet inconnu -> None")
check(fc2.apprend("le chat s'appelle Momo") is None, "redite EXACTE -> rien de neuf (pas de faux « corrigé »)")
fc3 = F.FaitsConversation()
fc3.apprend("le chien s'appelle Rex")
fc3.apprend("le chat s'appelle Momo")
fc3.apprend("bonjour")                                           # focus perdu + DEUX faits nom
check(fc3.apprend("non, il s'appelle Max") is None,
      "correction pronominale AMBIGUË (2 sujets, pas de focus) -> refusée, jamais devinée")
check(fc3.apprend("il ne faut pas oublier d'appeler le plombier demain") is None,
      "phrase complexe -> aucun motif (extraction ancrée message entier)")

# — rejeu depuis les tours (persistance/RGPD gratuits) —
tours = [{"role": "user", "texte": "le chien s'appelle Rex"},
         {"role": "ia", "texte": "Noté : le chien s'appelle Rex."},
         {"role": "user", "texte": "comment s'appelle le chien ?"},
         {"role": "ia", "texte": "Rex."},
         {"role": "user", "texte": "en fait c'est Max"}]
fc4 = F.depuis_tours(tours)
rep = fc4.repond("comment s'appelle le chien ?")
check(rep is not None and rep.startswith("Max"), "REJEU des tours -> état exact (correction comprise)")
check(F.depuis_tours([]).repond("comment s'appelle le chien ?") is None, "conversation vide -> None")

print("=== valide_faits_conversation : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
