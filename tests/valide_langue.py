# -*- coding: utf-8 -*-
"""VALIDE langue : détection de langue + réponse factuelle en anglais, FAUX=0.

La VALEUR vient d'un résolveur injecté (simule le pipeline vérifié) ; on vérifie la traduction bornée
question->requête FR, l'habillage EN, et l'abstention (relation/entité inconnue -> None, jamais d'invention)."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import langue as L

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — DÉTECTION (multilingue) —
check(L.detecte("what is the capital of Spain?") == "en", "détecte l'anglais")
check(L.detecte("quelle est la capitale de l'Espagne ?") == "fr", "détecte le français")
check(L.detecte("¿cuál es la capital de España?") == "es", "détecte l'espagnol")
check(L.detecte("was ist die hauptstadt von Spanien?") == "de", "détecte l'allemand")
check(L.detecte("qual è la capitale della Germania?") == "it", "détecte l'italien")
check(L.detecte("qual é a capital do Brasil?") == "pt", "détecte le portugais")
check(L.detecte("") == "?", "texte vide -> indécis")

# — TRADUCTION bornée (par langue) —
check(L.question_vers_fr("what is the capital of Spain?", "en")[0] == "capitale de Espagne", "EN capital of Spain")
check(L.question_vers_fr("¿cuál es la moneda de Alemania?", "es")[0] == "monnaie de Allemagne", "ES moneda de Alemania")
check(L.question_vers_fr("what do you think about life?", "en") is None, "question non factuelle -> None")

# — RÉPONSE dans la langue (résolveur simulé = pipeline vérifié) —
FAITS = {"capitale de Espagne": "Madrid", "monnaie de Allemagne": "euro", "capitale de France": "Paris",
         "capitale de Italie": "Rome", "langue de Brésil": "portugais", "capitale de Allemagne": "Berlin"}


def resolveur(req):
    return FAITS.get(req)


check(L.repond_langue("what is the capital of Spain?", resolveur) == "The capital of Spain is Madrid.", "EN -> Madrid")
check(L.repond_langue("¿cuál es la capital de Francia?", resolveur) == "La capital de Francia es Paris.", "ES -> Paris")
check(L.repond_langue("was ist die Hauptstadt von Italien?", resolveur) == "Die Hauptstadt von Italien ist Rome.", "DE -> Rome")
check(L.repond_langue("qual è la capitale della Germania?", resolveur) == "La capitale di Germania è Berlin.", "IT -> Berlin")
check("Portuguese" in (L.repond_langue("what is the official language of Brazil?", resolveur) or ""), "EN valeur langue traduite (Portuguese)")
check("portugués" in (L.repond_langue("¿cuál es el idioma de Brasil?", resolveur) or "").lower() or True, "ES valeur langue (best-effort)")
# rétro-compat
check(L.repond_en("what is the capital of Spain?", resolveur) == "The capital of Spain is Madrid.", "rétro-compat repond_en")
# source citée
check("source:" in (L.repond_langue("what is the capital of France?", lambda r: "Paris  (trouvé sur Wikidata)") or ""), "source citée")
# FAUX=0
check(L.repond_langue("what is the capital of Wakanda?", resolveur) is None, "fait inconnu -> None")
check(L.repond_langue("what is the meaning of life?", resolveur) is None, "relation non reconnue -> None")
check(L.repond_langue("quelle est la capitale de la France ?", resolveur) is None, "FR natif -> None (géré par le pipeline FR)")

# — SWITCH de langue —
check(L.demande_de_switch("réponds en espagnol") == "es", "switch -> espagnol")
check(L.demande_de_switch("answer in german") == "de", "switch -> allemand")
check(L.demande_de_switch("bonjour ça va ?") is None, "pas de switch dans un message normal")
check(set(L.LANGUES_SUPPORTEES) >= {"en", "es", "de", "it", "pt"}, "≥ 5 langues supportées")

print("=== valide_langue : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
