# -*- coding: utf-8 -*-
"""VALIDE confiance : corrections utilisateur (autorité) + sources bannies, FAUX=0.

Vérifie : une correction utilisateur est stockée et fait AUTORITÉ (prime, attribuée) ; le bannissement d'une
source la retire des recherches ; effacement RGPD ; robustesse d'entrée."""
from __future__ import annotations

import os
import sys
import tempfile

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

os.environ["VERAX_CONFIANCE_DIR"] = tempfile.mkdtemp(prefix="verax_confiance_")

import confiance as C
C.oublie()

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — CORRECTIONS UTILISATEUR (exigent une SOURCE) —
check(not C.corrige("capitale de la France ?", "Toulouse", ""),
      "FAUX=0 : correction SANS source REFUSÉE (pas d'écrasement de vérité)")
check(C.reponse_autorisee("capitale de la France ?") is None, "correction non sourcée non stockée")
check(C.corrige("quelle est la capitale de l'Australie ?", "Canberra", "wikipedia.org"),
      "correction AVEC source enregistrée")
e = C.reponse_autorisee("quelle est la capitale de l'Australie ?")
check(e and e["valeur"] == "Canberra" and e["source"] == "wikipedia.org", "correction sourcée retrouvée (valeur+source)")
check(C.reponse_autorisee("QUELLE EST LA CAPITALE DE L'AUSTRALIE ?")["valeur"] == "Canberra", "insensible casse/accents")
check(C.reponse_autorisee("question jamais corrigée") is None, "pas de correction inventée")
check(not C.corrige("", "x", "s") and not C.corrige("q", "", "s"), "refuse question/valeur vide")

# persistance
C._CACHE = None
check(C.reponse_autorisee("quelle est la capitale de l'Australie ?")["valeur"] == "Canberra", "correction persistante (disque)")

# écraser une correction (avec source)
C.corrige("capitale de l'australie", "Sydney", "blog.example")
C.corrige("capitale de l'australie", "Canberra", "wikidata")
check(C.reponse_autorisee("capitale de l'australie")["valeur"] == "Canberra", "dernière correction fait foi")

# effacement RGPD ciblé + global
check(C.oublie_correction("capitale de l'australie") == 1, "efface une correction ciblée")
check(C.reponse_autorisee("capitale de l'australie") is None, "correction ciblée effacée")

# — SOURCES BANNIES —
check(C.bannis_source("24matins.fr"), "bannit un domaine")
check(C.est_bannie("24matins.fr"), "domaine banni reconnu")
check(C.est_bannie("https://www.24matins.fr/article/x"), "banni reconnu depuis une URL complète")
check(C.est_bannie("sub.24matins.fr"), "sous-domaine d'un banni reconnu")
check(not C.est_bannie("lemonde.fr"), "domaine non banni -> non bloqué")
check(not C.bannis_source("24matins.fr"), "re-bannir le même -> pas de doublon")
check("24matins.fr" in C.sources_bannies(), "liste des bannis")
check(C.retablis_source("24matins.fr") and not C.est_bannie("24matins.fr"), "ré-autoriser un domaine")

# effacement global
C.corrige("q", "v", "src")
C.bannis_source("x.com")
C.oublie()
check(not C.sources_bannies() and C.reponse_autorisee("q") is None, "oublie() efface tout (RGPD)")

print("=== valide_confiance : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
