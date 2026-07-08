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
# COEFFICIENT BINOMIAL nommé (tombait en MÉMO « Noté », garbage vécu) : interprétation MONTRÉE.
check(_m("coefficient binomial 2 parmi 5") == "C(5, 2) = 10", "coefficient binomial 2 parmi 5 -> C(5,2)=10")
check(_m("coefficient binomial de 5 et 2") == "C(5, 2) = 10", "binomial sans parmi : ordre C(n,k)")
_bi = _m("coefficient binomial 5 parmi 2")
check(_bi and _bi.startswith("C(2, 5) = 0") and "impossible" in _bi, "k>n -> 0 EXPLIQUÉ, jamais un 0 sec")
# PERMUTATIONS par « ranger/classer » (tombait en repli) : façons/manières OBLIGATOIRE + un seul entier.
check(_m("de combien de façons peut-on ranger 4 livres") == "24 (permutations : 4!)", "ranger 4 livres -> 24")
check(_m("combien de manières de classer 5 dossiers") == "120 (permutations : 5!)", "classer 5 dossiers -> 120")
check(_m("range mes fichiers") is None, "garde : impératif « range mes fichiers » ne matche pas")
check(_m("combien de façons de ranger 4 livres sur 2 étagères") is None,
      "garde : deux entiers (étagères) = autre problème -> HORS")
# PROBABILITÉ dé/pièce (brique équiprobabilité ; hypothèse d'équilibre ÉNONCÉE ; « Noté » garbage vécu).
_p6 = _m("probabilité d'obtenir un 6 avec un dé")
check(_p6 == "1/6 (≈ 16.67 %) — en supposant un dé équilibré à 6 faces.", "proba 6 au dé -> 1/6 + hypothèse")
check(_m("probabilité d'obtenir un 7 avec un dé") == "0 — un dé à 6 faces ne peut pas donner 7.",
      "face impossible -> 0 EXPLIQUÉ")
check(_m("quelle est la probabilité de tirer un 3 avec un dé à 20 faces")
      == "1/20 (≈ 5.00 %) — en supposant un dé équilibré à 20 faces.", "dé à 20 faces -> 1/20")
check(_m("probabilité de faire pile avec une pièce") == "1/2 (50 %) — en supposant une pièce équilibrée.",
      "proba pile -> 1/2 + hypothèse")
check(_m("probabilité de pluie demain à Toulouse") is None, "garde : proba de pluie ne matche pas (pas un dé)")
check(_m("la probabilité que le dé soit pipé") is None, "garde : dé pipé sans face demandée -> HORS")
check(_m("probabilité d'obtenir un 6 avec deux dés") is None, "garde : plusieurs dés = autre loi -> HORS")
check(_m("fibonacci de 10") == "55", "Fibonacci 10 -> 55")
# NOMBRE PREMIER ORDINAL (« Non, 100 n'est pas premier » répondait À CÔTÉ, FAUX vécu 2026-07-08).
check(_m("quel est le 100e nombre premier") == "Le 100e nombre premier est 541.", "100e premier -> 541")
check(_m("le 1er nombre premier") == "Le 1er nombre premier est 2.", "1er premier -> 2")
# SOMME DE SÉRIE (la route stats servait « Somme : 101 (sur 2 valeurs) », bornes prises pour la liste).
_ss = _m("somme des entiers de 1 à 100")
check(_ss and _ss.startswith("5050"), "somme des entiers de 1 à 100 -> 5050")
_ss2 = _m("somme des 100 premiers entiers")
check(_ss2 and _ss2.startswith("5050"), "somme des 100 premiers entiers -> 5050")
_ss3 = _m("somme des 5 premiers nombres premiers")
check(_ss3 and _ss3.startswith("28"), "somme des 5 premiers nombres premiers -> 28")
# ATOMES D'UN ÉLÉMENT NOMMÉ (« 3 atomes » servait le TOTAL pour « atomes d'oxygène dans CO2 », FAUX vécu).
check(_m("combien d'atomes d'oxygène dans CO2") == "2 atomes d'oxygène", "atomes d'oxygène dans CO2 -> 2")
check(_m("combien d'atomes de carbone dans CO2") == "1 atome de carbone", "atomes de carbone dans CO2 -> 1")
_a0 = _m("combien d'atomes de sodium dans H2O")
check(_a0 and _a0.startswith("0 — pas d'atome de sodium"), "élément absent -> 0 EXPLIQUÉ")
check(_m("combien d'atomes de fer dans CO2") is None, "élément hors référentiel -> abstention, JAMAIS le total")
check(_m("combien d'atomes dans une molécule de H2O") == "3 atomes", "total sans élément nommé -> 3")
# POURCENTAGE MASSIQUE avec nom d'élément FR (« de l'oxygène » tombait en mémo).
check(_m("pourcentage massique de l'oxygène dans H2O") == "88.81 %", "pourcentage massique l'oxygène -> 88.81")
# MOLARITÉ / NOM DE COMPOSÉ / MOLES<->GRAMMES (chimie quantitative + nomenclature, tombaient en mémo).
check(_m("molarité de 2 moles dans 4 litres") == "0.5 mol/L (2 mol dans 4 L)", "molarité 2 mol / 4 L -> 0.5")
_cc = _m("concentration si je dissous 0,5 mole dans 2 litres")
check(_cc and _cc.startswith("0.25 mol/L"), "concentration 0,5 mol / 2 L -> 0.25")
check(_m("comment s'appelle le composé CO2") == "CO2 : dioxyde de carbone (nomenclature systématique)",
      "nom du composé CO2")
_h2s = _m("quel est le nom du composé chimique H2S")
check(_h2s and "sulfure d'hydrogène" in _h2s, "nom du composé H2S")
_nm = _m("combien de moles dans 36 grammes d'eau")
check(_nm and _nm.startswith("1.9983 mol") and "H2O" in _nm, "moles dans 36 g d'eau -> 1.9983 (n = m/M)")
check(_m("combien de moles dans 10 grammes de kryptonite") is None, "substance inconnue -> abstention")
check(_m("quelle est la concentration de CO2 dans l'atmosphère") is None,
      "garde : concentration sans moles/litres -> HORS (pas un calcul)")
# ÉLECTRONIQUE / MÉCANIQUE (briques electronique + mecanique ; tombaient en mémo « C'est noté »).
check(_m("résistance équivalente de 10 ohms et 20 ohms en série") == "30 Ω (10 et 20 en série : somme)",
      "résistances en série -> 30")
_rp = _m("résistance équivalente de 10 ohms et 10 ohms en parallèle")
check(_rp and _rp.startswith("5 Ω"), "résistances en parallèle -> 5")
check(_m("résistance de 10 ohms") is None, "garde : une seule résistance sans série/parallèle -> HORS")
_pd = _m("période d'un pendule de 1 mètre")
check(_pd and _pd.startswith("2.00641 s") and "9.80665" in _pd, "pendule 1 m -> 2.006 s, g DIT")
check(_m("pression de 100 newtons sur 2 mètres carrés") == "50 Pa (100 N / 2 m²)", "pression -> 50 Pa")
# POURCENTAGES : part exacte « représente X sur Y » (partait en intervalle de Wilson, FAUX vécu) +
# augmentations ENCHAÎNÉES (sur le résultat, pas la base ; partait en détection de tendance).
check(_m("quel pourcentage représente 45 sur 60") == "75 %", "45 sur 60 -> 75 %")
check(_m("augmente 50 de 10 % puis de 20 %") == "66 (50 + 10 % = 55 ; 55 + 20 % = 66)",
      "augmentations enchaînées -> 66 (étapes montrées)")
# NOTATION SCIENTIFIQUE + CONSTANTES NOMMÉES.
check(_m("notation scientifique de 123000") == "1.23 × 10^5", "123000 -> 1.23e5")
check(_m("notation scientifique de 0,00042") == "4.2 × 10^-4", "0,00042 -> 4.2e-4")
_or = _m("le nombre d'or")
check(_or and _or.startswith("1.61803399"), "nombre d'or -> 1.618")
_e = _m("e vaut combien")
check(_e and _e.startswith("2.71828183"), "e -> 2.718")
# RÈGLE DE TROIS DÉCIMALE (FAUX vécu : « 4,50 euros » lu « 4 » -> 9.33 au lieu de 10.5 — virgule mangée).
check(_m("si 3 stylos coûtent 4,50 euros combien coûtent 7 stylos") == "10.5", "règle de trois décimale -> 10.5")
# DÉCIMALES avec le MOT moins/plus, résidu monnaie vide (« 20 euros moins 7,50 » tombait en mémo).
check(_m("20 euros moins 7,50") == "12.5", "20 euros moins 7,50 -> 12.5")
check(_m("combien font 20 euros moins 7,50") == "12.5", "combien font … moins -> 12.5")
check(_m("il fait moins 5 degrés") is None, "garde : « moins 5 degrés » (résidu non vide) -> pas un calcul")
check(_m("la guerre de 1939-1945") is None, "garde : intervalle d'années -> pas une soustraction")
# FRACTIONS MULTIPLES (« les trois quarts de 200 » tombait en mémo) ; décimal FINI exigé.
check(_m("les trois quarts de 200") == "150", "trois quarts de 200 -> 150")
check(_m("deux tiers de 90") == "60", "deux tiers de 90 -> 60")
check(_m("deux tiers de 100") is None, "deux tiers de 100 (décimal infini) -> abstention")
# MONNAIE : rendu exact + somme pièces/billets (le Fermi multipliait tout : ~60 pour 16, FAUX vécu).
check(_m("rendu de monnaie sur 50 euros pour un achat de 37,25") == "12.75 (50 − 37.25)", "rendu -> 12.75")
_ri = _m("rendu sur 20 euros pour 25,50")
check(_ri and _ri.startswith("Impossible"), "achat > billet -> Impossible DIT")
check(_m("j'ai 3 pièces de 2 euros et 2 billets de 5 euros, combien j'ai en tout")
      == "16 euros (3 × 2 + 2 × 5)", "pièces+billets -> 16 (somme exacte montrée)")
# POLYGONES RÉGULIERS + SOLIDES (tombaient en mémo/repli).
check(_m("périmètre d'un hexagone régulier de côté 5") == "30 (hexagone régulier : 6 × 5)", "hexagone -> 30")
check(_m("périmètre d'un octogone de côté 2,5") == "20 (octogone régulier : 8 × 2.5)", "octogone -> 20")
check(_m("combien d'arêtes a un cube") == "12", "arêtes cube -> 12")
check(_m("combien de sommets a un tétraèdre") == "4", "sommets tétraèdre -> 4")
# PRIX TOTAL quantité × prix unitaire (« 3 baguettes à 1,20 euro » tombait en repli).
check(_m("combien coûtent 3 baguettes à 1,20 euro") == "3.6 euros (3 × 1.2)", "3 baguettes à 1,20 -> 3.6")
# MPH (1 mile = 1.609344 km, définition légale).
_mph = _m("convertis 72 km/h en miles par heure")
check(_mph and _mph.startswith("44.7387"), "72 km/h -> 44.74 mph")
_mph2 = _m("60 mph en km/h")
check(_mph2 and _mph2.startswith("96.56064"), "60 mph -> 96.56 km/h")
# LETTRES ordinales (alphabet et mot) — natif exact, bornes DITES.
check(_m("quelle est la 5e lettre du mot maison") == "o", "5e lettre de maison -> o")
check(_m("la dernière lettre du mot chat") == "t", "dernière lettre de chat -> t")
check(_m("la première lettre de l'alphabet") == "a", "première lettre alphabet -> a")
check(_m("la 10e lettre de l'alphabet") == "j", "10e lettre alphabet -> j")
_l30 = _m("la 30e lettre de l'alphabet")
check(_l30 and _l30.startswith("L'alphabet n'a que 26"), "30e lettre -> borne DITE")
# CINÉMATIQUE v = d/t (FAUX vécu : « vitesse moyenne … 150 km en 2 heures » -> « Moyenne : 76 », la route
# stats moyennait distance et durée). Calcul montré ; les trois sens (v, t, d) câblés.
check(_m("vitesse moyenne si je parcours 150 km en 2 heures") == "75 km/h (150 km / 2 h)", "v = d/t -> 75 km/h")
check(_m("combien de temps pour parcourir 300 km à 100 km/h") == "3 h (300 km / 100 km/h)", "t = d/v -> 3 h")
_tv = _m("combien de temps pour faire 100 km à 70 km/h")
check(_tv and _tv.startswith("≈ 1 h 26 min (arrondi à la minute)"), "t = d/v inexact -> arrondi DIT")
check(_m("quelle distance à 90 km/h pendant 2 heures") == "180 km (90 km/h × 2 h)", "d = v×t -> 180 km")
# CONSOMMATION / PRIX UNITAIRE (règle de trois du quotidien, calcul montré ; unités cohérentes exigées).
_co = _m("consommation de 6 litres aux 100 km, pour 250 km ça fait combien")
check(_co == "15 L (6 L/100 km × 250 km)", "consommation aux 100 km -> 15 L")
check(_m("prix de 1,5 kg à 4 euros le kilo") == "6 euros (1.5 kg × 4 euros le kilo)", "prix au kilo -> 6")
check(_m("2 kg à 3 euros le litre") is None, "garde : unités disparates (kg vs litre) -> abstention")
# IMC (kg/m², OMS ; sans interprétation médicale) — formats 1m75 / 175 cm / 1,80 m.
check(_m("IMC pour 70 kg et 1m75") == "22.86 (70 kg / (1.75 m)²) — indice de masse corporelle", "IMC 1m75")
check(_m("IMC pour 70 kg et 175 cm") == "22.86 (70 kg / (1.75 m)²) — indice de masse corporelle", "IMC 175 cm")
_imc3 = _m("quel est l'IMC pour 80 kilos et 1,80 m")
check(_imc3 and _imc3.startswith("24.69"), "IMC 1,80 m -> 24.69")
# pH (brique physique.calcule, −log10) et TVA (montant ET TTC montrés, base lue HT et DITE).
check(_m("pH pour une concentration de 0,001") == "pH = 3 (−log₁₀ de 0.001)", "pH 0,001 -> 3")
check(_m("TVA de 20% sur 100 euros") == "20 de TVA (20 % de 100 HT) ; TTC : 120", "TVA 20% sur 100")
# ANGLES : degré = π/180 exact, dans les deux sens ; les températures gardent leur route dédiée.
_dr = _m("convertis 30 degrés en radians")
check(_dr and _dr.startswith("0.523599"), "30° -> 0.5236 rad")
_rd = _m("3,14 radians en degrés")
check(_rd and _rd.startswith("179.9087"), "3,14 rad -> 179.9°")
# POURBOIRE (tombait en mémo « C'est noté ») : pourboire ET total montrés.
check(_m("15% de pourboire sur 80 euros") == "12 de pourboire (15 % de 80) ; total : 92", "pourboire 15% sur 80")
_pb2 = _m("un pourboire de 10% sur 45 euros")
check(_pb2 and _pb2.startswith("4.5 de pourboire"), "pourboire de 10% sur 45 -> 4.5")
# DURÉES VARIABLES -> réponses composées honnêtes (précédent : semaines/année).
_hm = _m("combien d'heures dans un mois")
check(_hm and _hm.startswith("de 672 h") and "744" in _hm, "heures dans un mois -> composé honnête 672-744")
_js = _m("combien de jours dans un siècle")
check(_js and _js.startswith("36 524 ou 36 525"), "jours dans un siècle -> 36524/36525 grégorien")
# ROMAIN -> NOMBRE : « en nombre » / « en chiffres » seuls acceptés (seul « arabes/décimal » passait).
check(_m("MMXXVI en nombre") == "2026", "MMXXVI en nombre -> 2026")
check(_m("XIV en chiffres") == "14", "XIV en chiffres -> 14")
check(_m("mille en nombre") is None, "garde : « mille » n'est pas un nombre romain (e hors alphabet)")
# CONVERSIONS : ligature « nœuds » (NFD ne la décompose pas) + durée compacte « 2h30 ».
check(_m("10 nœuds en km/h") == "18.52 km/h", "nœuds avec ligature œ -> 18.52 km/h")
check(_m("combien de secondes dans 2h30") == "9000 secondes", "2h30 -> 9000 s")
check(_m("2h30 en minutes") == "150 minutes", "2h30 -> 150 min")
# JOURS D'UN MOIS (« février 2024 » tombait en repli) : grégorien exact, février sans année = composé honnête.
check(_m("combien de jours en février 2024") == "29 jours (février 2024)", "février 2024 -> 29")
check(_m("combien de jours en février 2023") == "28 jours (février 2023)", "février 2023 -> 28")
check(_m("combien de jours en février") == "28 jours (29 les années bissextiles).", "février sans année")
check(_m("combien de jours en avril") == "30 jours", "avril -> 30")
check(_m("dans combien de jours le 25 décembre") is None,
      "garde : compte à rebours -> pas volé par les jours du mois")
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
# VALEUR ABSOLUE / CONVERSION DE BASE / INVERSE MODULAIRE (vague 6)
check(_m("valeur absolue de -5") == "5", "valeur absolue de -5 -> 5")
check(_m("convertis 42 en binaire") == "101010", "42 en binaire -> 101010")
check(_m("42 en hexadécimal") == "2A", "42 en hexadécimal -> 2A")
check(_m("convertis 1010 binaire en décimal") == "10", "1010 binaire -> 10 (décimal)")
check(_m("2A hexadécimal en décimal") == "42", "2A hexa -> 42 (décimal)")
check(_m("inverse de 7 modulo 13") == "2", "inverse modulaire 7 mod 13 -> 2")
check(_m("inverse de 6 modulo 9") is None, "6 non inversible mod 9 (pgcd≠1) -> abstention honnête")
check(_m("valeur de la maison") is None, "« valeur de X » (sans « absolue ») ne déclenche PAS (garde)")
# BISSEXTILE / JOURS D'UNE ANNÉE / OPÉRATIONS NOMMÉES / DÉCIMALES DE CONVERSION (vague 11).
_c = lambda t: (lambda r: r[1] if r[0] == _V else None)(FN.resout_conversion(t))

# VÉRIFICATIONS NUMÉRIQUES / FRACTIONS / DIVISEURS / PREMIERS D'INTERVALLE / UNITÉS (vague 12).
check(_m("est-ce que 7 est un nombre pair") == "Non, 7 n'est pas pair.", "7 pair -> Non")
check(_m("17 est-il impair") == "Oui, 17 est impair.", "17 impair -> Oui")
check(_m("est-ce que 15 est divisible par 3") == "Oui, 15 est divisible par 3 (3 × 5).", "15 divisible par 3")
check(_m("est-ce que 21 est un multiple de 7") is not None and "Oui" in _m("est-ce que 21 est un multiple de 7"),
      "21 multiple de 7 -> Oui")
check(_m("est-ce que 100 est un carré parfait") == "Oui, 100 est un carré parfait (10²).", "100 carré parfait")
_r = _m("est-ce que 50 est un carré parfait")
check(_r is not None and _r.startswith("Non") and "49" in _r and "64" in _r, "50 -> Non, encadré par 49 et 64")
check(_m("lequel est le plus grand : 2/3 ou 3/5") == "2/3 est plus grand (2/3 > 3/5).",
      "fractions comparées EXACTEMENT (plus jamais « Minimum : 2 ; maximum : 5 »)")
check(_m("4/8 ou 1/2, lequel est le plus grand") == "Ils sont égaux (4/8 = 1/2).", "4/8 = 1/2 (égalité exacte)")
check(_m("0.5 est-il égal à 1/2") == "Oui, 0.5 = 1/2.", "décimal = fraction (exact)")
check(_m("le produit de 4 et 25") == "100", "produit de 4 et 25 -> 100")
check(_m("la différence de 100 et 58") == "42", "différence de 100 et 58 -> 42")
check(_m("le quotient de 100 et 7") is None, "quotient non entier -> abstention")
_r = _m("les diviseurs de 36")
check(_r is not None and "9 diviseurs" in _r and "1, 2, 3, 4, 6, 9, 12, 18, 36" in _r, "diviseurs de 36 (énumérés)")
check(_m("un nombre premier entre 20 et 30") == "Entre 20 et 30 : 23, 29.",
      "premiers entre 20 et 30 -> 23, 29 (plus jamais « Non, 20 n'est pas premier »)")
check(_m("nombres premiers entre 24 et 28") == "Aucun nombre premier entre 24 et 28.", "intervalle sans premier")
check(_c("convertis 3 hectares en m2") == "30000 m2", "3 ha -> 30000 m²")
check(_c("2 gigaoctets en mégaoctets") == "2000 megaoctets", "2 Go -> 2000 Mo (SI, convention dite en source)")
_r = _c("150 centimètres en pieds")
check(_r is not None and _r.startswith("4.92"), "150 cm -> ~4.92 pieds (0,3048 exact)")
check(_c("combien de secondes dans 2 heures et demie") == "9000 secondes",
      "2 h et demie -> 9000 s (le « et demie » n'est PLUS ignoré : 7200 était FAUX)")
_r = _c("combien de semaines dans une année")
check(_r is not None and _r.startswith("52 semaines et 1 jour"), "semaines/année -> réponse composée honnête")
_r = _m("est-ce que 2024 est une année bissextile")
check(_r is not None and _r.startswith("Oui, 2024"), "2024 bissextile -> Oui (règle grégorienne, plus JAMAIS « 2010 » du film)")
_r = _m("2023 est-elle une année bissextile")
check(_r is not None and _r.startswith("Non, 2023"), "2023 -> Non")
_r = _m("est-ce que 2100 est une année bissextile")
check(_r is not None and _r.startswith("Non, 2100"), "2100 (siècle non divisible par 400) -> Non")
_r = _m("nombre de jours en 2024")
check(_r is not None and _r.startswith("366"), "2024 -> 366 jours")
_r = _m("combien de jours en 2023")
check(_r is not None and _r.startswith("365"), "2023 -> 365 jours")
check(_m("double de 21") == "42", "double de 21 -> 42")
check(_m("moitié de 42") == "21", "moitié de 42 -> 21")
check(_m("quart de 100") == "25", "quart de 100 -> 25")
check(_m("carré de 12") == "144", "carré de 12 -> 144")
check(_m("cube de 5") == "125", "cube de 5 -> 125")
check(_m("opposé de 7") == "-7", "opposé de 7 -> -7")
check(_m("inverse de 4") == "0.25", "inverse de 4 -> 0.25 (décimal fini)")
check(_m("inverse de 3") is None, "inverse de 3 (décimal infini) -> abstention, jamais 0.333")
check(_m("tiers de 9") == "3", "tiers de 9 -> 3")
check(_m("tiers de 10") is None, "tiers de 10 (non divisible) -> abstention")
check(_m("périmètre d'un carré de côté 5") == "20", "« carré de côté 5 » reste GÉOMÉTRIE (20, pas 25)")
check(_c("convertis 1,5 heures en minutes") == "90 minutes", "1,5 h -> 90 min (la virgule décimale n'est PLUS mangée)")
check(_c("combien de millisecondes dans une seconde") == "1000 millisecondes", "1 s -> 1000 ms")
# CONVERSIONS volume/vitesse + POURCENTAGES APPLIQUÉS + CHIFFRES ROMAINS + géométrie (vague 9).
check(_c("3 litres en centilitres") == "300 centilitres", "3 L -> 300 cL")
check(_c("90 km/h en m/s") == "25 m/s", "90 km/h -> 25 m/s (1000/3600 exact)")
check(_c("10 m/s en km/h") == "36 km/h", "10 m/s -> 36 km/h")
check(_c("20 noeuds en km/h") == "37.04 km/h", "20 nœuds -> 37.04 km/h (mille marin légal)")
check(_c("2 m3 en litres") == "2000 litres", "2 m³ -> 2000 L")
check(_c("combien de secondes dans une journée") == "86400 secondes", "1 journée -> 86400 s")
check(_c("5 litres en km") is None, "litres -> km (dimensions différentes) -> abstention")
_r = _m("20% de réduction sur 80 euros")
check(_r is not None and _r.startswith("64 (80 − 20 %"), "réduction 20 % sur 80 -> 64, calcul MONTRÉ")
_r = _m("remise de 30% sur 200")
check(_r is not None and _r.startswith("140 "), "remise 30 % sur 200 -> 140 (prix final, pas 60)")
_r = _m("augmente 200 de 15%")
check(_r is not None and _r.startswith("230 "), "augmente 200 de 15 % -> 230")
_r = _m("hausse de 10% sur 50")
check(_r is not None and _r.startswith("55 "), "hausse de 10 % sur 50 -> 55")
check(_m("150 est quel pourcentage de 600") == "25 %", "150 sur 600 -> 25 %")
check(_m("quel pourcentage de 600 représente 150") == "25 %", "forme inversée -> 25 % aussi")
check(_m("écris 1984 en chiffres romains") == "MCMLXXXIV", "1984 -> MCMLXXXIV")
# NOMBRE EN TOUTES LETTRES : ancres orthographiques vérifiées À LA MAIN (pièges : et un, vingts/cents, mille inv.)
_ANCRES_LETTRES = {21: "vingt et un", 71: "soixante et onze", 80: "quatre-vingts", 81: "quatre-vingt-un",
                   91: "quatre-vingt-onze", 100: "cent", 200: "deux cents", 201: "deux cent un",
                   1000: "mille", 1984: "mille neuf cent quatre-vingt-quatre", 2000: "deux mille",
                   80000: "quatre-vingt mille",
                   999999: "neuf cent quatre-vingt-dix-neuf mille neuf cent quatre-vingt-dix-neuf"}
for _n, _att in _ANCRES_LETTRES.items():
    check(FN._nombre_en_lettres(_n) == _att, "%d en lettres -> %s" % (_n, _att))
_r = _m("écris 1984 en lettres")
check(_r is not None and _r.startswith("mille neuf cent quatre-vingt-quatre"), "route « en lettres » câblée")
check(_m("1000000 en lettres") is None, "hors plage (>999999) -> abstention")
check(_m("que vaut XIV en chiffres arabes") == "14", "XIV -> 14")
check(_m("MCMLXXXIV en décimal") == "1984", "MCMLXXXIV -> 1984 (round-trip)")
check(_m("IIII en chiffres arabes") is None, "IIII non canonique -> abstention (round-trip strict)")
check(_m("CIVIL en chiffres arabes") is None, "un mot en lettres romaines n'est PAS un nombre (garde)")
check(_m("5000 en chiffres romains") is None, "hors plage 1..3999 -> abstention")
check(all(FN._depuis_romain(FN._en_romain(n)) == n for n in range(1, 4000)),
      "ROUND-TRIP romain complet 1..3999 (chaque valeur, aller-retour exact)")
check(_m("périmètre d'un triangle de côtés 3, 4 et 5") == "12", "périmètre triangle 3-4-5 -> 12")
check(_m("périmètre d'un triangle de côtés 1, 1 et 5") is None,
      "triangle 1-1-5 IMPOSSIBLE (inégalité triangulaire) -> abstention, pas une somme aveugle")
check(_m("aire d'un losange de diagonales 6 et 8") == "24", "aire losange d=6,8 -> 24 (d₁·d₂/2, Polygone)")
check(_m("le prix a augmenté de beaucoup") is None, "« augmenté de beaucoup » (pas de %) ne déclenche RIEN")
check(_m("la réduction des inégalités sur le continent") is None, "« réduction des inégalités » ne déclenche RIEN")
# VAGUE 22 : zéros d'un grand nombre (la congélation de l'eau est un fait base_faits, testé dans valide_base_faits).
_r = _m("combien de zéros dans un million")
check(_r is not None and _r.startswith("6 zéros"), "zéros d'un million -> 6")
_r = _m("combien de zéros dans un milliard")
check(_r is not None and _r.startswith("9 zéros"), "zéros d'un milliard -> 9")
# VAGUE 21 : volume cylindre/cône, aire trapèze, kilo -> grammes.
_r = _m("volume d'un cylindre de rayon 2 et hauteur 5")
check(_r is not None and _r.startswith("62.83"), "volume cylindre r=2 h=5 -> 62.83 (π·r²·h)")
_r = _m("volume d'un cône de rayon 3 et hauteur 6")
check(_r is not None and _r.startswith("56.54"), "volume cône r=3 h=6 -> 56.55 (π·r²·h/3)")
check(_m("aire d'un trapèze de bases 4 et 6 et hauteur 3") == "15", "aire trapèze b=4,6 h=3 -> 15")
check(_c("combien de grammes dans 2 kilos") == "2000 grammes", "2 kilos -> 2000 grammes (kilo = kg courant)")
check(_c("combien de grammes dans un kilo") == "1000 grammes", "1 kilo -> 1000 grammes")
# VAGUE 20 : comparaison directe, extremum, tri de nombres (la route stats min/max ne les coiffe plus).
_r = _m("est-ce que 8 est plus grand que 5")
check(_r is not None and _r.startswith("Oui"), "« 8 plus grand que 5 » -> Oui (plus « Minimum:5 max:8 »)")
_r = _m("est-ce que 3 est supérieur à 10")
check(_r is not None and _r.startswith("Non"), "« 3 supérieur à 10 » -> Non")
check(_m("quel est le plus grand entre 7 et 12") == "12", "extremum : plus grand entre 7 et 12 -> 12")
check(_m("quel est le plus petit de 5, 2 et 9") == "2", "extremum : plus petit de 5,2,9 -> 2")
check(_m("classe 3, 1 et 2 par ordre croissant") == "1, 2, 3 (ordre croissant)", "tri croissant")
check(_m("range 5, 2, 8, 1 du plus petit au plus grand") == "1, 2, 5, 8 (ordre croissant)", "tri « du plus petit »")
check(_m("trie 9, 3, 7 par ordre décroissant") == "9, 7, 3 (ordre décroissant)", "tri décroissant")
# VAGUE 19 : fractions (simplifier, ↔%, ←décimal), pourcentage inverse, prix avant réduction, arrondi à un rang.
check(_m("simplifie la fraction 6/8") == "3/4 (= 6/8)", "simplifier 6/8 -> 3/4")
check(_m("simplifie 10/5") == "2 (= 10/5)", "simplifier 10/5 -> 2 (entier)")
check(_m("convertis 3/4 en pourcentage") == "75 %", "3/4 en % -> 75 %")
check(_m("1/8 en pourcent") == "12.5 %", "1/8 en % -> 12.5 %")
check(_m("0,25 en fraction") == "1/4", "0,25 en fraction -> 1/4")
check(_m("40 est 20% de quel nombre") == "200", "pourcentage inverse : 40 = 20% de 200")
_r = _m("un article coûte 120 après 20% de réduction, quel était son prix")
check(_r is not None and _r.startswith("150"), "prix avant réduction : 120 après -20% -> 150")
check(_m("arrondis 347 à la centaine") == "300", "arrondi 347 à la centaine -> 300")
check(_m("arrondis 2851 au millier") == "3000", "arrondi 2851 au millier -> 3000")
check(_m("arrondi 1234 à la dizaine") == "1230", "arrondi 1234 à la dizaine -> 1230")
# PARTAGE / ARITHMÉTIQUE DÉCIMALE (opérateur explicite seulement, garde anti-FP forte).
check(_m("partage 20 euros entre 4 personnes") == "5 chacun (20 ÷ 4)", "partage 20/4 -> 5 chacun")
_r = _m("partage 20 euros entre 3 personnes")
check(_r is not None and "6 chacun, et il reste 2" in _r, "partage 20/3 -> 6 chacun + reste 2 (exact)")
check(_m("20 - 7,50") == "12.5", "20 − 7,50 -> 12.5 (décimal)")
check(_m("12,50 - 4") == "8.5", "12,50 − 4 -> 8.5")
check(_m("la guerre de 1939-1945") is None, "« 1939-1945 » (dates) n'est PAS une soustraction (garde)")
check(_m("distance 1,5 km") is None, "« distance 1,5 km » n'est PAS un calcul (garde)")
# VAGUE 17 : écart en %, facteurs premiers, nombre parfait, an/heure, règle de trois, diagonale, triangle équilatéral.
check(_m("le plus grand diviseur commun de 24 et 36") == "12",
      "« le plus grand diviseur commun » -> 12 (PGCD, plus « Minimum : 24 ; maximum : 36 »)")
_r = _m("de combien de % 40 est plus grand que 25")
check(_r is not None and _r.startswith("60 %"), "écart relatif : 40 vs 25 -> +60 %")
check(_m("décompose 60 en facteurs premiers") == "60 = 2² × 3 × 5", "facteurs premiers de 60")
check(_m("facteurs premiers de 100") == "100 = 2² × 5²", "facteurs premiers de 100")
_r = _m("est-ce que 28 est un nombre parfait")
check(_r is not None and _r.startswith("Oui, 28"), "28 est parfait")
_r = _m("est-ce que 12 est un nombre parfait")
check(_r is not None and _r.startswith("Non, 12"), "12 n'est pas parfait")
_r = _m("1 an en jours")
check(_r is not None and _r.startswith("365"), "1 an -> 365 jours (année commune, dit)")
check(_m("combien de minutes dans 2h30") == "150 minutes", "2h30 -> 150 minutes")
check(_m("si 3 pommes coûtent 2 euros, combien coûtent 9 pommes") == "6", "règle de trois -> 6")
_r = _m("diagonale d'un carré de côté 5")
check(_r is not None and _r.startswith("≈ 7.07"), "diagonale carré c=5 -> ≈7.07 (côté·√2, dit approché)")
_r = _m("aire d'un triangle équilatéral de côté 6")
check(_r is not None and _r.startswith("≈ 15.58"), "aire triangle équilatéral c=6 -> ≈15.59")
# RANGS / SUCCESSIONS / DIVISIONS DU TEMPS (vague 16) : conventions de cycles fermés.
_c = lambda t: (lambda r: r[1] if r[0] == _V else None)(FN.resout_conversion(t))

# ROBUSTESSE AUX VARIANTES (passe adverse 2026-07-08 : « c'est »/« sera-t-elle » faisaient REVENIR le film 2010).
_r = _m("est-ce que 2024 c'est une année bissextile")
check(_r is not None and _r.startswith("Oui, 2024"), "« 2024 c'est une année bissextile » -> Oui (plus jamais 2010)")
_r = _m("2028 sera-t-elle bissextile")
check(_r is not None and _r.startswith("Oui, 2028"), "« sera-t-elle » (futur + t euphonique) -> Oui")
check(_m("XIV ça fait combien en chiffres arabes") == "14", "« XIV ça fait combien en… » -> 14")
_r = _m("20 % de réduc sur 80 euros")
check(_r is not None and _r.startswith("64 "), "« réduc » (familier) -> 64")
check(_m("quel est le 5e mois de l'année") == "Mai (5e mois de l'année)", "5e mois -> Mai")
_r = _m("le 13e mois de l'année")
check(_r is not None and "que 12 mois" in _r, "13e mois -> correction honnête (12 mois), plus de mémo garbage")
check(_m("quel jour vient après mardi") == "Mercredi", "après mardi -> Mercredi")
check(_m("quel jour vient après dimanche") == "Lundi (la semaine reboucle)", "après dimanche -> Lundi (reboucle)")
check(_m("quelle lettre vient après le m") == "n", "après m -> n")
_r = _m("quelle lettre vient après le z")
check(_r is not None and "dernière lettre" in _r, "après z -> aucune (dite)")
check(_m("combien de trimestres dans une année") == "4", "trimestres/année -> 4")
check(_m("combien d'années dans un siècle") == "100", "années/siècle -> 100")
check(_m("combien de siècles dans un millénaire") == "10", "siècles/millénaire -> 10")
check(_m("combien de mois dans une année") == "12", "mois/année -> 12")
# COMPARAISON DE GRANDEURS (partagée avec _cap_comparaison) — via resout_conversion.
check(_c("lequel est le plus rapide : 100 km/h ou 30 m/s") is not None
      and _c("lequel est le plus rapide : 100 km/h ou 30 m/s").startswith("30 m/s est plus rapide"),
      "100 km/h vs 30 m/s -> 30 m/s (conversion exacte montrée)")
check(_c("36 km/h ou 10 m/s, lequel est le plus rapide") == "Ils sont égaux (36 km/h = 10 m/s après conversion).",
      "36 km/h = 10 m/s -> égaux")
check(_c("plus léger : 500 g ou 1 kg") is not None and _c("plus léger : 500 g ou 1 kg").startswith("500 g est plus"),
      "« plus léger » inverse le gagnant")
check(_c("plus rapide : 10 km ou 3 kg") is None, "dimensions différentes -> abstention")
# ANGLES / CERCLE (vague 15) : conventions euclidienne exactes, formule montrée.
_r = _m("somme des angles d'un triangle")
check(_r is not None and _r.startswith("180°"), "somme des angles d'un triangle -> 180°")
_r = _m("somme des angles d'un hexagone")
check(_r is not None and _r.startswith("720°"), "somme des angles d'un hexagone -> 720° ((n−2)·180)")
_r = _m("combien de degrés dans un cercle")
check(_r is not None and _r.startswith("360°"), "cercle -> 360°")
_r = _m("combien de degrés dans un demi-cercle")
check(_r is not None and _r.startswith("180°"), "demi-cercle -> 180°")
check(_m("combien de degrés fait-il dehors") is None, "« degrés dehors » (météo) pas volé (garde)")
# RACINE CUBIQUE / LOG EN BASE / ARRONDI (vague 8) : exact seulement, abstention sinon (jamais d'à-peu-près).
check(_m("racine cubique de 27") == "3", "racine cubique de 27 -> 3 (cube parfait)")
check(_m("racine cubique de -8") == "-2", "racine cubique de -8 -> -2")
check(_m("racine cubique de 30") is None, "racine cubique de 30 (pas un cube) -> abstention, JAMAIS 3.107")
check(_m("log de 100 en base 10") == "2", "log 100 base 10 -> 2")
check(_m("logarithme de 8 en base 2") == "3", "log 8 base 2 -> 3")
check(_m("log de 100 en base 3") is None, "log 100 base 3 (non entier) -> abstention")
check(_m("log de 1000") is None, "log sans base explicite -> abstention (on ne devine pas ln/log10)")
check(_m("arrondi de 3.7") == "4", "arrondi de 3.7 -> 4")
check(_m("arrondis 2,5") == "3", "arrondi de 2,5 -> 3 (demi-supérieur, pas l'arrondi bancaire)")
check(_m("arrondi de 3.14159 à 2 décimales") == "3.14", "arrondi à 2 décimales -> 3.14")
check(_m("partie entière de 5.9") == "5", "partie entière de 5.9 -> 5")
check(_m("partie entière de -2.3") == "-3", "partie entière de -2.3 -> -3 (plancher, définition math)")
check(_m("plafond de 3.2") == "4", "plafond de 3.2 -> 4")
check(_m("le plafond de 3 mètres") is None, "« plafond de 3 mètres » (entier, hauteur) ne déclenche PAS (garde)")
check(_m("l'arrondissement de Paris") is None, "« arrondissement » ne déclenche PAS l'arrondi (garde)")
# GÉOMÉTRIE SIMPLE (vague 7) : aire/périmètre/volume/hypoténuse via geometrie2d/3d (brique vérifiée).
check(_m("aire d'un cercle de rayon 3") == "28.2743", "aire cercle r=3 -> 28.2743 (π·r², geometrie2d)")
check(_m("circonférence d'un cercle de diamètre 10") == "31.4159", "circonférence d=10 -> 31.4159")
check(_m("périmètre d'un carré de côté 4") == "16", "périmètre carré c=4 -> 16")
check(_m("aire d'un rectangle de 3 par 5") == "15", "aire rectangle 3×5 -> 15")
check(_m("périmètre d'un rectangle de longueur 5 et largeur 3") == "16", "périmètre rectangle 5×3 -> 16")
check(_m("aire d'un triangle de base 6 et hauteur 4") == "12", "aire triangle b=6 h=4 -> 12")
check(_m("hypoténuse d'un triangle rectangle de côtés 3 et 4") == "5", "hypoténuse 3-4 -> 5 (Pythagore)")
check(_m("volume d'un cube de côté 2") == "8", "volume cube c=2 -> 8 (geometrie3d)")
check(_m("volume d'une sphère de rayon 2") == "33.5103", "volume sphère r=2 -> 33.5103 (4/3·π·r³)")
# GARDE : aire/périmètre/volume NON géométriques ne déclenchent RIEN (pas de vol de questions data).
for q in ("l'aire urbaine de Toulouse", "périmètre de sécurité autour du stade", "le volume sonore de 90 décibels",
          "quelle est la superficie de la France", "aire d'un cercle", "l'aire de repos à 3 km"):
    check(_m(q) is None, "géométrie ne vole PAS « %s » (garde)" % q[:36])
# GARDE anti-faux-positif : « premier »/nombres ordinaux ne déclenchent PAS la primalité sur une question DATA.
for q in ("le premier président élu en 1958", "premier ministre depuis 2017", "premier roman de 1984",
          "quelle est la capitale de la France ?", "population du Japon en 2020", "qui a gagné en 2018"):
    check(_m(q) is None, "maths ne vole PAS « %s » (faux positif interdit)" % q[:34])

print(f"\n=== valide_assistant_nl : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
