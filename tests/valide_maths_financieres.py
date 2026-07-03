"""
VALIDE maths_financieres.py — held-out ADVERSE.

Ancres = cas CONNUS de la valeur-temps de l'argent, calculés INDÉPENDAMMENT (arithmétique brute / valeurs
de manuel hand-verifiable), JAMAIS re-dérivés en appelant la fonction du module testé :
  • intérêt simple   I = C·t·n            (1000 à 5 % sur 2 ans = 100 d'intérêt, valeur acquise 1100) ;
  • intérêt composé  Vn = C·(1+t)^n       (1000 à 5 % composé 2 ans = 1102.5 ; 1000 à 10 % sur 3 ans = 1331) ;
  • valeur actuelle  V0 = VF/(1+t)^n      (round-trip : actualiser 1102.5 à 5 %/2 ans -> 1000) ;
  • annuité de prêt  a = C·t/(1−(1+t)^−n)  (10000 à 1 %/mois sur 12 ≈ 888.49 ; cas t=0 -> C/n exact) ;
  • VAN              Σ flux_i/(1+t)^i      (taux 0 = simple somme ; taux 10 % discounté).
+ SOUNDNESS : C<0 / VF<0, taux ≤ −1, n<0 (ou n≤0 pour l'annuité), booléen, str, NaN, inf, flux vide/non numérique
  -> ValueError (abstention, jamais un faux).
+ DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""
import math

import maths_financieres as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def _r(x):
    """Réplique l'arrondi au centime du module, pour comparer en non-circulaire."""
    return round(x, 2) + 0.0


TOL = 1e-9   # comparaison après arrondi identique des deux côtés

# ── 1) INTÉRÊT SIMPLE — montant et valeur acquise (ancres entières exactes) ──
check(M.interet_simple(1000, 0.05, 2) == 100.0, "intérêt simple : 1000·0,05·2 = 100")
check(M.interet_simple(5000, 0.03, 4) == 600.0, "intérêt simple : 5000·0,03·4 = 600")
check(M.interet_simple(1000, 0.05, 0) == 0.0, "intérêt simple : n=0 -> 0 (pas de temps)")
check(M.interet_simple(2500, 0, 3) == 0.0, "intérêt simple : taux=0 -> 0")
check(M.valeur_acquise_simple(1000, 0.05, 2) == 1100.0, "valeur acquise simple : 1000·(1+0,1) = 1100")
check(M.valeur_acquise_simple(2000, 0.04, 3) == 2240.0, "valeur acquise simple : 2000·1,12 = 2240")
check(M.valeur_acquise_simple(1000, 0.05, 0) == 1000.0, "valeur acquise simple : n=0 -> capital intact")

# ── 2) INTÉRÊT COMPOSÉ / VALEUR ACQUISE-FUTURE (ancres de manuel) ──
check(M.interet_compose(1000, 0.05, 2) == 1102.5, "composé : 1000·1,05² = 1102,5")
check(M.interet_compose(1000, 0.10, 3) == 1331.0, "composé : 1000·1,1³ = 1331")
check(M.interet_compose(1000, 0.05, 0) == 1000.0, "composé : n=0 -> capital intact")
check(M.interet_compose(1000, -0.10, 2) == 810.0, "composé taux négatif : 1000·0,9² = 810")
check(M.valeur_acquise(1000, 0.05, 2) == 1102.5, "valeur_acquise alias == composé")
check(M.valeur_future(1000, 0.10, 3) == 1331.0, "valeur_future alias == composé")
# le composé bat le simple à n>1 (cohérence financière, non circulaire)
check(M.interet_compose(1000, 0.05, 2) > M.valeur_acquise_simple(1000, 0.05, 2),
      "composé (1102,5) > acquis simple (1100) à 2 ans")

# ── 3) VALEUR ACTUELLE / ACTUALISATION (round-trip exact) ──
check(M.valeur_actuelle(1102.5, 0.05, 2) == 1000.0, "actualisation : 1102,5/1,05² = 1000")
check(M.valeur_actuelle(1331.0, 0.10, 3) == 1000.0, "actualisation : 1331/1,1³ = 1000")
check(M.valeur_actuelle(100, 0.05, 0) == 100.0, "actualisation : n=0 -> montant inchangé")
check(abs(M.valeur_actuelle(1000, 0.10, 1) - _r(1000 / 1.1)) < TOL, "actualisation : 1000/1,1 = 909,09")
# round-trip composé -> actualisé : on retrouve le capital
check(M.valeur_actuelle(M.interet_compose(5000, 0.07, 5), 0.07, 5) == 5000.0,
      "round-trip composé/actualisation = capital initial")

# ── 4) ANNUITÉ / MENSUALITÉ DE PRÊT ──
att = _r(10000 * 0.01 / (1 - (1.01) ** -12))      # calcul INDÉPENDANT
check(M.annuite_constante(10000, 0.01, 12) == att, "mensualité prêt 10000 à 1 %/mois sur 12 ≈ 888,49")
check(abs(M.annuite_constante(10000, 0.01, 12) - 888.49) < TOL, "mensualité = 888,49 (valeur connue)")
att2 = _r(100000 * 0.005 / (1 - (1.005) ** -240))  # prêt immobilier 100k à 0,5 %/mois sur 240
check(M.annuite_constante(100000, 0.005, 240) == att2, "prêt 100000 à 0,5 %/mois sur 240 ≈ 716,43")
check(abs(M.annuite_constante(100000, 0.005, 240) - 716.43) < TOL, "mensualité immo = 716,43 (connue)")
check(M.annuite_constante(1200, 0, 12) == 100.0, "annuité taux 0 (cas limite) : 1200/12 = 100")
check(M.annuite_constante(0, 0.01, 12) == 0.0, "annuité capital 0 -> 0")
# l'annuité × n rembourse plus que le capital quand t>0 (intérêts payés)
check(M.annuite_constante(10000, 0.01, 12) * 12 > 10000, "Σ mensualités > capital (intérêts) quand t>0")

# ── 5) VAN / NPV ──
check(M.van(0, [-100, 50, 60]) == 10.0, "VAN taux 0 : −100+50+60 = 10 (simple somme)")
att3 = _r(sum(f / (1.1) ** i for i, f in enumerate([-1000, 500, 600])))  # indépendant
check(M.van(0.1, [-1000, 500, 600]) == att3, "VAN 10 % flux [-1000,500,600] ≈ −49,59")
check(abs(M.van(0.1, [-1000, 500, 600]) - (-49.59)) < TOL, "VAN = −49,59 (valeur connue)")
check(M.van(0.1, [500]) == 500.0, "VAN flux unique en t=0 = flux non actualisé")
check(M.van(0.05, (-1000, 1102.5, 0)) == 50.0, "VAN tuple : −1000 + 1102,5/1,05 = 50")
check(M.npv(0.1, [-1000, 500, 600]) == M.van(0.1, [-1000, 500, 600]), "npv alias == van")
check(M.van(0, [200]) == 200.0, "VAN taux 0 flux unique = flux")

# ── 6) SOUNDNESS — capital / valeur future négatif -> ValueError ──
check(_leve_v(M.interet_simple, -1, 0.05, 2), "intérêt simple : C<0 -> ValueError")
check(_leve_v(M.valeur_acquise_simple, -1, 0.05, 2), "acquis simple : C<0 -> ValueError")
check(_leve_v(M.interet_compose, -5, 0.05, 2), "composé : C<0 -> ValueError")
check(_leve_v(M.valeur_acquise, -5, 0.05, 2), "valeur_acquise : C<0 -> ValueError")
check(_leve_v(M.valeur_future, -5, 0.05, 2), "valeur_future : C<0 -> ValueError")
check(_leve_v(M.valeur_actuelle, -1, 0.05, 2), "actualisation : VF<0 -> ValueError")
check(_leve_v(M.annuite_constante, -1, 0.01, 12), "annuité : C<0 -> ValueError")

# ── 7) SOUNDNESS — taux ≤ −1 (≤ −100 %) -> ValueError ──
check(_leve_v(M.interet_simple, 1000, -1, 2), "intérêt simple : taux=-1 -> ValueError")
check(_leve_v(M.interet_compose, 1000, -1, 2), "composé : taux=-1 -> ValueError")
check(_leve_v(M.interet_compose, 1000, -1.5, 2), "composé : taux=-1,5 -> ValueError")
check(_leve_v(M.valeur_actuelle, 1000, -1, 2), "actualisation : taux=-1 -> ValueError")
check(_leve_v(M.annuite_constante, 10000, -1, 12), "annuité : taux=-1 -> ValueError")
check(_leve_v(M.van, -1, [-100, 50, 60]), "VAN : taux=-1 -> ValueError")
check(_leve_v(M.van, -2, [-100, 50, 60]), "VAN : taux=-2 -> ValueError")
# taux entre -1 et 0 est VALIDE (taux négatif réel) : ne doit PAS lever
check(not _leve_v(M.interet_compose, 1000, -0.1, 2), "composé : taux=-0,1 valide (ne lève pas)")

# ── 8) SOUNDNESS — n invalide -> ValueError ──
check(_leve_v(M.interet_simple, 1000, 0.05, -1), "intérêt simple : n<0 -> ValueError")
check(_leve_v(M.interet_compose, 1000, 0.05, -1), "composé : n<0 -> ValueError")
check(_leve_v(M.valeur_actuelle, 1000, 0.05, -1), "actualisation : n<0 -> ValueError")
check(_leve_v(M.annuite_constante, 10000, 0.01, 0), "annuité : n=0 -> ValueError (division)")
check(_leve_v(M.annuite_constante, 10000, 0.01, -3), "annuité : n<0 -> ValueError")

# ── 9) SOUNDNESS — types invalides (bool / str / NaN / inf) -> ValueError ──
check(_leve_v(M.interet_simple, True, 0.05, 2), "C booléen -> ValueError")
check(_leve_v(M.interet_simple, 1000, True, 2), "taux booléen -> ValueError")
check(_leve_v(M.interet_simple, 1000, 0.05, True), "n booléen -> ValueError")
check(_leve_v(M.interet_compose, "1000", 0.05, 2), "C str -> ValueError")
check(_leve_v(M.interet_compose, 1000, float("nan"), 2), "taux NaN -> ValueError")
check(_leve_v(M.interet_compose, 1000, 0.05, float("inf")), "n inf -> ValueError")
check(_leve_v(M.valeur_actuelle, float("nan"), 0.05, 2), "VF NaN -> ValueError")
check(_leve_v(M.annuite_constante, float("inf"), 0.01, 12), "C inf -> ValueError")

# ── 10) SOUNDNESS — flux VAN invalide -> ValueError ──
check(_leve_v(M.van, 0.1, []), "VAN : flux vide -> ValueError")
check(_leve_v(M.van, 0.1, 5), "VAN : flux non-liste -> ValueError")
check(_leve_v(M.van, 0.1, [-100, "x", 60]), "VAN : élément non numérique -> ValueError")
check(_leve_v(M.van, 0.1, [-100, True, 60]), "VAN : élément booléen -> ValueError")
check(_leve_v(M.van, 0.1, [float("nan"), 50]), "VAN : élément NaN -> ValueError")
check(_leve_v(M.van, True, [-100, 50, 60]), "VAN : taux booléen -> ValueError")
check(_leve_v(M.npv, 0.1, []), "npv : flux vide -> ValueError")

# ── 11) DÉTERMINISME — fonctions pures, mêmes entrées -> mêmes sorties ──
check(M.interet_compose(1000, 0.05, 2) == M.interet_compose(1000, 0.05, 2), "composé déterministe")
check([M.annuite_constante(10000, 0.01, 12) for _ in range(5)].count(M.annuite_constante(10000, 0.01, 12)) == 5,
      "annuité : 5 appels identiques")
check(M.van(0.1, [-1000, 500, 600]) == M.van(0.1, [-1000, 500, 600]), "VAN déterministe")
check(M.valeur_actuelle(1102.5, 0.05, 2) == M.valeur_actuelle(1102.5, 0.05, 2), "actualisation déterministe")

print(f"\n=== valide_maths_financieres : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
