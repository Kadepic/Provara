# -*- coding: utf-8 -*-
"""VALIDE formes_verbales : reconnaissance des formes conjuguées, FAUX=0.

On vérifie que des formes conjuguées connues sont reconnues (présent/imparfait/futur/participe, réguliers et
irréguliers fréquents) ET que des pièges (noms/adjectifs en ‑ir/‑ent/‑ons) ne sont JAMAIS pris pour des verbes."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import formes_verbales as F

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# formes RECONNUES (doivent être True)
reconnues = [
    "parle", "parles", "parlons", "parlez", "parlent", "parlait", "parlais", "parlera", "parlé", "parlant",
    "mange", "mangeons", "mangeait", "mangera",
    "finit", "finis", "finissons", "finissait", "grandit", "choisit",
    "dort", "dorment", "dormait", "part", "sort", "sent", "sert",
    "vais", "va", "vont", "allait",                      # aller (irrégulier)
    "suis", "est", "sont", "était",                      # être
    "ai", "as", "a", "ont", "avait",                     # avoir
    "fait", "font", "dit", "voit", "sait", "peut", "veut", "doit", "vient", "prend",
    "travaille", "travaillons", "chante", "donne", "cherche", "trouve", "aime",
]
for f in reconnues:
    check(F.est_forme_verbale(f), "forme reconnue : « %s »" % f)

# pièges : NE doivent PAS être reconnus comme verbes (noms/adjectifs/adverbes SANS homographe verbal).
# (« table »/« content » SONT exclus : ce sont de vrais homographes — « tabler », « ils content » de conter —
#  donc est_forme_verbale=True est CORRECT ; la garantie de soundness est que la GRAMMAIRE les tague bien
#  nom/adjectif via le lexique prioritaire, vérifié plus bas.)
pieges = ["noir", "plaisir", "loisir", "dent", "comment", "argent", "maison", "chaise", "poumon",
          "démon", "nation", "rouge", "lent", "souvent"]
for p in pieges:
    check(not F.est_forme_verbale(p), "piège NON-verbe : « %s »" % p)

# soundness au niveau GRAMMAIRE : les homographes -> classe nom/adjectif (lexique prioritaire), jamais verbe
import grammaire_fr as _G
check(_G.classe_mot("table") == "nom", "grammaire : « table » -> nom (pas verbe)")
check(_G.classe_mot("content") in ("adjectif", "nom"), "grammaire : « content » -> adjectif/nom (pas verbe)")

# MODÈLES du 3e groupe (patrons Bescherelle) : familles systématiques
modeles = [
    # -re « attendre » (rendre/vendre/perdre/répondre/descendre)
    "attends", "attend", "rend", "vend", "perds", "réponds", "répond", "descend", "attendent",
    # « prendre »
    "prends", "prend", "prenons", "prennent", "apprend", "comprend",
    # « mettre »
    "mets", "met", "mettons", "permet", "promettent",
    # -indre
    "crains", "craint", "peins", "atteint", "joins", "joignons", "craignent",
    # -aître
    "connais", "connaît", "paraît", "paraissent", "reconnaît",
    # -uire
    "conduis", "conduit", "construit", "produit", "conduisons", "traduit",
    # ouvrir / courir / partir
    "couvre", "couvrons", "offre", "souffre", "cours", "court", "parcourt", "pars", "part", "dorment", "servent",
]
for f in modeles:
    check(F.est_forme_verbale(f), "modèle 3e groupe : « %s »" % f)

# lemme_de retrouve l'infinitif
check(F.lemme_de("dort") == "dormir", "lemme de « dort » = dormir")
check(F.lemme_de("mangeons") == "manger", "lemme de « mangeons » = manger")
check(F.lemme_de("vais") == "aller", "lemme de « vais » = aller")
check(F.lemme_de("xyzzy") is None, "mot inconnu -> lemme None")

print("=== valide_formes_verbales : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
