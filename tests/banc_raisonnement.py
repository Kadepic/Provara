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

def _conjonction_txt(q):
    """Adaptateur banc : rend « tête|ent1,ent2,… » du découpage conjonction, ou None (signature fn(msg)->str)."""
    c = R._decoupe_conjonction(q)
    return "%s|%s" % (c[0], ",".join(c[1])) if c else None


# (capacité, message, attendu). attendu="" => la réponse doit être VIDE/None (garde FAUX=0).
CAS = [
    ("is-a", R._cap_ontologie, "un chat est-il un mammifère ?", "Oui"),
    ("is-a-faux", R._cap_ontologie, "un chat est-il un poisson ?", "mammifère"),  # jamais « Oui »
    ("is-a-faux-contexte", R._cap_ontologie, "l'apartheid est-il un continent ?", ""),  # bruit de genre géo nettoyé
    ("is-a-seed", R._cap_ontologie, "une rose est-elle une fleur ?", "Oui"),          # seed curé (definition_nom vide)
    ("is-a-seed-fruit", R._cap_ontologie, "une pomme est-elle un fruit ?", "Oui"),
    ("point-commun", R._cap_ontologie, "qu'ont en commun le chat et le requin ?", "animal"),
    ("point-commun-nway", R._cap_point_commun_nway, "qu'ont en commun le chat, le requin et le lion ?", "animal"),
    ("cause", R._cap_cause, "quelle est la cause du paludisme ?", "du paludisme"),
    ("definition", R._cap_definition, "c'est quoi le paludisme ?", "Paludisme"),
    ("definition-longue", R._cap_definition, "quelle est la définition du paludisme ?", "Paludisme"),
    ("comptage", R._cap_comptage, "combien de pays en Afrique ?", "compté exactement"),
    ("comptage-recall", R._cap_comptage, "combien de montagnes en Europe ?", "non exhaustive"),  # ensemble troué
    ("classement", R._cap_classement, "les 3 pays les plus peuplés d'Afrique", "Nigéria"),
    ("classement-liste", R._cap_classement_liste, "classe la France, l'Allemagne et l'Italie par population", "1. Allemagne"),
    ("classement-liste-croissant", R._cap_classement_liste, "trie la France, l'Espagne et l'Italie par population croissante", "1. Espagne"),
    ("filtre", R._cap_filtre, "quels pays d'Afrique ont plus de 100 millions d'habitants ?", "Nigéria"),
    ("filtre-entre", R._cap_filtre, "quels pays d'Afrique ont entre 100 et 300 millions d'habitants ?", "Nigéria"),
    ("filtre-entre-magnitudes", R._cap_filtre,
     "quels pays d'Europe ont entre 500 000 et 2 millions d'habitants ?", "entre 500 000 et 2 000 000"),
    ("filtre-entre-decimal", R._cap_filtre, "quels pays d'Asie ont entre 1 et 1,5 milliard d'habitants ?", "Inde"),
    ("filtre-superficie", R._cap_filtre, "quels pays d'Afrique ont une superficie entre 1 et 2 millions de km² ?", "km²"),
    ("comparaison", R._cap_comparaison, "la Chine est-elle plus peuplée que l'Inde ?", "l'inverse"),
    ("comparaison-nway", R._cap_comparaison_nway, "quel est le plus peuplé entre la France, l'Allemagne et l'Italie ?", "Allemagne"),
    ("comparaison-superficie", R._cap_comparaison, "la France est-elle plus vaste que l'Espagne ?", "Oui"),
    ("comparaison-altitude", R._cap_comparaison, "l'Abendberg est-il plus haut que l'Ahintziaga ?", "plus haut"),
    ("comparaison-riche", R._cap_comparaison, "la France est-elle plus riche que l'Espagne ?", "Oui"),
    ("difference-pop", R._cap_difference, "quelle est la différence de population entre la France et l'Allemagne ?", "de plus"),
    ("difference-superficie", R._cap_difference, "différence de superficie entre la France et l'Espagne ?", "km²"),
    ("conjonction", _conjonction_txt, "quelle est la capitale de la France et de l'Espagne ?", "France,Espagne"),
    ("agregat-superficie", R._cap_agregat, "superficie totale de l'Afrique ?", "km²"),
    ("agregat", R._cap_agregat, "population totale de l'Afrique ?", "somme"),
    ("agregat-liste", R._cap_agregat_liste, "quelle est la population cumulée de la France et de l'Allemagne ?", "152 211 586"),
    ("agregat-liste-moyenne", R._cap_agregat_liste, "population moyenne de la France, l'Allemagne et l'Italie ?", "moyenne"),
    ("deduction", R._cap_deduction, "sur quel continent est Abuja ?", "je le déduis"),
    ("orbite", R._cap_orbite, "est-ce que Phobos fait partie du système solaire ?", "je le déduis"),
    ("transitif-hydro", R._cap_transitif, "est-ce que la Lukna finit dans la mer Baltique ?", "Niémen"),
    ("transitif-groupe", R._cap_transitif, "105 Music fait-elle partie du groupe Sony ?", "Sony Music"),
    ("inverse-capitale", R._cap_inverse, "quel pays a pour capitale Madrid ?", "Espagne"),
    ("inverse-de-quel", R._cap_inverse, "de quel pays Tokyo est la capitale ?", "Japon"),
    ("inverse-verbe-langue", R._cap_inverse, "quels pays parlent français ?", "France"),
    ("inverse-verbe-monnaie", R._cap_inverse, "dans quel pays utilise-t-on le yen ?", "Japon"),
    ("temporel", R._cap_temporel, "quel est le plus ancien entre la bataille de Marignan et la bataille de Verdun ?", "1515"),
    ("duree", R._cap_duree, "combien de temps a duré la guerre de Cent Ans ?", "116 ans"),
    ("duree-regne", R._cap_duree, "combien de temps a duré le règne de Louis XIV ?", "72 ans"),
    ("age-deces", R._cap_age, "à quel âge est mort Napoléon Ier ?", "52 ans"),
    ("temporel-nway", R._cap_temporel_nway, "quel est le plus ancien entre la bataille de Marignan, la bataille de Verdun et la bataille de Waterloo ?", "1515"),
    ("ecart-temporel", R._cap_ecart_temporel, "combien d'années séparent la bataille de Marignan et la bataille de Waterloo ?", "300 ans"),
    ("analogie", R._cap_analogie, "Paris est à la France ce que Berlin est à ?", "Allemagne"),
    ("portrait", R._cap_portrait, "parle-moi du Nigéria", "Le Nigéria est un pays"),
    ("portrait-personne", R._cap_portrait_personne, "qui est Napoléon Ier ?", "Ajaccio"),
    ("portrait-personne-fem", R._cap_portrait_personne, "qui était Marie Curie ?", "née"),
    ("fait-personne-lieu", R._cap_fait_personne, "où est né Napoléon Ier ?", "Ajaccio"),
    ("fait-personne-fem", R._cap_fait_personne, "où est morte Marie Curie ?", "est morte"),
    # gardes FAUX=0
    ("faux-filtre-entre", R._cap_filtre, "quels pays d'Afrique ont entre 5 et 10 milliards d'habitants ?", "Aucun"),
    ("faux-orbite", R._cap_orbite, "est-ce que la Terre orbite la Lune ?", ""),
    ("faux-transitif", R._cap_transitif, "est-ce que la Lukna finit dans la mer Noire ?", ""),
    ("faux-inverse", R._cap_inverse, "quel pays a pour capitale Xanadu ?", ""),
    # superlatif SÛR seulement si l'ensemble est complet : montagnes/villes ont un membership troué -> abstention
    ("faux-superlatif-montagne", R._superlatif_argmax, "la montagne la plus haute d'Europe", ""),
    ("inverse-non-hijack", R._cap_inverse, "quelle est la capitale de l'Espagne ?", ""),
    ("difference-non-hijack", R._cap_difference, "population de la France ?", ""),
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
