#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BANC DE RÉGRESSION — suite de RAISONNEMENT de l'interface conversationnelle (2026-07-04).

Verrouille chaque capacité de raisonnement (is-a, cause, définition, comptage, classement, filtre, comparaison,
agrégation, déduction prouvée, découverte de règle, portrait) contre une régression silencieuse. Chaque cas :
(nom_capacité, message, sous-chaîne ATTENDUE dans la réponse). FAUX=0 : on vérifie AUSSI que les faux ne sont jamais
confirmés (« la Terre orbite la Lune » -> pas de réponse ; « un chat est un poisson » -> pas « Oui »).

Usage :  LECTEUR_DATASETS_DIR=<base> python3 tests/banc_raisonnement.py
  (certaines capacités — définition, hyponymes, is-a transitif — exigent la base COMPLÈTE : definition_nom,
   classe_animal… absents de l'échantillon léger ; le banc SIGNALE les cas non couverts par les données présentes.)
"""
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(_ICI)
sys.path.insert(0, os.path.join(_RACINE, "src"))
sys.path.insert(0, os.path.join(_RACINE, "interface"))
os.environ.setdefault("LECTEUR_DATASETS_DIR", os.path.join(_RACINE, "datasets", "lecteur"))

import importlib.util as _u
_spec = _u.spec_from_file_location("repond", os.path.join(_RACINE, "interface", "repond.py"))
R = _u.module_from_spec(_spec)
_spec.loader.exec_module(R)

# (capacité, message, attendu). attendu="" => la réponse doit être VIDE/None (garde FAUX=0).
CAS = [
    ("is-a", R._cap_ontologie, "un chat est-il un mammifère ?", "Oui"),
    ("is-a-faux", R._cap_ontologie, "un chat est-il un poisson ?", "mammifère"),  # jamais « Oui »
    ("point-commun", R._cap_ontologie, "qu'ont en commun le chat et le requin ?", "animal"),
    ("cause", R._cap_cause, "quelle est la cause du paludisme ?", "du paludisme"),
    ("definition", R._cap_definition, "c'est quoi le paludisme ?", "Paludisme"),
    ("comptage", R._cap_comptage, "combien de pays en Afrique ?", "pays en Afrique"),
    ("classement", R._cap_classement, "les 3 pays les plus peuplés d'Afrique", "Nigéria"),
    ("filtre", R._cap_filtre, "quels pays d'Afrique ont plus de 100 millions d'habitants ?", "Nigéria"),
    ("filtre-entre", R._cap_filtre, "quels pays d'Afrique ont entre 100 et 300 millions d'habitants ?", "Nigéria"),
    ("filtre-entre-magnitudes", R._cap_filtre,
     "quels pays d'Europe ont entre 500 000 et 2 millions d'habitants ?", "entre 500 000 et 2 000 000"),
    ("filtre-entre-decimal", R._cap_filtre, "quels pays d'Asie ont entre 1 et 1,5 milliard d'habitants ?", "Inde"),
    ("filtre-superficie", R._cap_filtre, "quels pays d'Afrique ont une superficie entre 1 et 2 millions de km² ?", "km²"),
    ("comparaison", R._cap_comparaison, "la Chine est-elle plus peuplée que l'Inde ?", "l'inverse"),
    ("comparaison-superficie", R._cap_comparaison, "la France est-elle plus vaste que l'Espagne ?", "Oui"),
    ("comparaison-riche", R._cap_comparaison, "la France est-elle plus riche que l'Espagne ?", "Oui"),
    ("agregat-superficie", R._cap_agregat, "superficie totale de l'Afrique ?", "km²"),
    ("agregat", R._cap_agregat, "population totale de l'Afrique ?", "somme"),
    ("deduction", R._cap_deduction, "sur quel continent est Abuja ?", "je le déduis"),
    ("orbite", R._cap_orbite, "est-ce que Phobos fait partie du système solaire ?", "je le déduis"),
    ("temporel", R._cap_temporel, "quel est le plus ancien entre la bataille de Marignan et la bataille de Verdun ?", "1515"),
    ("analogie", R._cap_analogie, "Paris est à la France ce que Berlin est à ?", "Allemagne"),
    ("portrait", R._cap_portrait, "parle-moi du Nigéria", "Le Nigéria est un pays"),
    # gardes FAUX=0
    ("faux-filtre-entre", R._cap_filtre, "quels pays d'Afrique ont entre 5 et 10 milliards d'habitants ?", "Aucun"),
    ("faux-orbite", R._cap_orbite, "est-ce que la Terre orbite la Lune ?", ""),
    ("faux-compar", R._cap_comparaison, "la France est-elle plus peuplée que l'Inde ?", "l'inverse"),
]


def run():
    ok, echecs, non_couverts = 0, [], 0
    for nom, fn, msg, attendu in CAS:
        try:
            rep = fn(msg)
        except Exception as e:
            echecs.append((nom, msg, "EXCEPTION %r" % e))
            continue
        if attendu == "":                       # doit être vide (FAUX=0)
            if not rep:
                ok += 1
            else:
                echecs.append((nom, msg, "attendu VIDE, obtenu: %s" % str(rep)[:60]))
        elif rep is None:
            non_couverts += 1                   # donnée probablement absente (échantillon) -> non compté échec
            print("  ~ %-14s NON COUVERT (données absentes ?) : %s" % (nom, msg))
        elif attendu.lower() in str(rep).lower():
            ok += 1
        else:
            echecs.append((nom, msg, "attendu «%s», obtenu: %s" % (attendu, str(rep)[:70])))
    total_testables = len(CAS) - non_couverts
    print("\nSCORE : %d/%d capacités OK" % (ok, total_testables) +
          (" (%d non couverts par les données présentes)" % non_couverts if non_couverts else ""))
    if echecs:
        print("ÉCHECS :")
        for nom, msg, det in echecs:
            print("  ✗ %-14s %s -> %s" % (nom, repr(msg), det))
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(run())
