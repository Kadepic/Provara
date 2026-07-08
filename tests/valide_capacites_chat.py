# -*- coding: utf-8 -*-
"""VALIDE les capacités OUTILS câblées au chat (audit orphelines 2026-07-03) : grammaire, conjugaison, graphique,
distance, invention, audit de code. FAUX=0 : chaque handler répond dans son périmètre et s'abstient (None)
hors périmètre — jamais de réponse inventée, jamais de détournement d'une question normale.

Léger : on teste les handlers de repond.py directement. Les handlers LOURDS (distance/invention/audit) sont
vérifiés surtout pour leur SÛRETÉ de routage (None sur entrée non concernée) ; leur chemin complet est couvert
e2e par ailleurs."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import repond as R

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — GRAMMAIRE —
r = R._cap_grammaire("quelle est la nature du mot chat ?")
check(r and "nom" in r, "grammaire : nature de 'chat' -> nom")
r = R._cap_grammaire("nature grammaticale de rapidement")
check(r and "adverbe" in r, "grammaire : 'rapidement' -> adverbe")
r = R._cap_grammaire("analyse grammaticale : le chien dort")
check(r and "Type" in r, "grammaire : analyse de phrase")
check(R._cap_grammaire("quelle est la capitale de la France ?") is None, "grammaire : ne capte PAS une question factuelle")
r = R._cap_grammaire("nature du mot xyzqwerty")
check(r and ("pas certain" in r or "deviner" in r), "grammaire : mot inconnu -> abstention honnête")

# — CONJUGAISON —
r = R._cap_conjugaison("conjugue le verbe parler")
check(r and "parlons" in r and "parlent" in r, "conjugaison : parler au présent")
r = R._cap_conjugaison("conjugaison de finir")
check(r and "finissons" in r, "conjugaison : finir")
r = R._cap_conjugaison("conjugue manger")
check(r and ("abst" in r.lower() or "périmètre" in r or "perimetre" in r), "conjugaison : verbe hors périmètre -> abstention honnête")
check(R._cap_conjugaison("quelle heure est-il ?") is None, "conjugaison : ne capte pas une question quelconque")

# — GRAPHIQUE —
r = R._cap_graphique("trace un graphique en barres de 3, 5, 8, 2")
check(r and r.startswith("<svg"), "graphique : barres -> SVG")
r = R._cap_graphique("trace la courbe de 1, 4, 9, 16")
check(r and r.startswith("<svg"), "graphique : courbe -> SVG")
check(R._cap_graphique("trace de la route") is None, "graphique : pas de nombres -> None")
check(R._cap_graphique("quelle est la population du Japon ?") is None, "graphique : question sans intention graphique -> None")

# — DEMANDE CRÉATIVE OUVERTE (vécu Yohan 2026-07-06 : « invente quelque chose » -> fausse correction + web Reverso) —
r = R._cap_creer_ouvert("je voudrais inventer quelque chose pour un vrai besoin, as-tu des idées ?")
check(r is not None and "je ne bluffe jamais" in r and "besoin" in r.lower(),
      "créatif ouvert -> réponse honnête + redirection vers le vrai moteur de besoin (jamais une idée fabriquée)")
r = R._cap_creer_ouvert("qu'est-ce que je peux créer pour la population ?")
check(r is not None and "concret" in r.lower(), "« qu'est-ce que je peux créer » capté -> orientation honnête")
check(R._cap_creer_ouvert("comment rafraîchir une pièce sans climatiseur ?") is None,
      "besoin CONCRET « X sans Y » -> laissé au vrai moteur d'invention (pas capté par le handler ouvert)")
check(R._cap_creer_ouvert("quelle est la capitale de la France ?") is None, "question factuelle -> None")
# garde did-you-mean : un mot VALIDE (« inventer », infinitif) n'est JAMAIS proposé en correction
check(R._suggere_type("je voudrais inventer quelque chose") is None,
      "did-you-mean : « inventer » est un vrai mot -> aucune correction proposée (garde lexique embarqué)")
check(R._suggere_type("quel flauve traverse paris") == ("flauve", "fleuve"),
      "did-you-mean : une VRAIE faute (« flauve ») reste corrigée")

# — INVENTION (léger : besoin.py) —
r = R._cap_invention("comment rafraîchir une pièce sans climatiseur ?")
check(r and ("BESOIN" in r or "but réel" in r or "but reel" in r.lower()), "invention : reformulation physique du besoin")
check(R._cap_invention("quelle est la capitale de l'Italie ?") is None, "invention : ne capte pas une question factuelle")
check(R._cap_invention("comment dire bonjour sans accent ?") is None, "invention : acte de LANGAGE (« dire ») -> None (pipeline continue)")
check(R._cap_invention("comment écrire mon nom sans faute ?") is None, "invention : acte de langage (« écrire ») -> None")
r = R._cap_invention("comment conserver des aliments sans frigo ?")
check(r is not None and "catalogue" in r and "Carnot" in r,
      "invention : besoin PHYSIQUE hors catalogue -> amplification honnête (méthode + limite dure), plus jamais « internet coupé »")

# — AUDIT CODE : sûreté de routage (None hors périmètre) —
check(R._cap_audit_code("bonjour comment vas-tu ?") is None, "audit code : message normal -> None")
check(R._cap_audit_code("parle-moi du code de la route") is None, "audit code : 'code' sans bloc -> None")

# — DISTANCE : sûreté de routage —
check(R._cap_distance("bonjour") is None, "distance : message normal -> None")

# — SITE NOMMÉ (vécu 2026-07-06 : « regarde yohanfauck.fr » -> clarification générique) —
import os as _os
import veille_structure as _VS_site
check(R._cap_site("bonjour comment vas-tu ?") is None, "site : message sans domaine -> None")
check(R._cap_site("relance maj.py stp") is None, "site : « maj.py » n'est PAS un domaine (TLD fermés)")
_web_avant = _os.environ.get("IA_WEB")
_apercu_avant = _VS_site.apercu_site
try:
    _os.environ["IA_WEB"] = "0"
    r = R._cap_site("peux-tu regarder le site yohanfauck.fr ?")
    check(r is not None and "Internet est coupé" in r and "yohanfauck.fr" in r,
          "site + web OFF -> refus honnête actionnable (bouton 🌐), jamais une invention")
    _os.environ["IA_WEB"] = "1"
    _VS_site.apercu_site = lambda cible, timeout=8: ("Yohan Fauck — Portfolio",
                                                     "Développeur, moteurs de raisonnement vérifiés.",
                                                     "https://yohanfauck.fr")
    r = R._cap_site("peux-tu regarder le site yohanfauck.fr et me dire ce que tu en penses ?")
    check(r is not None and "yohanfauck.fr" in r and "Portfolio" in r and "rapporté" in r.lower(),
          "site + web ON -> rapport ATTRIBUÉ (domaine, titre, extrait, lien)")
    check(r is not None and "jugement subjectif" in r,
          "« ce que tu en penses » -> cadrage honnête (on cite la page, on ne juge pas)")
    _VS_site.apercu_site = lambda cible, timeout=8: None
    r = R._cap_site("va voir https://site-injoignable.example/page")
    check(r is not None and "pas réussi à lire" in r, "site injoignable -> aveu honnête, jamais deviné")
finally:
    _VS_site.apercu_site = _apercu_avant
    if _web_avant is None:
        _os.environ.pop("IA_WEB", None)
    else:
        _os.environ["IA_WEB"] = _web_avant

# — « MON AVIS » COMPARATIF (réflexion outillée : Pareto / vote des critères / sensibilité — Yohan 2026-07-06) —
check(R._cap_avis("quelle est la capitale de la France ?") is None, "avis : lookup factuel -> None")
check(R._cap_avis("la France est-elle plus grande que l'Espagne ?") is None,
      "avis : comparaison factuelle (plus/moins) -> None (le cap comparaison garde la main)")
_valeur_avant = R._valeur_attr
_FAUX_FAITS = {("superficie", "aaa"): 10, ("superficie", "bbb"): 5,
               ("population_pays", "aaa"): 1, ("population_pays", "bbb"): 2,
               ("pib_pays", "aaa"): 1, ("pib_pays", "bbb"): 2}
try:
    R._valeur_attr = lambda e, rel: ((_FAUX_FAITS.get((rel, e)), e.upper())
                                     if (rel, e) in _FAUX_FAITS else (None, None))
    r = R._cap_avis("tu préfères aaa ou bbb ?")
    check(r is not None and "Mon avis : BBB" in r and "2 critère(s) sur 3" in r,
          "avis : vote majoritaire des critères, valeurs montrées")
    check(r is not None and "BASCULE" in r and "superficie" in r,
          "avis : SENSIBILITÉ affichée (le critère qui ferait changer d'avis)")
    _FAUX_FAITS[("pib_pays", "bbb")] = 1                         # pib ex æquo -> vote 1–1
    r = R._cap_avis("tu préfères aaa ou bbb ?")
    check(r is not None and "SUSPENDS" in r, "avis : égalité au vote -> avis SUSPENDU (ton critère tranche)")
    _FAUX_FAITS[("population_pays", "bbb")] = 0.5                # aaa mène partout -> dominance
    _FAUX_FAITS[("pib_pays", "bbb")] = 0.5
    r = R._cap_avis("tu préfères aaa ou bbb ?")
    check(r is not None and "DOMINANCE DE PARETO" in r and "Mon avis : AAA" in r,
          "avis : dominance de Pareto -> avis ROBUSTE (aucune pondération ne peut inverser)")
    for k in list(_FAUX_FAITS):
        if k[0] != "superficie":
            del _FAUX_FAITS[k]                                   # un seul critère -> avis MINCE assumé
    r = R._cap_avis("tu préfères aaa ou bbb ?")
    check(r is not None and "MINCE" in r, "avis : un seul critère mesurable -> avis annoncé MINCE, jamais gonflé")
    # — LE CRITÈRE DE L'UTILISATEUR (le « donne-moi ton critère n°1 » n'est PLUS une impasse) —
    _FAUX_FAITS.update({("population_pays", "aaa"): 1, ("population_pays", "bbb"): 2})
    check(R._cap_avis_critere("la superficie", "cv-avis") is None, "critère : aucun avis en attente -> None")
    R._cap_avis("tu préfères aaa ou bbb ?", "cv-avis")
    r = R._cap_avis_critere("mon critère n°1 est la superficie", "cv-avis")
    check(r is not None and "TON critère (superficie)" in r and "AAA" in r,
          "critère nommé au tour suivant -> RE-TRANCHE sur ce critère (valeurs montrées)")
    check(R._cap_avis_critere("la superficie", "cv-avis") is None, "état consommé une seule fois")
    R._cap_avis("tu préfères aaa ou bbb ?", "cv-avis")
    check(R._cap_avis_critere("quelle est la capitale de la France ?", "cv-avis") is None,
          "message sans rapport -> None (pipeline normal, l'état reste)")
    r = R._cap_avis_critere("mon critère c'est le climat", "cv-avis")
    check(r is not None and "pas de mesure" in r and "superficie" in r,
          "critère NON mesuré nommé explicitement -> aveu honnête + critères disponibles")
    # — AVIS À 3+ CANDIDATS (Condorcet/Borda — choix_social câblé au conversationnel) —
    _FAUX_FAITS.clear()
    _FAUX_FAITS.update({("superficie", "aaa"): 3, ("superficie", "bbb"): 2, ("superficie", "ccc"): 1,
                        ("population_pays", "aaa"): 30, ("population_pays", "bbb"): 20, ("population_pays", "ccc"): 10,
                        ("pib_pays", "aaa"): 5, ("pib_pays", "bbb"): 9, ("pib_pays", "ccc"): 1})
    r = R._cap_avis("quelle est la meilleure destination entre aaa, bbb et ccc ?", "cv-multi")
    check(r is not None and "CONDORCET" in r and "Mon avis : AAA" in r,
          "3 candidats -> gagnant de Condorcet (bat chacun en duel, critères = électeurs)")
    check(r is not None and "AAA 3 > BBB 2 > CCC 1" in r.replace("km²", "").replace("  ", " "),
          "classement complet montré par critère (valeurs vérifiées)")
    r = R._cap_avis_critere("mon critère n°1 est le PIB", "cv-multi")
    check(r is not None and "BBB" in r and "mon avis suit ton critère : BBB" in r,
          "multi : le critère de l'utilisateur re-tranche (classement complet sur CE critère)")
finally:
    R._valeur_attr = _valeur_avant

# — VOYELLES / CONSONNES (vague 17) : comptage de lettres, PAS le concept « consonne » (37 hyponymes, FAUX vécu) —
r = R._cap_texte("combien de voyelles dans le mot bonjour")
check(r is not None and "3 voyelle" in r, "voyelles de bonjour -> 3")
r = R._cap_texte("le mot chien contient combien de consonnes")
check(r is not None and "3 consonne" in r, "consonnes de chien -> 3 (« contient » plus corrigé en « continent »)")
check("continent" not in R._guerit_entree("le mot chien contient combien de consonnes"),
      "le guérisseur ne corrige PLUS « contient » en « continent »")

# — CONTINUATION heure (indépendante des datasets) : « et à New York ? » après l'heure de Tokyo —
import conversation as _cvB
_memB2 = _cvB.MemoireConversation(racine=None)
R.repond(_memB2, "cont-h", "quelle heure est-il à Tokyo ?", pleine=True)
rh = R.repond(_memB2, "cont-h", "et à New York ?", pleine=True)
check(rh is not None and "New York" in rh and not rh.startswith("Il est"),
      "« et à New York ? » après l'heure de Tokyo -> l'heure de New York (continuation)")

# — GÉNÉRATION D'ANAGRAMMES (dictionnaire embarqué : mots réels, jamais des lettres mélangées inventées) —
# checks POSITIFS seulement si le dictionnaire est chargé (la suite tourne sans LECTEUR_DATASETS_DIR).
if os.path.exists(os.path.join(R._DOSSIER_LECTEUR, "definition_nom.jsonl")):
    r = R._cap_anagramme("anagramme de chien")
    check(r is not None and "niche" in r and "dictionnaire" in r, "anagramme de chien -> niche (mot réel, sourcé)")
    r = R._cap_anagramme("anagramme de xyzzy")
    check(r is not None and r.startswith("Aucune anagramme") and "verbes" in r,
          "aucune trouvée -> aveu honnête + limite du dictionnaire DITE (noms seulement)")
check(R._cap_anagramme("l'anagramme de la phrase entière ne doit pas matcher") is None,
      "une phrase entière ne déclenche pas la génération (un seul mot)")

# — RAPPELS-TÂCHES (« rappelle-moi de X » partait en cascade factuelle -> « pas l'information », préexistant) —
r = R._cap_rappel("rappelle-moi d'acheter du pain")
check(r == "C'est noté : acheter du pain. Demande-moi « qu'est-ce que je devais faire ? » et je te le rappelle.",
      "rappel-tâche -> accusé + promesse RE-SERVABLE (pas d'alarme promise)")
r = R._cap_rappel("rappelle-moi demain d'appeler le médecin")
check(r is not None and "je n'ai pas d'alarme" in r and "(demain)" in r,
      "moment nommé -> HONNÊTETÉ : pas d'alarme, re-servi à la demande seulement")
check(R._cap_rappel("rappelle-moi la capitale de la France") is None,
      "« rappelle-moi LA capitale » = une QUESTION (re-servir l'info), pas un rappel-tâche")
check(R._cap_rappel("rappelle-moi qui a écrit 1984") is None, "« rappelle-moi qui… » = question, pas un rappel")
r = R._cap_rappel("rappelle-moi que mon code porte est 4512")
check(r is not None and r.startswith("C'est noté : mon code porte est 4512"), "« rappelle-moi que FAIT » stocké")
# E2E : stockage puis LISTE — la promesse « je te le rappelle » est TENUE par le stage mémoire.
import tempfile as _tf
import conversation as _cvx
_memx = _cvx.MemoireConversation(racine=_tf.mkdtemp(prefix="rappel-gate-"))
for _q in ("rappelle-moi d'acheter du pain", "rappelle-moi de sortir la poubelle"):
    _memx.ajoute("cr1", "user", _q, scope="prive")           # la couche serveur note chaque tour (serveur.py)
    R.repond(_memx, "cr1", _q, pleine=True)
_memx.ajoute("cr1", "user", "qu'est-ce que je devais faire ?", scope="prive")
r = R.repond(_memx, "cr1", "qu'est-ce que je devais faire ?", pleine=True)
check(r is not None and "acheter du pain" in r and "sortir la poubelle" in r,
      "« qu'est-ce que je devais faire ? » -> la liste des rappels stockés (promesse tenue)")

# — FUSEAUX HORAIRES (FAUX=0 vécu : « heure à New York » servait l'heure LOCALE) + ÂGE depuis l'année —
r = R._cap_quotidien("quelle heure est-il à New York ?")
check(r is not None and not r.startswith("Il est") and "New York" in r,
      "heure à New York -> fuseau IANA OU abstention — plus JAMAIS l'heure locale nue")
r = R._cap_quotidien("tokyo il est quelle heure ?")
check(r is not None and "Tokyo" in r and not r.startswith("Il est"),
      "ville EN TÊTE de phrase -> fuseau aussi (l'heure locale était servie pour Tokyo, FAUX vécu)")
r = R._cap_quotidien("quelle heure est-il à Trifouillis-les-Oies ?")
check(r is not None and "abstenir" in r.lower() or (r is not None and "fuseau" in r),
      "ville inconnue -> abstention honnête dite")
r = R._cap_quotidien("quelle heure est-il ?")
check(r is not None and r.startswith("Il est"), "sans ville -> heure locale (horloge machine), comme avant")
r = R._cap_quotidien("quel âge a une personne née en 1990 ?")
check(r is not None and "selon que l'anniversaire" in r, "âge né en 1990 -> fourchette honnête (anniversaire inconnu)")
# VAGUE 32 : âge exact avec date complète ; phrasé « si je suis né en … » ; année future ; heure décalée ;
# garde éphémérides (l'heure ACTUELLE était servie au coucher du soleil et à « dans 3 heures », FAUX vécus).
r = R._cap_quotidien("quel âge a quelqu'un né le 15 mars 1990 ?")
check(r is not None and r.split()[0].isdigit() and "15 mars 1990" in r, "date complète -> âge EXACT")
r = R._cap_quotidien("si je suis né en 1990 quel âge j'ai ?")
check(r is not None and "selon que l'anniversaire" in r, "phrasé « si je suis né en » -> fourchette")
r = R._cap_quotidien("quelle année dans 10 ans ?")
check(r is not None and r.startswith("En ") and "horloge" in r, "année dans 10 ans -> année + 10 étiquetée")
r = R._cap_quotidien("dans combien d'années 2050 ?")
check(r is not None and r.startswith("Dans ") and "2050" in r, "dans combien d'années 2050 -> écart exact")
r = R._cap_quotidien("à quelle heure le soleil se couche ?")
check(r is not None and "éphémérides" in r, "coucher du soleil -> abstention DITE, jamais l'horloge")
r = R._cap_quotidien("quelle heure sera-t-il dans 3 heures ?")
check(r is not None and r.startswith("Il sera") and "+ 3 heures" in r, "heure future -> horloge + décalage")
# VAGUE 33 : calendrier courant (horloge machine, tout étiqueté).
r = R._cap_quotidien("quelle saison sommes-nous ?")
check(r is not None and "hémisphère nord" in r and "approximatives" in r, "saison -> hémisphères + bornes dites")
r = R._cap_quotidien("quel est le numéro de la semaine actuelle ?")
check(r is not None and r.startswith("Semaine ") and "ISO 8601" in r, "semaine ISO -> numérotation dite")
r = R._cap_quotidien("combien de jours reste-t-il avant la fin de l'année ?")
check(r is not None and "31 décembre" in r, "jours restants -> calcul exact")
r = R._cap_quotidien("quel est le 200e jour de l'année ?")
check(r is not None and "200e jour" in r, "200e jour -> date exacte, année d'horloge étiquetée")
r = R._cap_quotidien("le 400e jour de l'année ?")
check(r is not None and "pas de 400e" in r, "400e jour -> borne DITE")
r = R._cap_quotidien("l'année prochaine est-elle bissextile ?")
check(r is not None and ("Oui" in r or "Non" in r) and "grégorienne" in r, "bissextile relative -> résolue + règle dite")
# CONJUGAISON (vague 35) : « comment CONJUGUER aimer au futur » conjuguait « conjuguer » au présent (FAUX vécu).
r = R._cap_conjugaison("comment conjuguer aimer au futur ?")
check(r is not None and "PRÉSENT" in r and "futur" in r, "temps hors présent -> honnêteté, jamais le présent servi")
r = R._cap_conjugaison("l'imparfait de chanter ?")
check(r is not None and "PRÉSENT" in r, "imparfait -> honnêteté (périmètre dit)")
r = R._cap_conjugaison("conjugue le verbe chanter au présent")
check(r is not None and "je chante" in r, "présent régulier intact")
r = R._cap_quotidien("dans combien de jours le 25 décembre ?")
check(r is not None and "décembre" in r and "jours" in r, "compte à rebours vers une date (plus le « 31 » du gabarit mois)")
r = R._cap_quotidien("dans combien de jours Noël ?")
check(r is not None and "25 décembre" in r, "Noël -> compte à rebours jusqu'au 25 décembre")
r = R._cap_quotidien("quel jour de la semaine sommes-nous ?")
check(r is not None and "Nous sommes le" in r, "« quel jour de la semaine sommes-nous » -> date du jour")
r = R._cap_quotidien("quelle est la date aujourd'hui")
check(r is not None and "Nous sommes le" in r, "« quelle est la date aujourd'hui » -> date du jour")
r = R._cap_quotidien("quel jour de la semaine était le 14 juillet 1789 ?")
check(r == "Le 14 juillet 1789 était un mardi (calendrier grégorien).", "14 juillet 1789 -> mardi (exact)")
r = R._cap_quotidien("quel jour était le 11 novembre 1918 ?")
check(r is not None and "lundi" in r, "11 novembre 1918 -> lundi")
r = R._cap_quotidien("quel jour était le 3 mars 1400 ?")
check(r is not None and "julien" in r, "avant 1583 -> abstention DITE (calendrier julien), jamais un jour décalé")

# — OPÉRATIONS TEXTUELLES exactes sur un mot (_cap_texte, vague 10 : natif déterministe, FAUX=0 par construction) —
r = R._cap_texte("compte les lettres du mot anticonstitutionnellement")
check(r == "25 lettres dans « anticonstitutionnellement ».", "compter les lettres -> 25 (exact)")
r = R._cap_texte("compte les lettres du mot porte-monnaie")
check(r is not None and r.startswith("12 lettres") and "non comptés" in r,
      "mot à tiret -> 12 lettres, restriction DITE (tirets non comptés)")
check(R._cap_texte("épelle le mot chien à l'envers") == "« chien » à l'envers : neihc.", "envers -> neihc")
check(R._cap_texte("épelle chien") == "« chien » s'épelle : c-h-i-e-n.", "épeler -> c-h-i-e-n")
r = R._cap_texte("niche et chien sont-ils des anagrammes ?")
check(r is not None and r.startswith("Oui"), "niche/chien -> anagrammes (mêmes lettres triées)")
r = R._cap_texte("chien et chat sont-ils des anagrammes ?")
check(r is not None and r.startswith("Non"), "chien/chat -> pas anagrammes")
check(R._cap_texte("épelle-moi la vérité sur cette affaire") is None, "« épelle-moi la vérité sur… » (pas UN mot) -> None")
check(R._cap_texte("inverse le mot chat") == "« chat » à l'envers : tahc.", "« inverse le mot chat » -> tahc")
check(R._cap_texte("retourne le mot bonjour") == "« bonjour » à l'envers : ruojnob.", "« retourne le mot X » -> renversé")
check(R._cap_texte("épelle chien") == "« chien » s'épelle : c-h-i-e-n.", "« épelle chien » (sans « à l'envers ») reste l'épellation")
check(R._cap_texte("combien de lettres a envoyées Napoléon") is None, "lettres = courriers -> pas volé (garde)")
check(R._cap_texte("quelle est la capitale de la France") is None, "question factuelle -> None")
r = R._cap_texte("mets le mot bonjour en majuscules")
check(r is not None and "BONJOUR" in r, "majuscules -> BONJOUR")
r = R._cap_texte("combien de mots dans la phrase le chat mange la souris")
check(r is not None and r.startswith("5 mots"), "compter les mots -> 5 (règle dite : séparés par des espaces)")
r = R._cap_texte("trie les nombres 5, 2, 9, 1")
check(r == "Dans l'ordre croissant : 1, 2, 5, 9.", "tri croissant exact")

# — ARITHMÉTIQUE DE DATES (horloge machine + datetime, calcul calendaire EXACT — vague 9) —
import datetime as _dt  # noqa: E402

_aujourdhui = _dt.date.today()
_d45 = _aujourdhui + _dt.timedelta(days=45)
r = R._cap_quotidien("quel jour serons-nous dans 45 jours ?")
check(r is not None and ("%d" % _d45.day) in r and "exact" in r,
      "« dans 45 jours » -> date exacte (horloge + timedelta), étiquetée calculée")
r = R._cap_quotidien("quel jour était-il il y a 10 jours ?")
_dm10 = _aujourdhui - _dt.timedelta(days=10)
check(r is not None and r.startswith("C'était") and ("%d" % _dm10.day) in r, "« il y a 10 jours » -> passé exact")
r = R._cap_quotidien("combien de jours entre le 1er janvier et le 15 mars ?")
_n = abs((_dt.date(_aujourdhui.year, 3, 15) - _dt.date(_aujourdhui.year, 1, 1)).days)
check(r is not None and r.startswith("%d jours" % _n) and "horloge" in r,
      "intervalle sans année -> %d jours, année de l'horloge ÉTIQUETÉE (bissextile change le compte)" % _n)
r = R._cap_quotidien("combien de jours entre le 1er janvier 2024 et le 15 mars 2024 ?")
check(r is not None and r.startswith("74 jours"), "2024 bissextile -> 74 jours (et pas 73)")
check(R._cap_quotidien("combien de jours entre le 15 mars et le 1er janvier ?") is None,
      "intervalle INVERSÉ sans années (année suivante ?) -> abstention honnête")
check(R._cap_quotidien("quel jour serons-nous dans 3 mois ?") is None,
      "« dans 3 mois » (durée ambiguë 28-31 j) -> abstention, jamais d'à-peu-près")
_d21 = _aujourdhui + _dt.timedelta(days=21)
r = R._cap_quotidien("quelle est la date dans 3 semaines ?")
check(r is not None and ("%d" % _d21.day) in r and "exact" in r,
      "« quelle EST LA date dans 3 semaines » -> date exacte (le motif acceptait seulement « quelle date »)")
# HEURE D'UNE VILLE MULTI-MOTS (FAUX vécu 2026-07-08 : « Rio de Janeiro » -> l'heure LOCALE servie, la
# particule minuscule cassait l'ancre de fin de la garde).
r = R._cap_quotidien("quelle heure est-il à Rio de Janeiro ?")
check(r is not None and "Sao_Paulo" in r, "Rio de Janeiro -> fuseau America/Sao_Paulo, jamais l'heure locale")
r = R._cap_quotidien("quelle heure est-il à Oulan-Bator ?")
check(r is not None and "m'abstenir" in r, "ville inconnue multi-mots -> abstention DITE, jamais l'heure locale")
# JOUR DE LA SEMAINE au FUTUR + année d'horloge ÉTIQUETÉE (« tombera le 25 décembre » partait en fuzzy
# « 24 decembre » -> « 2019 », FAUX vécu 2026-07-08).
r = R._cap_quotidien("quel jour de la semaine sera le 1er janvier 2030 ?")
check(r == "Le 1 janvier 2030 sera un mardi (calendrier grégorien).", "futur explicite -> sera un mardi")
r = R._cap_quotidien("le 14 juillet tombe quel jour ?")
check(r is not None and "horloge de ta machine" in r, "date sans année -> année d'horloge ÉTIQUETÉE")
r = R._cap_quotidien("donne-moi l'heure de Tokyo")
check(r is not None and "Asia/Tokyo" in r, "« donne-moi l'heure de Tokyo » -> fuseau (motif élargi)")
# GARDE COMPTAGE : la durée composée n'est pas un comptage d'hyponymes (« 10 termes jour », vécu).
check(R._cap_comptage("2 semaines et 3 jours ça fait combien de jours") is None,
      "durée composée -> pas un comptage lexical")
# OPÉRATIONS TEXTUELLES vague 31 (« Le radar est un système » répondait à côté du MOT, vécu 2026-07-08).
r = R._cap_texte("le mot radar est-il un palindrome")
check(r is not None and r.startswith("Oui — « radar »"), "palindrome radar -> Oui (natif)")
r = R._cap_texte("le mot chat est-il un palindrome")
check(r is not None and r.startswith("Non") and "tahc" in r, "palindrome chat -> Non + envers montré")
check(R._cap_texte("combien de fois la lettre s dans mississippi")
      == "4 fois la lettre « s » dans « mississippi ».", "occurrences -> 4")
check(R._cap_texte("trie les mots banane, abricot, cerise par ordre alphabétique")
      == "Ordre alphabétique : abricot, banane, cerise.", "tri de mots (le lexique dumpait, vécu)")
check(R._cap_texte("quel est le plus long mot entre chat et éléphant")
      == "« éléphant » (8 lettres contre 4).", "plus long mot -> éléphant")
check(R._cap_texte("les initiales de Jean-Claude Van Damme")
      == "J. C. V. D. (initiales de Jean-Claude Van Damme).", "initiales -> J. C. V. D.")
r = R._cap_texte("remplace les a par des o dans banana")
check(r is not None and "bonono" in r, "remplacement de lettre -> bonono")
r = R._cap_texte("combien de caractères dans anticonstitutionnellement")
check(r is not None and r.startswith("25 caractères"), "caractères -> 25 (tout signe compris)")
check(R._cap_quotidien("combien de jours entre le 30 février et le 15 mars ?") is None,
      "date invalide (30 février) -> abstention")

# — CONSEIL PARAPLUIE (avis ⑤ : décision sous incertitude, decision.py — probabilité RAPPORTÉE, règle AFFICHÉE) —
import meteo as _MET  # noqa: E402

_pluie_avant = _MET.pluie_aujourdhui
try:
    os.environ["IA_WEB"] = "1"
    _MET.pluie_aujourdhui = lambda v: {"nom": v, "pays": "France", "proba_pluie": 80}
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ?")
    check(r is not None and r.startswith("Conseil calculé") and "80 %" in r and "prendre le parapluie" in r,
          "pluie 80 % -> conseil CALCULÉ « prendre » (utilité espérée, probabilité rapportée)")
    check(r is not None and "Règle affichée" in r and "re-tranche" in r,
          "la règle d'utilité est AFFICHÉE et re-tranchable (verdict conditionnel, jamais un fait)")
    _MET.pluie_aujourdhui = lambda v: {"nom": v, "pays": "France", "proba_pluie": 1}
    r = R._cap_quotidien("faut-il prendre un parapluie à Toulouse ?")
    check(r is not None and "sortir sans" in r, "pluie 1 % -> conseil « sortir sans » (asymétrie assumée)")
    _MET.pluie_aujourdhui = lambda v: {"nom": v, "pays": "France", "proba_pluie": 9}
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ?")
    check(r is not None and "pile ou face" in r,
          "pluie ~9 % (point d'indifférence) -> ABSTENTION honnête (écart d'utilité sous la marge)")
    # PONDÉRATION UTILISATEUR : la promesse « je re-tranche » est TENUE (marqueurs fermés dans la demande).
    _MET.pluie_aujourdhui = lambda v: {"nom": v, "pays": "France", "proba_pluie": 20}
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ?")
    check(r is not None and "prendre le parapluie" in r, "pluie 20 %, pondération défaut -> prendre")
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ? pas envie de le porter")
    check(r is not None and "sortir sans" in r and "TA pondération" in r,
          "même 20 % mais « pas envie de le porter » -> re-tranché « sortir sans », règle utilisateur AFFICHÉE")
    _MET.pluie_aujourdhui = lambda v: {"nom": v, "pays": "France", "proba_pluie": 6}
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ?")
    check(r is not None and "sortir sans" in r, "pluie 6 %, défaut -> sortir sans")
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ? j'ai horreur d'être trempé")
    check(r is not None and "prendre le parapluie" in r,
          "même 6 % mais « horreur d'être trempé » -> re-tranché « prendre » (aversion pondérée)")
    r = R._cap_quotidien("dois-je prendre un parapluie ?", "cv-pluie")
    check(r is not None and "quelle ville" in r, "sans ville -> demande la ville (attente à trou rejouable)")
    import assistant_nl as _A2
    check(_A2.reprend_clarification("cv-pluie", "à Brives") == "dois-je prendre un parapluie à Brives ?",
          "« à Brives » au tour suivant COMPLÈTE la question parapluie (conversation, pas question-réponse)")
    os.environ.pop("IA_WEB", None)
    r = R._cap_quotidien("dois-je prendre un parapluie à Toulouse ?")
    check(r is not None and "EN DIRECT" in r and "🌐" in r, "web OFF -> refus honnête actionnable (jamais deviné)")
    check(_A2.qualifie_texte("Conseil calculé — test").statut == _A2.SUPPOSITION,
          "porte unique : un conseil calculé est classé SUPPOSITION (conditionnel), jamais FAIT")
finally:
    _MET.pluie_aujourdhui = _pluie_avant
    os.environ.pop("IA_WEB", None)

# — TROUS DE L'AUDIT ATOMIQUE 2026-07-08 (batterie réelle) : plus jamais mémo/web-coupé sur ces intentions —
r = R._cap_challenge("teste mes connaissances")
check(r is not None and "Défi accepté" in r, "« teste mes connaissances » -> challenge (partait en MÉMO)")
r = R._cap_challenge("pose-moi une question difficile sur la géographie")
check(r is not None and "géographie" in r, "« pose-moi une question sur X » -> challenge SUR X (partait au web)")
r = R._cap_creer_ouvert("donne-moi une idée")
check(r is not None and "idée du chapeau" in r, "« donne-moi UNE idée » -> amplificateur créatif (partait au web)")
r = R._cap_creer_ouvert("propose-moi une idée de produit innovant")
check(r is not None and "idée du chapeau" in r, "« propose-moi une idée de X » -> amplificateur créatif")
r = R._cap_invention("que manque-t-il pour stocker l'énergie solaire la nuit ?")
check(r is not None and "catalogue" in r and "CHIFFRE" in r,
      "besoin HORS catalogue -> amplification honnête (méthode donnée), plus jamais « internet coupé »")

# — SYLLOGISME À PRÉMISSES FOURNIES (mode hypothétique balisé, jamais un fait) —
r = R._cap_syllogisme("si tous les mammifères allaitent et que le chat est un mammifère, que peut-on en déduire ?")
check(r is not None and r.startswith("D'après TES prémisses") and "le chat allaite" in r,
      "syllogisme valide -> conclusion DANS les prémisses, article gardé (« le chat allaite »)")
check(r is not None and "CORROBORENT" in r, "mineure vérifiée dans le store -> corroboration DITE (chat → mammifère)")
r = R._cap_syllogisme("si tous les oiseaux volent et que la tulipe est une fleur, que peut-on en déduire ?")
check(r is not None and "ne se noue pas" in r, "moyen terme disjoint -> syllogisme refusé EXPLIQUÉ (jamais forcé)")
check(R._cap_syllogisme("quelle est la capitale de la France ?") is None, "hors périmètre -> None")
r = R._cap_syllogisme("si tous les hommes sont mortels et que Socrate est un homme, que peut-on en conclure ?")
check(r is not None and "Socrate est mortel" in r,
      "Barbara classique -> « Socrate est mortel » (copule accordée au singulier)")
r = R._cap_syllogisme("si tous les félins sont des animaux et que le chat est un félin, que peut-on en déduire ?")
check(r is not None and "le chat est un animal" in r, "« sont des animaux » -> « est un animal » (pluriel -aux)")
import assistant_nl as _A3
check(_A3.qualifie_texte("D'après TES prémisses — test").statut == _A3.SUPPOSITION,
      "porte unique : une conclusion de syllogisme est SUPPOSITION (prémisses de l'utilisateur), jamais FAIT")

# — QUIZ VÉRIFIÉ (mandat « que l'IA nous challenge ») : question POSÉE depuis la base, réponse JUGÉE contre le fait —
r = R._cap_challenge("challenge-moi sur la géographie", "cv-quiz")
check(r is not None and "ma question" in r and "capitale de «" in r,
      "défi -> une VRAIE question tirée de la base vérifiée (plus seulement « affirme »)")
q = R._QUIZ.get("cv-quiz")
check(q is not None and bool(q.get("valeur")), "réponse attendue mémorisée par conversation")
check(R._quiz_verdict("cv-quiz", q["valeur"]).startswith("✔ Exact"),
      "bonne réponse -> ✔ tranché par le fait vérifié (jamais un jugement au flair)")
R._cap_challenge("challenge-moi", "cv-quiz")
v = R._quiz_verdict("cv-quiz", "Ouagadougou-les-Bains")
check(v is not None and v.startswith("✘ Non") and R._QUIZ.get("cv-quiz") is None,
      "mauvaise réponse -> ✘ + LA correction vérifiée, état consommé (une seule chance)")
R._cap_challenge("challenge-moi", "cv-quiz")
check(R._quiz_verdict("cv-quiz", "quelle est la population du japon ?") is None,
      "nouvelle vraie demande pendant le quiz -> None (la conversation n'est JAMAIS otage)")
R._cap_challenge("challenge-moi", "cv-quiz")
check("Fin du défi" in (R._quiz_verdict("cv-quiz", "stop") or ""), "« stop » -> fin propre du défi")
check(_A3.qualifie_texte("Défi accepté — test").statut == _A3.ECHANGE,
      "porte unique : un défi lancé est un ÉCHANGE, pas un fait")

# — LOGIQUE PROPOSITIONNELLE (câblage « tout câbler » : sophismes.py rendu conversationnel) —
r = R._cap_logique("si il pleut alors la route est mouillée, or il pleut, donc la route est mouillée")
check(r is not None and "VALIDE" in r and "modus ponens" in r, "modus ponens -> VALIDE")
r = R._cap_logique("si il pleut alors la route est mouillée, or la route n'est pas mouillée, donc il ne pleut pas")
check(r is not None and "VALIDE" in r and "modus tollens" in r, "modus tollens -> VALIDE")
r = R._cap_logique("si il pleut alors la route est mouillée, or la route est mouillée, donc il pleut")
check(r is not None and "INVALIDE" in r and "affirmation du conséquent" in r, "affirmation du conséquent -> sophisme")
r = R._cap_logique("si il pleut alors la route est mouillée, or il ne pleut pas, donc la route n'est pas mouillée")
check(r is not None and "INVALIDE" in r and "négation de l'antécédent" in r, "négation de l'antécédent -> sophisme")
check(R._cap_logique("quelle est la capitale de la France ?") is None, "logique ne vole pas une question factuelle")
check(R._cap_logique("bonjour comment vas-tu ?") is None, "logique hors périmètre -> None")
import assistant_nl as _A4
check(_A4.qualifie_texte("Raisonnement VALIDE (modus ponens) : test").statut == _A4.FAIT,
      "porte unique : verdict logique = FAIT (forme jugée par module vérifié)")

# — DEMANDE IMPÉRATIVE NON TRAITÉE : repli honnête, plus jamais « C'est noté » (qualité conversationnelle) —
check(R._est_demande_imperative("équilibre la réaction H2 + O2 -> H2O"), "« équilibre … » détecté comme ordre")
check(R._est_demande_imperative("range mes fichiers"), "« range … » détecté comme ordre")
check(R._est_demande_imperative("stp équilibre la réaction"), "préambule « stp » dépouillé -> ordre impératif")
check(not R._est_demande_imperative("mon plat préféré est la ratatouille"), "affirmation perso -> PAS un ordre")
check(not R._est_demande_imperative("rappelle-moi d'acheter du pain"), "verbe de MÉMORISATION -> PAS un ordre (mémo légitime)")
check(not R._est_demande_imperative("j'ai rendez-vous mardi"), "note datée -> PAS un ordre (mémo légitime)")

# — THÉORIE DES JEUX (jeux_appliques rendu conversationnel : équilibres de Nash de jeux classiques) —
r = R._cap_jeux("quel est l'équilibre de Nash du dilemme du prisonnier ?")
check(r is not None and "trahir, trahir" in r and "Pareto" in r, "dilemme du prisonnier -> (trahir, trahir) + paradoxe Pareto")
r = R._cap_jeux("équilibre de Nash de la bataille des sexes")
check(r is not None and "bataille des sexes" in r and "(0, 0)" in r and "(1, 1)" in r, "bataille des sexes -> 2 équilibres")
r = R._cap_jeux("équilibre de Nash du matching pennies")
check(r is not None and "PAS d'équilibre" in r and "mixtes" in r, "matching pennies -> pas d'équilibre pur (honnête)")
check(R._cap_jeux("quelle est la capitale de la France ?") is None, "jeux ne vole pas une question factuelle")
check(R._cap_jeux("parle-moi du jeu vidéo Zelda") is None, "« jeu » sans jeu catalogué -> None (pas d'invention)")

# — MODULO / RESTE (FAUX=0 : « reste de 17 divisé par 5 » donnait 3.4 = la division, pas le reste) —
check(R._reponse_calcul("quel est le reste de 17 divisé par 5") == "2", "reste de 17÷5 -> 2 (plus jamais 3.4)")
check(R._reponse_calcul("17 modulo 5") == "2", "17 modulo 5 -> 2")
check(R._reponse_calcul("17 mod 5") == "2", "17 mod 5 -> 2")
check(R._reponse_calcul("12 divisé par 4") == "3", "division exacte préservée (12÷4 -> 3)")
check(R._reponse_calcul("reste de 10 divisé par 0") is None, "reste par 0 -> None (abstention honnête)")

print("=== valide_capacites_chat : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
