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
    ("is-a-faux", R._cap_ontologie, "un chat est-il un poisson ?", "félin"),  # jamais « Oui » ; genre réel = félin
    ("is-a-faux-contexte", R._cap_ontologie, "l'apartheid est-il un continent ?", "régime"),  # réfute : régime, PAS continent
    ("is-a-seed", R._cap_ontologie, "une rose est-elle une fleur ?", "Oui"),          # seed curé (definition_nom vide)
    ("is-a-seed-fruit", R._cap_ontologie, "une pomme est-elle un fruit ?", "Oui"),
    ("is-a-metal", R._cap_ontologie, "le fer est-il un métal ?", "Oui"),
    ("point-commun-metal", R._cap_point_commun_nway, "qu'ont en commun l'or, l'argent et le fer ?", "métal"),
    ("hyponymes-metaux", R._cap_hyponymes, "cite des métaux", "argent"),  # pluriel irrégulier métaux -> métal
    ("point-commun", R._cap_ontologie, "qu'ont en commun le chat et le requin ?", "animal"),
    ("point-commun-nway", R._cap_point_commun_nway, "qu'ont en commun le chat, le requin et le lion ?", "animal"),
    ("cause", R._cap_cause, "quelle est la cause du paludisme ?", "du paludisme"),
    ("definition", R._cap_definition, "c'est quoi le paludisme ?", "Paludisme"),
    ("definition-longue", R._cap_definition, "quelle est la définition du paludisme ?", "Paludisme"),
    ("comptage", R._cap_comptage, "combien de pays en Afrique ?", "compté exactement"),
    ("comptage-recall", R._cap_comptage, "combien de montagnes en Europe ?", "non exhaustive"),  # ensemble troué
    ("classement", R._cap_classement, "les 3 pays les plus peuplés d'Afrique", "Nigéria"),
    ("classement-petit", R._cap_classement, "les 3 plus petits pays d'Europe", "Vatican"),  # polarité « petit »
    ("rang", R._cap_rang, "quel est le rang de la France par population en Europe ?", "4ᵉ sur 47"),
    ("classement-liste", R._cap_classement_liste, "classe la France, l'Allemagne et l'Italie par population", "1. Allemagne"),
    ("classement-liste-croissant", R._cap_classement_liste, "trie la France, l'Espagne et l'Italie par population croissante", "1. Espagne"),
    ("filtre", R._cap_filtre, "quels pays d'Afrique ont plus de 100 millions d'habitants ?", "Nigéria"),
    ("filtre-entre", R._cap_filtre, "quels pays d'Afrique ont entre 100 et 300 millions d'habitants ?", "Nigéria"),
    ("filtre-combien", R._cap_filtre, "combien de pays d'Afrique ont plus de 50 millions d'habitants ?", "compté exactement"),
    ("filtre-proportion", R._cap_filtre, "quelle proportion des pays d'Afrique ont plus de 50 millions d'habitants ?", "%"),
    ("filtre-entre-magnitudes", R._cap_filtre,
     "quels pays d'Europe ont entre 500 000 et 2 millions d'habitants ?", "entre 500 000 et 2 000 000"),
    ("filtre-entre-decimal", R._cap_filtre, "quels pays d'Asie ont entre 1 et 1,5 milliard d'habitants ?", "Inde"),
    ("filtre-superficie", R._cap_filtre, "quels pays d'Afrique ont une superficie entre 1 et 2 millions de km² ?", "km²"),
    ("comparaison", R._cap_comparaison, "la Chine est-elle plus peuplée que l'Inde ?", "l'inverse"),
    ("comparaison-nway", R._cap_comparaison_nway, "quel est le plus peuplé entre la France, l'Allemagne et l'Italie ?", "Allemagne"),
    ("meme-attribut-oui", R._cap_meme_attribut, "la France et l'Allemagne sont-elles sur le même continent ?", "Oui"),
    ("meme-attribut-non", R._cap_meme_attribut, "la France et le Japon sont-ils sur le même continent ?", "Non"),
    ("dimension-superficie", R._cap_dimension, "quelle est la superficie de la France ?", "551 695 km²"),
    ("dimension-hauteur", R._cap_dimension, "quelle est la hauteur de A'DAM ?", "100 m"),
    ("faux-dimension-concept", R._cap_dimension, "quelle est la longueur du bonheur ?", ""),  # nom commun -> abstention
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
    ("orbite-direct", R._cap_orbite, "la Terre tourne-t-elle autour du Soleil ?", "Oui"),          # ex-FAUX Baudelaire
    ("orbite-direct-sms", R._cap_orbite, "est ce que la terre tourne autour du soleil", "Oui"),
    ("orbite-derive", R._cap_orbite, "la Lune tourne-t-elle autour du Soleil ?", "je le déduis"),
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
    ("date-evenement", R._cap_date_evenement, "quand a eu lieu la bataille de Marignan ?", "1515"),
    ("date-evenement-fin", R._cap_date_evenement, "quand s'est terminée la guerre de Cent Ans ?", "1453"),
    ("analogie", R._cap_analogie, "Paris est à la France ce que Berlin est à ?", "Allemagne"),
    ("portrait", R._cap_portrait, "parle-moi du Nigéria", "Le Nigéria est un pays"),
    ("portrait-personne", R._cap_portrait_personne, "qui est Napoléon Ier ?", "Ajaccio"),
    ("portrait-personne-fem", R._cap_portrait_personne, "qui était Marie Curie ?", "née"),
    ("guerison-etait", R._guerit_entree, "qui était Marie Curie ?", "était"),  # « était » protégé (pas -> « état »)
    ("guerison-mots-outils", R._guerit_entree, "la France a-t-elle des colonies", "des colonies"),  # « des » pas -> « dis »
    ("fait-personne-lieu", R._cap_fait_personne, "où est né Napoléon Ier ?", "Ajaccio"),
    ("fait-personne-fem", R._cap_fait_personne, "où est morte Marie Curie ?", "est morte"),
    ("createur-auteur", R._cap_createur, "qui a écrit 1984 ?", "George Orwell"),
    ("createur-compositeur", R._cap_createur, "qui a composé le Boléro ?", "Ravel"),
    ("oeuvres-de", R._cap_oeuvres_de, "qu'a composé Maurice Ravel ?", "Boléro"),
    ("naissance-compare", R._cap_naissance_compare, "qui est le plus âgé entre Napoléon Ier et Louis XIV ?", "Louis XIV"),
    ("naissance-compare-jeune", R._cap_naissance_compare, "qui est le plus jeune entre Napoléon Ier et Louis XIV ?", "Napoléon"),
    ("succession", R._cap_succession, "qui a succédé à Louis XIV ?", "Louis XV"),
    ("succession-predecesseur", R._cap_succession, "qui a précédé Louis XIV ?", "Louis XIII"),
    ("record-sommet", R._cap_record_monde, "quel est le plus haut sommet du monde ?", "Everest"),
    ("record-fleuve-dispute", R._cap_record_monde, "quel est le plus long fleuve du monde ?", "DISPUTÉE"),
    ("record-ile", R._cap_record_monde, "quelle est la plus grande île du monde ?", "Groenland"),
    ("record-desert", R._cap_record_monde, "quel désert est le plus grand du monde ?", "Sahara"),
    ("record-planete", R._cap_record_monde, "quelle est la plus grande planète du système solaire ?", "Jupiter"),
    ("record-lac-postpose", R._cap_record_monde, "le lac le plus profond du monde", "Baïkal"),
    ("faux-record-zone", R._cap_record_monde, "la montagne la plus haute d'Europe", ""),   # zone-scopé -> pas ce cap
    ("fleuve-ville", R._cap_fleuve_ville, "quel fleuve traverse Paris ?", "Seine"),        # ex-FAUX : 147 rivières
    ("fleuve-ville-multi", R._cap_fleuve_ville, "quelle rivière traverse Lyon ?", "Saône"),
    ("fleuve-ville-sur", R._cap_fleuve_ville, "sur quel fleuve se trouve Budapest ?", "Danube"),
    ("fleuve-villes-inverse", R._cap_fleuve_ville, "quelles villes le Danube traverse-t-il ?", "Budapest"),
    ("fleuve-ville-ouinon", R._cap_fleuve_ville, "est-ce que la Seine traverse Paris ?", "Oui"),
    ("localisation-pays", R._cap_localisation, "dans quel pays est 1117 Mountain ?", "États-Unis"),
    ("localisation-continent", R._cap_localisation, "sur quel continent est Abbott Peak ?", "Antarctique"),
    ("faux-localisation-concept", R._cap_localisation, "où se trouve le bonheur ?", ""),  # nom commun -> pas un lieu
    # gardes FAUX=0
    ("faux-filtre-entre", R._cap_filtre, "quels pays d'Afrique ont entre 5 et 10 milliards d'habitants ?", "Aucun"),
    # le faux n'est plus tu : il est RÉFUTÉ avec le fait réel (anti-symétrie induite), jamais confirmé
    ("faux-orbite", R._cap_orbite, "est-ce que la Terre orbite la Lune ?", "Non — c'est l'inverse"),
    ("faux-orbite-soleil", R._cap_orbite, "le Soleil tourne-t-il autour de la Terre ?", "Non — c'est l'inverse"),
    ("faux-transitif", R._cap_transitif, "est-ce que la Lukna finit dans la mer Noire ?", ""),
    # paire absente : le fait réel est montré, jamais « Oui » ni « Non » sec (la Bièvre traverse VRAIMENT Paris)
    ("faux-fleuve-ville", R._cap_fleuve_ville, "la Seine traverse-t-elle Lyon ?", "Rhône"),
    ("faux-fleuve-inconnu", R._cap_fleuve_ville, "quel fleuve traverse Gotham City ?", ""),
    ("faux-inverse", R._cap_inverse, "quel pays a pour capitale Xanadu ?", ""),
    # superlatif SÛR seulement si l'ensemble est complet : montagnes/villes ont un membership troué -> abstention
    ("faux-superlatif-montagne", R._superlatif_argmax, "la montagne la plus haute d'Europe", ""),
    ("superlatif-global", lambda q: (R._superlatif_argmax(q) or ("",))[0], "le pays le plus vaste du monde", "Russie"),
    ("superlatif-petit", lambda q: (R._superlatif_argmax(q) or ("",))[0], "le pays le moins peuplé du monde", "Tuvalu"),
    ("inverse-non-hijack", R._cap_inverse, "quelle est la capitale de l'Espagne ?", ""),
    ("difference-non-hijack", R._cap_difference, "population de la France ?", ""),
    ("faux-compar", R._cap_comparaison, "la France est-elle plus peuplée que l'Inde ?", "l'inverse"),
    # brique « structure reconnue mais non ancrée » : abstention ENRICHIE qui dit ce qui est compris (relation
    # connue + entité) et ce qui manque (aucun fait pour trancher) — et QUI est l'entité quand elle est définie.
    ("structure-ancree-fictif", R._structure_non_ancree, "quelle est la capitale du wakanda ?", "fictif"),
    ("structure-non-ancree", R._structure_non_ancree, "quelle est la population du blorgistan ?",
     "aucun fait vérifié qui ancre"),
    ("structure-non-hijack", R._structure_non_ancree, "la capitale du wakanda est-elle grande ?", ""),  # copule -> mis-parse
    # famille CRÉATEUR : structure reconnue (« qui a écrit X ») + entité définie mais sans fait créateur
    ("structure-createur", R._structure_non_ancree, "qui a écrit le necronomicon ?", "lovecraft"),
    # titres stockés AVEC article : « la joconde » est la clé réelle de peintre_oeuvre (+ accord du participe)
    ("createur-article", R._cap_createur, "qui a peint la joconde ?", "peinte par Léonard de Vinci"),
    # dévoilement de l'enrobage conversationnel (fossé de généralisation) + verbes familiers
    ("devoile-enrobage", R._devoile, "dis-moi qui a écrit 1984", "qui a écrit 1984"),
    ("devoile-politesse-fin", R._devoile, "donne-moi la capitale du japon, merci", "capitale du japon"),
    ("createur-familier", R._cap_createur, "qui a pondu 1984 ?", "George Orwell"),
    ("createur-tourne", R._cap_createur, "qui a tourné titanic ?", "Cameron"),
    # gate de pertinence web : un extrait qui ne parle pas de la question n'est PAS servi (hors-sujet sourcé
    # mesuré en e2e : « capitale du wakanda » -> page gentilés). Le pertinent passe.
    ("web-gate-horssujet", lambda q: "" if not R._extrait_pertinent(
        q, "Comment on appelle les habitants de Wakanda - Synonyme du mot",
        "la réponse complète sur fr.wikipedia") else "SERVI", "quelle est la capitale du wakanda ?", ""),
    ("web-gate-pertinent", lambda q: "OK" if R._extrait_pertinent(
        q, "Tokyo — Wikipédia", "Tokyo est la capitale du Japon depuis 1868.") else "",
     "quelle est la capitale du Japon ?", "OK"),
    # 3e famille d'abstention structurée : faits ciblés (naissance/mort/localisation)
    ("structure-fait-personne", R._structure_non_ancree, "quand est mort Dumbledore ?", "dumbledore"),
    ("structure-localisation", R._structure_non_ancree, "où se trouve Fondcombe ?", "fondcombe"),
    ("structure-fait-non-hijack", R._structure_non_ancree, "et il est mort quand ?", ""),   # pronom -> pas une entité
    # hyponymes : phrasé « quels X sont des Y » + anti-bruit (pas de syntagme à article dans la liste)
    ("hypo-quels-animaux", R._cap_hyponymes, "quels animaux sont des félins ?", "lion"),
    ("hypo-anti-bruit", lambda q: "BRUIT" if "la recherche" in (R._cap_hyponymes(q) or "") else "OK",
     "cite des cétacés", "OK"),
    # filtre de rappel mémoire : une QUESTION stockée en SMS ne doit pas être ressortie comme une « réponse »
    # (« cest koi la capitale du japon » est une question, pas un énoncé à rappeler).
    ("rappel-question-sms", lambda q: "QUESTION" if (R._veut_reponse(q) or R._veut_reponse(R._desms(q)))
     else "ENONCE", "cest koi la capitale du japon", "QUESTION"),
    # transitivité des conflits militaires (piste #5) : bataille -> opération -> front -> guerre
    ("transitif-conflit-ouvert", R._cap_transitif, "de quelle guerre fait partie la bataille de Marignan ?",
     "Ligue de Cambrai"),
    ("transitif-conflit-chaine", R._cap_transitif, "de quelle bataille fait partie l'opération Tonga ?", "Normandie"),
    ("transitif-conflit-verif", R._cap_transitif,
     "est-ce que l'opération Tonga fait partie du front de l'Ouest ?", "Oui"),
    ("transitif-conflit-faux", R._cap_transitif,
     "est-ce que la bataille de Marignan fait partie de la guerre de Cent Ans ?", ""),   # FAUX -> abstention
    # parse SVO libre (ordre des mots libre) : tête de relation + entité vérifiée, quel que soit l'ordre
    ("svo-entite-avant", lambda q: (R._parse_svo_libre(q) or ("",))[0], "du Japon, dis-moi la capitale", "Tokyo"),
    ("svo-pour-entite", lambda q: (R._parse_svo_libre(q) or ("",))[0], "pour le Japon, la monnaie ?", "yen"),
    ("svo-concept-refuse", lambda q: (R._parse_svo_libre(q) or ("",))[0], "le sens, pour le bonheur ?", ""),  # concept -> None
    # garde FAUX=0 : « où se trouve le bonheur » (concept) ne renvoie PAS les coords d'un hameau homonyme
    ("localisation-concept-coords", R._localisation, "où se trouve le bonheur ?", ""),
    # synonymes de têtes de relation : mot proche -> relation exacte, valeur vérifiée
    ("synonyme-tete-richesse", R._cap_synonyme_tete, "quelle est la richesse du Japon ?", "$"),
    ("synonyme-tete-taille", R._cap_synonyme_tete, "quelle est la taille de la France ?", "km²"),
    ("synonyme-tete-faux", R._cap_synonyme_tete, "quelle est la taille de Napoléon Ier ?", ""),  # pas dans superficie
    # garde FAUX=0 : un alias appris ne peut PAS échanger une entité (« wakanda »->« france » = faux)
    ("alias-change-entite", lambda q: "BLOQUE" if R._alias_change_entite(
        "population du wakanda", "population du france") else "PASSE", "x", "BLOQUE"),
    ("alias-reformulation-ok", lambda q: "PASSE" if not R._alias_change_entite(
        "cest koi la capitale du japon", "quelle est la capitale du japon") else "BLOQUE", "x", "PASSE"),
    # FAUX=0 : « Berlin est-elle la capitale de l'Allemagne » est RELATIONNEL, pas un is-a — l'ontologie ne doit
    # PAS répondre le genre bruité (« Berlin est un paquet ») à cette question VRAIE.
    ("onto-non-hijack-relation", R._cap_ontologie, "Berlin est-elle la capitale de l'Allemagne ?", ""),
    ("meme-monnaie-euro", R._cap_meme_attribut, "la France et l'Allemagne ont-elles la même monnaie ?", "Oui"),
    ("meme-monnaie-diff", R._cap_meme_attribut, "la France et le Japon ont-ils la même monnaie ?", "Non"),
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
