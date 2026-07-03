"""VALIDE classifieur_bornage.py — le routeur de statut : sound par construction (route, n'affirme pas), conservateur.

Ancres : question à juge -> BORNÉ+JUGE (fait) ; question factuelle sans juge -> BORNÉ+PAS_DE_JUGE (à chercher) ;
question de goût/opinion/futur/fiction -> NON_BORNÉ (supposition) ; question ambiguë -> INDÉCIDABLE -> non-borné.
Invariant FAUX=0 : R_FAIT (le seul chemin qui affirme) n'est atteint QUE via un juge réel, jamais par marqueur seul.
"""
import classifieur_bornage as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k); return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) JUGE RÉEL fourni -> borné + accessible (prime le mot ambigu) ──
r = C.classe("quel est le meilleur coup dans cette position d'échecs ?", juge_verdict=True, juge_nom="minimax")
check(r.statut_ontologique == C.BORNE and r.acces == C.JUGE_DISPO and r.regime == C.R_FAIT,
      "juge réel positif -> BORNÉ+JUGE (le résultat prime le mot 'meilleur')")
check(r.route_fait() is True, "route_fait() True seulement avec juge")

# ── 2) calcul arithmétique = juge interne ──
r = C.classe("combien font 17 * 23 ?")
check(r.regime == C.R_FAIT and r.acces == C.JUGE_DISPO, "calcul arithmétique -> juge interne -> FAIT")

# ── 3) prédicats BORNÉS positifs sans juge -> vérité existe, à chercher ──
for q in ("quelle est la population de Paris ?", "en quelle année est mort Napoléon ?",
          "quelle est la capitale du Kazakhstan ?", "qui a inventé le téléphone ?",
          "qu'est-ce que l'entropie ?", "qu'est-ce qu'une fonction récursive ?",
          "qu'est-ce qu'un nombre premier ?"):
    r = C.classe(q)
    check(r.statut_ontologique == C.BORNE and r.acces == C.PAS_DE_JUGE and r.regime == C.R_SUPPOSITION_A_CHERCHER,
          f"borné sans juge -> à chercher : {q!r}")
    check(r.route_fait() is False, f"borné sans juge n'affirme PAS un fait : {q!r}")

# ── 4) prédicats NON-BORNÉS -> supposition calibrée (opinion) ──
for q in ("quelle est la plus belle ville du monde ?", "préfères-tu le thé ou le café ?",
          "devrait-on interdire les voitures en ville ?", "qui va gagner la présidentielle en 2050 ?",
          "invente une histoire de dragons", "à ton avis, ce film est-il bon ?"):
    r = C.classe(q)
    check(r.statut_ontologique == C.NON_BORNE and r.regime == C.R_SUPPOSITION_OPINION, f"non-borné -> opinion : {q!r}")
    check(r.route_fait() is False, f"non-borné n'affirme jamais un fait : {q!r}")

# ── 5) le mot non-borné PRÉEMPTE le prédicat borné faible (mais pas un juge réel) ──
r = C.classe("quelle est la meilleure capitale ?")   # 'capitale' (borné) MAIS 'meilleure' (non-borné dur)
check(r.statut_ontologique == C.NON_BORNE, "'meilleure X' -> non-borné (le jugement préempte le prédicat factuel)")

# ── 6) INDÉCIDABLE -> non-borné conservateur (jamais borné au doute) ──
r = C.classe("raconte")
check(r.statut_ontologique == C.INDECIDABLE and r.regime == C.R_SUPPOSITION_OPINION, "aucun signal -> INDÉCIDABLE -> non-borné")
check(r.route_fait() is False, "indécidable n'affirme jamais un fait (conservateur)")

# ── 7) juge fourni NÉGATIF : borné mais non tranché -> à chercher/HORS, jamais un fait affirmé ──
r = C.classe("quelle est la population de Paris ?", juge_verdict=False)
check(r.statut_ontologique == C.BORNE and r.route_fait() is False, "juge négatif -> borné mais pas de fait affirmé")

# ── 8) INVARIANT FAUX=0 : R_FAIT n'est JAMAIS atteint sans juge (aucun marqueur seul n'affirme) ──
import re
sans_juge_donnent_fait = [q for q in (
    "quelle est la population de Paris ?", "quelle est la plus belle ville ?", "qui a inventé le téléphone ?",
    "raconte", "préfères-tu le thé ?") if C.classe(q).regime == C.R_FAIT]
check(sans_juge_donnent_fait == [], "AUCUN marqueur seul (sans juge/calcul) ne route vers R_FAIT (anti-hallucination)")

# ── 9) FAUX=0 entrée ──
check(leve(C.classe, ""), "question vide -> ValueError")
check(leve(C.classe, None), "question None -> ValueError")

# ── 10) NON-RÉGRESSION passe adversariale : le faux juge arith (verbe « calculer », plages « 1990-2000 ») ──
#     ne doit JAMAIS router une opinion/prédiction/fiction vers R_FAIT sans vrai calcul évalué.
for q in ("A ton avis, comment calculer le bonheur ?", "Devrait-on calculer la valeur d'une vie humaine ?",
          "Quel est le meilleur album des années 1990-2000 ?", "Que va-t-il se passer entre 2050-2100 ?",
          "Penses-tu que 1+1 fasse le bonheur ?", "Calcule si Dieu existe.",
          "Préfères-tu calculer ou rêver ?", "Qui va gagner en 2026-2027 ?"):
    check(C.classe(q).regime != C.R_FAIT, f"non-régression grave : jamais R_FAIT sans vrai calcul : {q!r}")
# un VRAI calcul reste un fait (juge interne qui évalue réellement)
for q in ("combien font 17 * 23 ?", "calcule 100 / 4", "7*7"):
    check(C.classe(q).regime == C.R_FAIT, f"vrai calcul évalué -> FAIT : {q!r}")
# marqueur d'évaluation ajouté : « le mieux » préempte le prédicat de lieu
check(C.classe("dans quel pays vit-on le mieux ?").statut_ontologique == C.NON_BORNE, "'vit-on le mieux' -> non-borné")

print(f"\n=== valide_classifieur_bornage : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
