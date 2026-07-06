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

# — INVENTION (léger : besoin.py) —
r = R._cap_invention("comment rafraîchir une pièce sans climatiseur ?")
check(r and ("BESOIN" in r or "but réel" in r or "but reel" in r.lower()), "invention : reformulation physique du besoin")
check(R._cap_invention("quelle est la capitale de l'Italie ?") is None, "invention : ne capte pas une question factuelle")
check(R._cap_invention("comment dire bonjour sans accent ?") is None, "invention : besoin hors catalogue physique -> None (pipeline continue)")

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
finally:
    R._valeur_attr = _valeur_avant

print("=== valide_capacites_chat : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
