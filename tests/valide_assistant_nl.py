#!/usr/bin/env python3
"""
VALIDE assistant_nl — la porte conversationnelle AUTONOME (bornage -> répond/calcule/cherche/DEMANDE) — ADVERSE, FAUX=0.

Contrat jugé :
  • question bornée CONNUE -> FAIT avec provenance (jamais sans source) ;
  • calcul réellement évalué ET COUVRANT toute la question -> la bonne valeur ; fragment/opinion -> JAMAIS un fait ;
  • question AMBIGUË -> l'assistant POSE UNE QUESTION (statut clarification), ne devine JAMAIS ;
  • confirmation « oui » -> la question d'origine est REJOUÉE avec la correction CONFIRMÉE (état consommé une fois) ;
  • non-borné -> SUPPOSITION cadrée ; rappel de dialogue -> SUPPOSITION RAPPORTÉE (jamais FAIT) ;
  • borné inconnu SANS réseau -> HORS gracieux (recherche réelle = opt-in IA_WEB=1 / transport injecté) ;
  • mode léger (pleine=False) : le hook assistant est INVISIBLE (aucune régression du repli existant).

NON-RÉGRESSION des failles de la passe adverse 2026-07-03 (22 confirmées) : extraction arithmétique partielle,
défaut-FAIT de l'enveloppe, année passée « prédiction », réécriture qui perdait le « ? », état partagé sans
conv_id, boucle de clarification indécidable, purge RGPD de l'état, messages honnêtes.

OFFLINE STRICT : LECTEUR_AMORCE_SEULE=1 (pas de chargement des 77M faits), transport veille FACTICE, IA_WEB
jamais posé. Ancres EXTERNES non circulaires : Paris (capitale), 42=6*7, 5=2,5+2,5, rivières du Portugal
(données réelles relues indépendamment du chemin testé).
"""
import os
import sys

os.environ["LECTEUR_AMORCE_SEULE"] = "1"          # AVANT tout import susceptible de tirer le lecteur
os.environ.pop("IA_WEB", None)                     # jamais de réseau réel dans la gate

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)
sys.path.insert(0, os.path.join(_ICI, "interface"))

ok = 0
ko = 0


def check(c: bool, l: str):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + l)


import assistant_nl as A                            # léger (base_faits + classifieur_bornage)
import classifieur_bornage as CB
import fonction_nl as FN
from base_faits import VERIFIE as _V, HORS as _H

# ————————————————— (1) ROUTAGE APRÈS-HORS : les 4 régimes du gardien de bornage —————————————————
r = A.apres_hors("quel est le plus beau pays du monde ?")
check(r is not None and r.statut == A.SUPPOSITION, "opinion -> statut SUPPOSITION (jamais un fait)")
check(r is not None and r.regime == "supposition_opinion", "opinion -> régime supposition_opinion")
# cadrage honnête : le texte DIT explicitement que la question est subjective (formulation « design Yohan »
# « Il n'y a pas de réponse unique, c'est subjectif… » — remplace l'ancien préfixe « Question non bornée »).
check(r is not None and ("subjectif" in r.texte.lower() or r.texte.startswith("Question non bornée")),
      "opinion -> cadrage honnête explicite (subjectif)")

r = A.apres_hors("combien font 6*7 ?")
check(r is not None and r.statut == A.FAIT and r.texte == "42", "calcul évalué -> FAIT 42 (ancre externe 6*7)")
check(r is not None and bool(r.source), "calcul -> provenance non vide")
r = A.apres_hors("combien font 10/4 ?")
check(r is not None and r.statut == A.FAIT and r.texte == "2.5", "calcul division -> 2.5 exact")
r = A.apres_hors("calcule 100-58")
check(r is not None and r.statut == A.FAIT and r.texte == "42", "impératif calcule -> FAIT 42")

# NON-RÉG faille « extraction PARTIELLE » : fragment évalué = FAUX servi comme fait. Plus jamais.
r = A.apres_hors("combien font 2,5 + 2,5 ?")
check(r is not None and r.statut == A.FAIT and r.texte == "5",
      "virgule décimale française -> 5 EXACT (ancre : 2,5+2,5=5, plus jamais « 7 »)")
r = A.apres_hors("combien font 2 + 2 fois 3 ?")
check(r is None or r.statut != A.FAIT, "« 2 + 2 fois 3 » (op verbale) -> JAMAIS un fait fragmentaire")
r = A.apres_hors("combien font 2*3**4 ?")
check(r is None or r.statut != A.FAIT, "« 2*3**4 » (chiffre orphelin après troncature) -> JAMAIS un fait")
r = A.apres_hors("quel est le resultat de 10/4 divise par 2 ?")
check(r is None or r.statut != A.FAIT, "« 10/4 divisé par 2 » -> JAMAIS un fait fragmentaire")
r = A.apres_hors("combien font 0.1+0.2 ?")
check(r is not None and r.statut == A.FAIT and r.texte == "0.3",
      "artefact flottant -> restitution arrondie sûre « 0.3 » (jamais 0.30000000000000004)")

# opinion PRÉEMPTE le calcul (biais conservateur du classifieur) : jamais un fait sur une demande d'avis.
r = A.apres_hors("a ton avis combien font 2+2 ?")
check(r is not None and r.statut != A.FAIT, "« à ton avis 2+2 » -> jamais FAIT (opinion préempte le calcul)")
r = A.apres_hors("combien font 1/0 ?")
check(r is None or r.statut != A.FAIT, "1/0 -> jamais un FAIT, pas d'exception")

r = A.apres_hors("quelle est la population du wakanda ?")
check(r is not None and r.statut == A.HORS, "borné inconnu sans web -> HORS gracieux")
check(r is not None and r.regime == "supposition_a_chercher", "borné inconnu -> régime à-chercher")
check(r is not None and "IA_WEB" in r.source, "réseau opt-in : le détail technique vit dans source, pas le texte")
check(r is not None and "IA_WEB" not in r.texte, "texte utilisateur sans jargon interne")

r = A.apres_hors("des trucs et des machins", None)
check(r is not None and r.statut == A.CLARIFICATION, "indécidable -> l'assistant POSE UNE QUESTION")
check(r is not None and "?" in r.texte and bool(r.attente), "clarification -> vraie question + attente déclarée")

check(A.apres_hors("") is None and A.apres_hors(None) is None, "entrée vide/None -> None (repli appelant)")

# NON-RÉG faille « année passée = prédiction » : le passé daté est BORNÉ (fait à chercher), le futur reste non-borné.
c = CB.classe("qui a gagne la coupe du monde de football en 2018 ?")
check(c.statut_ontologique == CB.BORNE and c.regime == CB.R_SUPPOSITION_A_CHERCHER,
      "« qui a gagné … en 2018 » -> BORNÉ à chercher (plus jamais « prédiction »)")
c = CB.classe("que va-t-il se passer en 2050 ?")
check(c.statut_ontologique == CB.NON_BORNE, "« que va-t-il se passer en 2050 » -> non-borné (marqueur verbal)")
c = CB.classe("quelle est la population de la france en 2999 ?")
check(c.statut_ontologique == CB.NON_BORNE, "année STRICTEMENT future (2999) -> non-borné (le futur n'est pas un fait)")

# NON-RÉG fonction_nl (FAUX+ préexistant démasqué) : couverture totale exigée.
st, tx, _ = FN.resout_arithmetique("combien font 2 + 2 fois 3")
check(st == _H, "fonction_nl : « 2 + 2 fois 3 » -> HORS (plus jamais un fragment évalué)")
st, tx, _ = FN.resout_arithmetique("calcule 3 plus 4")
check(st == _V and tx == "7", "fonction_nl : « 3 plus 4 » -> 7 (le cas légitime marche toujours)")
st, tx, _ = FN.resout_arithmetique("racine de 16 plus 9")
check(st == _H, "fonction_nl : « racine de 16 plus 9 » -> HORS (fragment racine refusé)")
st, tx, _ = FN.resout_arithmetique("racine carree de 144")
check(st == _V and tx == "12", "fonction_nl : racine de 144 -> 12 (cas légitime)")

# ————————————————— (2) RECHERCHE AUTONOME (transport factice, offline strict, cache TTL) —————————————————
A._PING_CACHE = None
A._TRANSPORT = lambda url, timeout=15: (200, ("contenu distinct de " + url).encode())
r = A.apres_hors("quelle est la population du wakanda ?")
check(r is not None and r.statut == A.HORS, "recherche factice -> reste HORS (pas d'extraction = pas de fait)")
check(r is not None and "joignabilité" in r.texte and "source(s) de confiance" in r.texte,
      "recherche factice -> dit EXACTEMENT ce qui a été fait (joignabilité, pas une fausse recherche)")
check(r is not None and bool(r.source), "recherche factice -> domaines en provenance")
check(r is not None and "supposition" in r.texte, "recherche factice -> typage supposition rapportée explicite")

A._PING_CACHE = None
def _transport_ko(url, timeout=15):
    raise OSError("pas de réseau")
A._TRANSPORT = _transport_ko
r = A.apres_hors("quelle est la population du wakanda ?")
check(r is not None and r.statut == A.HORS and "injoignables" in r.texte,
      "sources injoignables -> HORS honnête (dégradation gracieuse)")

# cache TTL : le 2e appel n'exécute PAS le transport (compteur d'appels stable).
A._PING_CACHE = None
_compte = [0]
def _transport_compte(url, timeout=15):
    _compte[0] += 1
    return (200, ("x" + url).encode())
A._TRANSPORT = _transport_compte
A.apres_hors("quelle est la population du wakanda ?")
n1 = _compte[0]
A.apres_hors("quelle est la superficie du wakanda ?")
check(_compte[0] == n1 and n1 > 0, "cache TTL joignabilité : pas de re-contact des sources à chaque question")
A._TRANSPORT = None
A._PING_CACHE = None

# sujet VIDE (question bornée sans contenu) -> CLARIFICATION, pas de recherche absurde.
r = A.apres_hors("quand a-t-il eu lieu ?", "c-vide")
check(r is not None and r.statut == A.CLARIFICATION and r.texte.startswith("Peux-tu préciser le sujet"),
      "borné sans sujet -> CLARIFICATION (jamais une recherche sur « lieu »)")
check(A.reprend_clarification("c-vide", "oui") == "", "« oui » après demande de précision -> invitation à reformuler")

# ————————————————— (3) CLARIFICATION AVEC ÉTAT (confirmée, consommée une fois, jamais silencieuse) —————————————————
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "vouliez-vous dire fleuve ?")
q2 = A.reprend_clarification("cv", "oui")
check(q2 == "quel fleuve traverse le portugal ?",
      "« oui » -> question réécrite SUR L'ORIGINAL, « ? » préservé (plus jamais « C'est noté »)")
check(A.reprend_clarification("cv", "oui") is None, "état consommé une seule fois (pas de rejeu)")

A.note_clarification("cv", "le flauve de la France", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "oui") == "le fleuve de la France ?",
      "réécriture sans « ? » d'origine -> « ? » AJOUTÉ (une clarification confirmée EST une demande)")
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "OUI !") == "quel fleuve traverse le portugal ?",
      "« OUI ! » (majuscules/ponctuation) -> confirmé quand même")
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "oui oui") == "quel fleuve traverse le portugal ?",
      "« oui oui » (tête confirmante courte) -> confirmé")
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "fleuve") == "quel fleuve traverse le portugal ?",
      "répéter le mot proposé -> confirmé")
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "non") == "", "« non » -> refus explicite (invite à reformuler)")
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "oui mais pour la Loire") is None,
      "« oui mais … » -> PAS une confirmation (nouvelle question, jamais de substitution douteuse)")
check(A.reprend_clarification("cv", "oui") is None, "l'état a été consommé (pas de piège différé)")
A.note_clarification("cv", "quel flauve traverse le portugal ?", "flauve", "fleuve", "…")
check(A.reprend_clarification("cv", "quelle est la capitale du japon ?") is None,
      "réponse sans rapport -> None (traitée comme nouvelle question)")
A.note_clarification(None, "q", "a", "b", "t")
check(A.reprend_clarification(None, "oui") is None, "conv_id None -> aucun état (no-op sûr)")

# anti-boucle indécidable : 2 clarifications puis HORS différencié ; « oui » intercepté proprement.
A.oublie_etat("c-ind"); A._INDECIS.pop("c-ind", None)
r1 = A.apres_hors("des trucs et des machins", "c-ind")
r2 = A.apres_hors("des bidules et des choses la", "c-ind")
r3 = A.apres_hors("des machins chouettes par la", "c-ind")
check(r1.statut == A.CLARIFICATION and r2.statut == A.CLARIFICATION,
      "indécidable -> 2 clarifications d'abord (on demande)")
check(r3.statut == A.HORS and r3.texte.startswith("Je ne sais pas encore traiter"),
      "3e indécidable consécutif -> HORS différencié (anti-boucle, plus jamais le même message à l'infini)")
check(A.reprend_clarification("c-ind", "oui") == "",
      "« oui » après clarification indécidable -> invitation à reformuler (plus jamais « C'est noté »)")

# CLARIFICATION À TROU (slot) — vécu 2026-07-06 : « il fait quel temps ? » -> « pour quelle ville ? » ->
# « A Brives » partait en recherche web libre au lieu de compléter la question météo.
A.note_attente_slot("c-slot", "quel temps fait-il à %s ?")
check(A.reprend_clarification("c-slot", "A Brives") == "quel temps fait-il à Brives ?",
      "« A Brives » après « pour quelle ville ? » -> question météo COMPLÉTÉE (conversation, pas question-réponse)")
check(A.reprend_clarification("c-slot", "Toulouse") is None, "état slot consommé une seule fois")
A.note_attente_slot("c-slot", "quel temps fait-il à %s ?")
check(A.reprend_clarification("c-slot", "à Saint-Étienne stp") == "quel temps fait-il à Saint-Étienne ?",
      "préposition + politesse dépouillées, casse/accents de la ville GARDÉS")
A.note_attente_slot("c-slot", "quel temps fait-il à %s ?")
check(A.reprend_clarification("c-slot", "quelle est la capitale du japon ?") is None,
      "nouvelle question pendant l'attente de slot -> None (traitée normalement, jamais fourrée dans le trou)")
A.note_attente_slot("c-slot", "quel temps fait-il à %s ?")
check(A.reprend_clarification("c-slot", "non merci") == "",
      "refus pendant l'attente de slot -> refus explicite (invite à reformuler)")
A.note_attente_slot(None, "quel temps fait-il à %s ?")
check(A.reprend_clarification(None, "Paris") is None, "slot avec conv_id None -> no-op sûr")
A.note_attente_slot("c-slot2", "météo sans trou")
check(A.reprend_clarification("c-slot2", "Paris") is None, "gabarit sans %s -> jamais enregistré (no-op sûr)")

# AVIS 2/2 — POUR/CONTRE sourcé + verdict CONDITIONNEL (débats sans chiffres, brique Yohan « mon avis est… »).
import veille_structure as _VS_avis
_cwd_avant = _VS_avis.cherche_web_domaines
_wl_avant = _VS_avis.cherche_web_libre
A._TRANSPORT = lambda url, timeout=15: (200, b"x")
try:
    _VS_avis.cherche_web_domaines = lambda q, k=2, **kw: [
        ("Pour et contre", "Elles font moins de bruit et le coût d'usage est plus faible, mais l'autonomie "
                           "est plus courte et le prix d'achat est plus élevé.",
         "http://exemple.fr/ve", "exemple.fr"),
        ("Menu", "Marques Renault Peugeot Tesla Classements Guides Comparatifs Essais Newsletter",
         "http://menu.fr/nav", "menu.fr")]
    r = A.apres_hors("que penses-tu des voitures électriques ?", "c-avis")
    check(r is not None and r.statut == A.SUPPOSITION and "CONDITIONNEL" in r.texte,
          "débat sans chiffres -> avis CONDITIONNEL signé (règle affichée), jamais un goût inventé")
    check(r is not None and "exemple.fr" in r.texte and "rapporté" in r.texte,
          "les deux faces sont RAPPORTÉES et attribuées (dom + extrait)")
    check(r is not None and "menu.fr" not in r.texte,
          "garde PROSE : un extrait « menu de navigation » n'est jamais servi comme argument (vécu live)")
    check(r is not None and "critère" in r.texte, "le trancheur est le CRITÈRE de l'utilisateur (invité)")
    _VS_avis.cherche_web_domaines = lambda q, k=2, **kw: []
    _VS_avis.cherche_web_libre = lambda q, timeout=15: None
    r = A.apres_hors("que penses-tu des voitures électriques ?", "c-avis")
    check(r is not None and r.statut == A.SUPPOSITION and r.texte.startswith(A._PFX_OPINION),
          "aucune source -> repli cadrage subjectif existant, inchangé")
finally:
    _VS_avis.cherche_web_domaines = _cwd_avant
    _VS_avis.cherche_web_libre = _wl_avant
    A._TRANSPORT = None

# RGPD : l'oubli purge AUSSI l'état en-process (plus rien à rejouer).
A.note_clarification("c-rgpd", "question secrete flauve ?", "flauve", "fleuve", "…")
A.oublie_etat("c-rgpd")
check(A.reprend_clarification("c-rgpd", "oui") is None, "oublie_etat -> la question effacée n'est PLUS rejouable")

# ————————————————— (4) PORTE UNIQUE (amorce, mémoire ISOLÉE — classification POSITIVE) —————————————————
import conversation
mem = conversation.MemoireConversation(racine=None)          # volatile : zéro pollution des vraies conversations

r = A.repond("Bonjour !", "t-p0", memoire=mem)
check(r.statut == A.ECHANGE and r.texte.startswith("Bonjour"), "politesse -> statut ECHANGE (pas un fait)")

r = A.repond("Quelle est la capitale de la France ?", "t-p1", memoire=mem)
check(r.statut == A.FAIT and r.texte == "Paris", "borné connu -> FAIT Paris (ancre externe)")
check(r.regime == "fait" and bool(r.source), "borné connu -> régime fait rebouclé + provenance")

r = A.repond("Qui es-tu ?", "t-p1", memoire=mem)
check(r.statut == A.ECHANGE, "méta -> statut ECHANGE")

r = A.repond("Quelle est la population du wakanda ?", "t-p1", memoire=mem)
check(r.statut == A.HORS and "vérifié" in r.texte, "borné inconnu -> HORS honnête via la porte unique")

r = A.repond("", "t-p1", memoire=mem)
check(r.statut == A.HORS and r.texte == "", "question vide -> HORS vide (pas d'invention)")

# NON-RÉG faille « défaut = FAIT » : le rappel d'un dire utilisateur est une SUPPOSITION RAPPORTÉE, jamais un fait.
mem_r = conversation.MemoireConversation(racine=None)
mem_r.ajoute("t-rap", "user", "la capitale de l'australie c'est sydney")
r = A.repond("c'est quoi la capitale de l'australie", "t-rap", pleine=False, memoire=mem_r)
check(r.statut == A.SUPPOSITION and r.texte.startswith("D'après ce que tu m'as dit"),
      "rappel d'un dire utilisateur -> SUPPOSITION RAPPORTÉE (plus jamais FAIT « pipeline vérifié »)")
check("non vérifié" in r.source, "rappel -> source honnête (contenu non vérifié)")
check(r.regime == "", "rappel -> aucun régime de juge forgé")

# NON-RÉG : le refus « non » d'une clarification n'est PAS un fait.
mem_f = conversation.MemoireConversation(racine=None)
r = A.repond("quel flauve traverse le portugal ?", "t-flux", memoire=mem_f)
check(r.statut == A.CLARIFICATION and "vouliez-vous dire" in r.texte,
      "faute de frappe -> l'assistant POSE la question de clarification")
check(bool(r.attente), "clarification -> attente déclarée dans l'enveloppe")
r = A.repond("non", "t-flux", memoire=mem_f)
check(r.statut == A.CLARIFICATION and "eformule" in r.texte,
      "« non » -> invitation à reformuler, statut CLARIFICATION (plus jamais FAIT)")

# flux COMPLET : faute -> DEMANDE -> « oui » -> REJOUE la question corrigée -> vraie réponse (données réelles).
r = A.repond("quel flauve traverse le portugal ?", "t-flux", memoire=mem_f)
check(r.statut == A.CLARIFICATION, "la clarification se repose (nouvel état)")
r = A.repond("oui", "t-flux", memoire=mem_f)
# MÉCANISME : « oui » REJOUE la question corrigée (« flauve »->« fleuve »). En gate LÉGER (amorce-seule, hors
# ligne) la donnée « cours d'eau du Portugal » n'est pas chargée -> abstention HONNÊTE attendue ; avec données/
# web -> FAIT chiffré. FAUX=0 : jamais une invention (soit le fait réel, soit un aveu d'ignorance honnête).
if r.statut == A.FAIT:
    check("portugal" in r.texte.lower() and any(ch.isdigit() for ch in r.texte),
          "« oui » -> question corrigée REJOUÉE -> vraie liste des cours d'eau (données présentes)")
else:
    check(r.statut == A.HORS and ("information" in r.texte.lower() or "internet" in r.texte.lower()),
          "« oui » -> question corrigée REJOUÉE -> abstention honnête (donnée absente en gate léger, jamais inventée)")

# non-borné via la porte unique
r = A.repond("quel est le plus beau pays du monde ?", "t-p1", memoire=mem)
check(r.statut == A.SUPPOSITION, "non-borné via porte unique -> SUPPOSITION cadrée")

# sans conv_id : id JETABLE -> aucun état partagé entre appelants anonymes.
r = A.repond("quel flauve traverse le portugal ?", memoire=mem)
check(r.statut == A.CLARIFICATION, "sans conv_id : clarification posée quand même")
r = A.repond("oui", memoire=mem)
check(r.statut != A.FAIT, "sans conv_id : « oui » d'un AUTRE appel ne rejoue RIEN (pas de clé partagée)")

# qualifie_texte : classification positive directe.
import repond as _REP
check(A.qualifie_texte("Je n'ai pas l'information en mémoire pour l'instant.").statut == A.HORS,
      "qualifie_texte : repli -> HORS")
check(A.qualifie_texte(_REP._MSG_REFUS).statut == A.CLARIFICATION, "qualifie_texte : refus -> CLARIFICATION")
check(A.qualifie_texte("D'après ce que tu m'as dit : « x »").statut == A.SUPPOSITION,
      "qualifie_texte : rappel -> SUPPOSITION")
check(A.qualifie_texte("Paris") is None, "qualifie_texte : réponse factuelle -> None (FAIT par l'appelant)")

# ————————————————— (5) INTERFACE : mode léger STRICTEMENT inchangé (aucune régression de gate) —————————————————
import serveur

mem2 = conversation.MemoireConversation(racine=None)
rr = serveur.ajoute_message(mem2, "c-leger", "Quelle est la population du wakanda ?")   # pleine=False par défaut
check(_REP.est_fallback(rr["reponse"]), "léger : question inconnue -> repli existant (hook INVISIBLE)")
check(_REP.est_fallback("C'est noté, je m'en souviendrai. Tu pourras me le redemander."),
      "est_fallback reconnaît l'accusé de réception")
check(not _REP.est_fallback("Paris"), "est_fallback ne capte pas une vraie réponse")
rr = serveur.ajoute_message(mem2, "c-leger", "Mon plat préféré est la raclette.")
check(rr["reponse"] in _REP._variantes("note", _REP._MSG_NOTE),
      "léger : affirmation -> accusé de réception (famille « noté », variantes de formulation admises)")

# RGPD de bout en bout : oublier une conversation purge l'état de clarification.
A.note_clarification("c-oubli", "question secrete flauve ?", "flauve", "fleuve", "…")
serveur.oublie_conversation(mem2, "c-oubli")
check(A.reprend_clarification("c-oubli", "oui") is None,
      "oublie_conversation -> l'état assistant est purgé (rien d'« oublié » ne se rejoue)")

# ————————————————— MATHS DISCRÈTES / ARITHMÉTIQUE / TRIGO en NL (câblage « tout câbler » 2026-07-08) —————————————————
def _m(q):
    st, tx, _ = FN.resout_fonction(q)
    return tx if st == _V else None


check(_m("20% de 150 ?") == "30", "pourcentage : 20% de 150 -> 30")
check(_m("pgcd de 12 et 18") == "6", "PGCD de 12 et 18 -> 6")
check(_m("ppcm de 4 et 6") == "12", "PPCM de 4 et 6 -> 12")
check(_m("est-ce que 17 est premier ?") and "Oui" in _m("est-ce que 17 est premier ?"), "17 premier -> Oui")
check(_m("18 est-il un nombre premier ?") and "Non" in _m("18 est-il un nombre premier ?"), "18 premier -> Non")
check(_m("factorielle de 5") == "120", "factorielle 5 -> 120")
check(_m("5!") == "120", "5! -> 120")
check(_m("combien de façons d'ordonner 5 éléments") == "120", "permutations 5 -> 120")
check(_m("combinaisons de 2 parmi 5") == "10", "C(5,2) -> 10")
check(_m("arrangements de 2 parmi 5") == "20", "A(5,2) -> 20")
check(_m("fibonacci de 10") == "55", "Fibonacci 10 -> 55")
check(_m("sinus de 30 degrés") == "0.5", "sin 30° -> 0.5")
check(_m("cos de 60°") == "0.5", "cos 60° -> 0.5")
check(_m("tangente de 45") == "1", "tan 45° -> 1")
# INTÉRÊTS (placement) : valeur acquise + gain, étiquetés (composé par défaut, simple sur mention).
_i = _m("combien rapportent 1000 euros à 5% pendant 3 ans")
check(_i and "157.63" in _i and "1157.63" in _i, "intérêts composés : gain 157.63 + valeur acquise 1157.63")
_i = _m("1000 euros à 5% pendant 3 ans en intérêts simples")
check(_i and "150" in _i and "1150" in _i, "intérêts simples : gain 150 + valeur acquise 1150")
check(_m("20% de 150 ?") == "30", "le pourcentage simple n'est PAS confondu avec la finance (garde 3 composants)")
# NOMBRES COMPLEXES : module / argument / conjugué (parseur a+bi robuste : i seul, imaginaire pur, signes).
check(_m("module de 3+4i") == "5", "module de 3+4i -> 5")
check(_m("module de 5i") == "5", "module d'un imaginaire pur 5i -> 5")
check(_m("argument de i") and "1.57" in _m("argument de i"), "argument de i -> π/2 rad")
check(_m("conjugué de 2-3i") and "2 + 3i" in _m("conjugué de 2-3i"), "conjugué de 2-3i -> 2 + 3i")
check(_m("module de -3-4i") == "5", "module de -3-4i -> 5 (signes négatifs)")
check(_m("parle-moi de Djibouti") is None, "un « i » dans un nom propre ne déclenche PAS les complexes (garde mot-clé)")
# GARDE anti-faux-positif : « premier »/nombres ordinaux ne déclenchent PAS la primalité sur une question DATA.
for q in ("le premier président élu en 1958", "premier ministre depuis 2017", "premier roman de 1984",
          "quelle est la capitale de la France ?", "population du Japon en 2020", "qui a gagné en 2018"):
    check(_m(q) is None, "maths ne vole PAS « %s » (faux positif interdit)" % q[:34])

print(f"\n=== valide_assistant_nl : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
