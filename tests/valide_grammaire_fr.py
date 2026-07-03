# -*- coding: utf-8 -*-
"""VALIDE grammaire_fr : analyse grammaticale française, FAUX=0 (jamais de classe inventée).

Priorité SOUNDNESS : on vérifie surtout que le module ne tague JAMAIS faux (mots-outils fermés corrects, mots
ambigus -> 'inconnu' plutôt qu'un choix arbitraire), et que le TYPE de phrase (question/affirmation/ordre) est
correct — c'est l'output le plus utile au routage conversationnel."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import grammaire_fr as G

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# (1) mots-outils (ensembles FERMÉS) -> classe exacte
for mot, cl in [("le", "déterminant"), ("un", "déterminant"), ("je", "pronom"), ("nous", "pronom"),
                ("dans", "préposition"), ("avec", "préposition"), ("et", "conjonction"), ("mais", "conjonction"),
                ("est", "auxiliaire"), ("sont", "auxiliaire"), ("ne", "adverbe"), ("très", "adverbe")]:
    check(G.classe_mot(mot) == cl, "mot-outil « %s » -> %s" % (mot, cl))

# (2) mots pleins via lexique massif -> classe correcte
for mot, cl in [("chat", "nom"), ("souris", "nom"), ("dormir", "verbe"),
                ("heureux", "adjectif"), ("rapidement", "adverbe"), ("hiver", "nom")]:
    check(G.classe_mot(mot) == cl, "mot plein « %s » -> %s" % (mot, cl))

# (3) SOUNDNESS : mots ambigus / pièges -> jamais taggés FAUX (inconnu accepté, verbe/faux REFUSÉ)
check(G.classe_mot("noir") != "verbe", "« noir » n'est PAS taggé verbe (piège ‑ir)")
check(G.classe_mot("amer") != "verbe", "« amer » n'est PAS taggé verbe")
check(G.classe_mot("xyzzy") == "inconnu", "mot inexistant -> inconnu (pas d'invention)")
check(G.classe_mot("Paris") == "nom propre", "majuscule -> nom propre")

# (4) genre grammatical (quand connu)
check(G.genre_mot("chat") == "masculin", "genre « chat » masculin")
check(G.genre_mot("souris") == "féminin", "genre « souris » féminin")
check(G.genre_mot("xyzzy") is None, "genre inconnu -> None (pas d'invention)")

# (5) TYPE de phrase — l'output clé du routage
cas = [
    ("Le chat dort.", "affirmation", False),
    ("Quelle est la capitale de la France ?", "question", False),
    ("Comment fais-tu ça ?", "question", False),
    ("Viens-tu demain ?", "question", False),
    ("Donne-moi la population du Japon.", "ordre", False),
    ("Je ne veux pas de café.", "affirmation", True),
    ("Il n'a jamais compris.", "affirmation", True),
    ("Quel beau paysage !", "exclamation", False),
]
for ph, typ, neg in cas:
    tp = G.type_phrase(ph)
    check(tp["type"] == typ, "type « %s » -> %s (vu %s)" % (ph, typ, tp["type"]))
    check(tp["negative"] == neg, "négation « %s » -> %s" % (ph, neg))

# (6) question sans « ? » (ponctuation oubliée) reste détectée par le mot interrogatif
check(G.type_phrase("quelle est la monnaie du Japon")["type"] == "question", "question sans « ? » détectée")

# (7) structure SVO avec auxiliaire connu
st = G.structure("le chat est noir")
check(st["verbe"] == "est", "structure : verbe = est (auxiliaire)")
check(st["sujet"] == "le chat", "structure : sujet = le chat")

# (7bis) FORMES CONJUGUÉES reconnues (index inverse) -> SVO réel
for forme in ["dort", "mange", "parlait", "mangeons", "finit", "vais", "chante", "travaillons"]:
    check(G.classe_mot(forme) in ("verbe", "auxiliaire"), "forme conjuguée « %s » -> verbe" % forme)
# soundness : des pièges NE sont PAS des verbes
for piege in ["noir", "dent", "maison", "chaise", "comment"]:
    check(G.classe_mot(piege) != "verbe", "piège « %s » n'est PAS verbe" % piege)
st = G.structure("le chien mange la souris")
check(st["verbe"] == "mange" and st["sujet"] == "le chien" and st["objet"] == "la souris",
      "SVO avec verbe conjugué : le chien / mange / la souris")
st = G.structure("le lion chasse la gazelle")
check(st["verbe"] == "chasse" and st["objet"] == "la gazelle", "SVO : le lion chasse la gazelle")

# (8) analyse renvoie une paire par mot
paires = G.analyse("le chien mange")
check(len(paires) == 3 and paires[0] == ("le", "déterminant"), "analyse : une paire (mot, classe) par mot")

# (9) resume_analyse lisible
r = G.resume_analyse("Le chat dort.")
check("Type : affirmation" in r and "chat : nom" in r, "resume_analyse : type + natures")

print("=== valide_grammaire_fr : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
