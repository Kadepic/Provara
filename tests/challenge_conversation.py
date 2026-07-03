# -*- coding: utf-8 -*-
"""HARNAIS DE CHALLENGE CONVERSATIONNEL — boucle adverse (mandat Yohan 2026-07-03).

But : soumettre à VERAX des énoncés de complexité et de registre CROISSANTS (courant / technique / soutenu /
multi-domaine), classer sa réponse par CLASSE DE COMPORTEMENT (pas par texte exact) et faire ressortir les
ÉCHECS RÉELS — un vrai message qui tombe sur un repli générique (« famille inconnue », « C'est noté » à tort),
ou une réponse manifestement à côté du sujet.

Ce n'est PAS une gate FAUX=0 (le web bouge, les réponses varient) : c'est un TABLEAU DE BORD. Chaque tour de la
boucle « challenge -> échec -> brique -> re-challenge » ajoute ici des énoncés. Objectif de la campagne :
zéro ÉCHEC sur des demandes légitimes, jusqu'à la compréhension de textes longs.

Exécution :  PYTHONPATH="interface:src:ingestion" python3 tests/challenge_conversation.py
             (léger : LECTEUR_AMORCE_SEULE=1 -> pas de chargement lourd ; le web reste optionnel).
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "ingestion"))

import conversation
import repond as R

# ————————————————————————— Classes de comportement (par reconnaissance du texte terminal) —————————————————————————
SOCIAL, FACTUEL, SUBJECTIF, CLARIF, ABSTENTION, MEMO, FALLBACK, META, AUTRE = (
    "SOCIAL", "FACTUEL", "SUBJECTIF", "CLARIF", "ABSTENTION", "MEMO", "FALLBACK", "META", "AUTRE")


OUTIL = "OUTIL"   # capacité outil câblée (grammaire, conjugaison, stats, graphique, invention…)


def classe(rep: str) -> str:
    """Range la réponse dans une classe de comportement (heuristique de SURFACE, tolérante)."""
    if not rep:
        return AUTRE
    b = rep.lower()
    # repli d'échec : ce qu'on veut faire DISPARAÎTRE sur les demandes légitimes
    if ("je ne sais pas encore traiter cette famille" in b
            or b.startswith("je n'arrive pas à rattacher")):
        return FALLBACK
    if rep == R._MSG_NOTE:
        return MEMO
    if rep.startswith("<svg") or any(s in b for s in (
            "conjugaison de", "au présent de l'indicatif", "je ne conjugue", "moyenne :", "médiane :", "écart-type",
            "proportion estimée", "taux estimé", "pente robuste", "ordre de grandeur", "miser f", "kelly",
            "regardons le besoin", "audit de sécurité", "distance entre", "type : ", "» : nom", "» : verbe",
            "» : adjectif", "» : adverbe", "je pense que ça monte", "cette valeur me semble anormale",
            "je ne suis pas certain de la nature")):
        return OUTIL
    if "d'après" in b or "trouvé sur" in b or "🔗" in rep or "d'après ce que tu m'as dit" in b:
        return FACTUEL
    if ("c'est subjectif" in b or "pas de réponse unique" in b or "question non bornée" in b
            or "ça dépend du critère" in b):
        return SUBJECTIF
    if "vouliez-vous dire" in b or "peux-tu préciser" in b or "quel critère" in b or "donne-moi un critère" in b:
        return CLARIF
    if b.startswith("je n'ai pas l'information") or "internet est coupé" in b:
        return ABSTENTION
    if any(s in b for s in ("bonjour", "je vais très bien", "à bientôt", "avec plaisir", "hello")):
        return SOCIAL
    if "je m'appelle verax" in b or "je suis un" in b or "je réponds depuis" in b:
        return META
    # réponse COURTE et directe, sans marqueur d'échec -> réponse factuelle nue (« Madrid », « Paris »)
    if 0 < len(rep.strip()) <= 60 and "\n" not in rep.strip():
        return FACTUEL
    return AUTRE


# ————————————————————————— Corpus GRADUÉ (niveau 1 = simple … niveau 5 = long/complexe) —————————————————————————
# `attendu` = ensemble des classes ACCEPTABLES (⊇1). `web` = a besoin d'internet pour bien répondre.
# `registre` : courant / technique / soutenu / mixte. Un cas ÉCHOUE s'il tombe en FALLBACK/MEMO/AUTRE hors attendu.
CAS = [
    # — Niveau 1 : social & méta (courant) —
    dict(n=1, reg="courant", q="Bonjour !", ok={SOCIAL}),
    dict(n=1, reg="courant", q="Qui es-tu ?", ok={META}),
    dict(n=1, reg="courant", q="Merci beaucoup", ok={SOCIAL}),
    # — Niveau 2 : fait simple, un attribut (courant) —
    dict(n=2, reg="courant", q="Quelle est la capitale de l'Espagne ?", ok={FACTUEL}),
    dict(n=2, reg="courant", q="qu'est ce que la canicule ?", ok={FACTUEL}, web=True),
    dict(n=2, reg="technique", q="définition de sérendipité", ok={FACTUEL}, web=True),
    # — Niveau 3 : salutation combinée + demande, superlatif d'opinion, notoriété (mixte) —
    dict(n=3, reg="courant", q="Bonjour comment vas tu ? qu'est ce que la canicule ?", ok={SOCIAL, FACTUEL}, web=True),
    dict(n=3, reg="courant", q="Qui est le rappeur le plus connu du moment ?", ok={SUBJECTIF, CLARIF}),
    dict(n=3, reg="courant", q="Quel est le plus beau pays du monde ?", ok={SUBJECTIF, CLARIF}),
    # — Niveau 4 : intention + sujet à extraire, registre technique/soutenu —
    dict(n=4, reg="courant", q="Peux tu me dire quelle boisson serait vraiment rafraichissante en temps de canicule ?",
         ok={FACTUEL, SUBJECTIF, CLARIF}, web=True),
    dict(n=4, reg="technique", q="Comment fonctionne une pompe à chaleur air-eau ?", ok={FACTUEL}, web=True),
    dict(n=4, reg="soutenu", q="Pourriez-vous m'exposer les tenants de la photosynthèse ?", ok={FACTUEL}, web=True),
    dict(n=4, reg="technique", q="Qu'est-ce que l'apoptose cellulaire ?", ok={FACTUEL}, web=True),
    # — Niveau 5 : phrases longues, multi-clause, multi-domaine —
    dict(n=5, reg="mixte", q="J'aimerais comprendre en quoi la relativité restreinte a bouleversé "
         "notre conception du temps et de l'espace au début du vingtième siècle.", ok={FACTUEL}, web=True),
    dict(n=5, reg="soutenu", q="Quelles furent les conséquences économiques du traité de Versailles "
         "sur l'Allemagne de l'entre-deux-guerres ?", ok={FACTUEL}, web=True),
    dict(n=5, reg="technique", q="Explique-moi le rôle des mitochondries dans la respiration cellulaire "
         "et la production d'ATP.", ok={FACTUEL}, web=True),

    # — CAPACITÉS OUTILS câblées (grammaire, conjugaison, stats, graphique, invention, distance) —
    dict(n=2, reg="courant", q="quelle est la nature du mot chat ?", ok={OUTIL}),
    dict(n=3, reg="soutenu", q="quelle est la nature grammaticale du vocable « nonobstant » ?", ok={OUTIL, ABSTENTION}),
    dict(n=2, reg="courant", q="conjugue le verbe parler", ok={OUTIL}),
    dict(n=3, reg="courant", q="conjugue le verbe manger", ok={OUTIL}),   # abstention honnête (particularité)
    dict(n=2, reg="technique", q="quelle est la moyenne de 12, 15, 14, 13, 16, 12 ?", ok={OUTIL}),
    dict(n=3, reg="technique", q="est-ce que la série 100, 102, 101, 105, 108, 110 est en hausse ?", ok={OUTIL}),
    dict(n=3, reg="technique", q="j'ai 37 succès sur 100, quel est l'intervalle de confiance ?", ok={OUTIL}),
    dict(n=3, reg="technique", q="je gagne avec proba 0.55 à une cote de 2, combien parier avec Kelly ?", ok={OUTIL}),
    dict(n=2, reg="courant", q="trace un graphique en barres de 3, 5, 8, 2", ok={OUTIL}),
    dict(n=4, reg="soutenu", q="comment rafraîchir une pièce sans recourir à un climatiseur ?", ok={OUTIL, FACTUEL}, web=True),
    # distance : nécessite le lecteur COMPLET (coordonnées) ; en mode léger de test -> abstention honnête tolérée
    dict(n=3, reg="courant", q="distance entre Paris et Madrid", ok={OUTIL, ABSTENTION}),

    # — Registre SOUTENU / TECHNIQUE pur (factuel via web) —
    dict(n=4, reg="soutenu", q="Qu'entend-on par « sérendipité » ?", ok={FACTUEL}, web=True),
    dict(n=4, reg="technique", q="Qu'est-ce que la supraconductivité ?", ok={FACTUEL}, web=True),
    dict(n=5, reg="technique", q="Décris le mécanisme de la réaction de Maillard en cuisine.", ok={FACTUEL}, web=True),
]


def run(avec_web: bool):
    mem = conversation.MemoireConversation(racine=None)
    if avec_web:
        os.environ["IA_WEB"] = "1"
    resultats = []
    for i, cas in enumerate(CAS):
        if cas.get("web") and not avec_web:
            continue
        rep = R.repond(mem, "challenge", cas["q"], pleine=True)
        c = classe(rep)
        echec = c not in cas["ok"]
        resultats.append((cas, c, echec, rep))
    return resultats


def rapporte(resultats):
    parN, parReg = {}, {}
    echecs = []
    for cas, c, echec, rep in resultats:
        parN.setdefault(cas["n"], [0, 0]); parReg.setdefault(cas["reg"], [0, 0])
        parN[cas["n"]][1] += 1; parReg[cas["reg"]][1] += 1
        if not echec:
            parN[cas["n"]][0] += 1; parReg[cas["reg"]][0] += 1
        else:
            echecs.append((cas, c, rep))
    total = len(resultats)
    reussis = total - len(echecs)
    print("\n=== CHALLENGE CONVERSATIONNEL : %d/%d comportements attendus ===" % (reussis, total))
    print("par niveau :", " ".join("N%d %d/%d" % (n, a, b) for n, (a, b) in sorted(parN.items())))
    print("par registre :", " ".join("%s %d/%d" % (r, a, b) for r, (a, b) in sorted(parReg.items())))
    if echecs:
        print("\n--- ÉCHECS (demande légitime mal traitée) ---")
        for cas, c, rep in echecs:
            print("  [N%d %s] %s" % (cas["n"], cas["reg"], cas["q"]))
            print("     attendu %s, obtenu %s : %s" % ("/".join(sorted(cas["ok"])), c, rep[:110].replace("\n", " ")))
    return reussis, total


if __name__ == "__main__":
    avec_web = os.environ.get("IA_WEB") == "1" or "--web" in sys.argv
    res = run(avec_web)
    r, t = rapporte(res)
    print("\n(mode %s — %s)" % ("AVEC web" if avec_web else "SANS web (cas web ignorés)",
                                "relancer avec --web pour les cas factuels en ligne"))
    sys.exit(0 if r == t else 1)
