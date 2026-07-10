"""
VALIDE dynamique_populations.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES :
  • Exponentielle : N0=100, r=ln(2), t=1 -> 200 EXACTEMENT (une population double en un temps ln2/r).
    Le temps de doublement de r = 0,05 est ln(2)/0,05 = 13,8629436… ans (calculé à la main dans la gate).
  • Logistique : N(0) = N0 pour tout jeu de paramètres ; N(t) -> K quand t -> ∞ ; la croissance est
    maximale en K/2 (fait exact : la dérivée seconde s'y annule).
  • Logistique DISCRÈTE : les seuils de bifurcation sont des FAITS établis (May 1976) — équilibre stable
    pour 1 <= r < 3, cycle de période 2 à partir de r = 3, chaos à partir de r = 3,5699456…
    Point fixe K(1 − 1/r) : pour r=2, K=1000 -> 500 (calculé à la main).
  • Lotka-Volterra : l'équilibre (x*, y*) = (gamma/delta, alpha/beta). ANCRE CONTRE-INTUITIVE : x* ne
    dépend QUE des paramètres du prédateur. Un module qui ferait dépendre x* de alpha serait FAUX.

ANCRE D'HONNÊTETÉ : au-delà du seuil de chaos, `point_fixe_logistique_discrete` doit ABSTENIR. Le point fixe
existe mathématiquement mais la suite ne l'atteint jamais : le rendre serait le faux le plus tentant du module.

SOUNDNESS : N0<=0, K<=0, t<0, r<0 pour le régime, r<=0 pour le doublement, generations non entier,
N0>K en discret, bool/str/NaN/inf -> ValueError. Déterminisme et boucle fermée vérifiés.
"""
import math
import sys

import dynamique_populations as D

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
        fn(*a, **k)
        return False
    except ValueError:
        return True


def proche(x, att, tol=1e-6):
    return x is not None and abs(x - att) <= tol * max(1.0, abs(att))


# ── 1) EXPONENTIELLE : ancres calculées à la main ──
check(proche(D.croissance_exponentielle(100.0, math.log(2.0), 1.0), 200.0),
      "N0=100, r=ln2, t=1 -> 200 (doublement exact)")
check(proche(D.croissance_exponentielle(100.0, math.log(2.0), 2.0), 400.0), "t=2 -> quadruplement")
check(proche(D.croissance_exponentielle(100.0, 0.0, 5.0), 100.0), "r=0 -> population constante")
check(D.croissance_exponentielle(100.0, -0.5, 3.0) < 100.0, "r<0 -> décroissance")
check(proche(D.croissance_exponentielle(50.0, 0.1, 0.0), 50.0), "t=0 -> N0")

# ln(2)/0,05 = 13,86294361… (posé à la main)
check(proche(D.temps_de_doublement(0.05), 13.8629436112, tol=1e-8), "temps de doublement de r=0,05")
check(proche(D.temps_de_doublement(math.log(2.0)), 1.0), "r = ln2 -> doublement en 1")
# boucle fermée : deux chemins de code inverses
for r in (0.01, 0.05, 0.2, 1.0):
    check(proche(D.taux_depuis_doublement(D.temps_de_doublement(r)), r), f"boucle fermée r={r}")

# ── 2) LOGISTIQUE CONTINUE ──
check(proche(D.croissance_logistique(10.0, 0.5, 1000.0, 0.0), 10.0), "logistique en t=0 -> N0")
check(proche(D.croissance_logistique(1000.0, 0.5, 1000.0, 7.0), 1000.0), "N0 = K -> reste K (pas de div/0)")
check(proche(D.croissance_logistique(10.0, 0.5, 1000.0, 1000.0), 1000.0, tol=1e-6),
      "t -> grand : la population tend vers K")
check(D.croissance_logistique(2000.0, 0.5, 1000.0, 5.0) < 2000.0,
      "N0 > K (surpopulation) : la population DÉCROÎT vers K")
check(D.croissance_logistique(2000.0, 0.5, 1000.0, 1000.0) > 999.0,
      "surpopulation : convergence vers K par le haut")
check(proche(D.point_inflexion_logistique(1000.0), 500.0), "croissance maximale en K/2")
# monotonie sous K
suite = [D.croissance_logistique(10.0, 0.5, 1000.0, t) for t in range(0, 30, 3)]
check(all(a < b for a, b in zip(suite, suite[1:])), "sous K : la logistique est strictement croissante")
check(all(v <= 1000.0 for v in suite), "sous K : la population ne dépasse jamais K")
check(D.capacite_atteinte(995.0, 1000.0) is True, "995 est à 1 % de 1000 -> capacité atteinte")
check(D.capacite_atteinte(900.0, 1000.0) is False, "900 n'est pas à 1 % de 1000")

# ── 3) LOGISTIQUE DISCRÈTE : les régimes sont des FAITS (May 1976) ──
check(D.regime_logistique_discrete(0.5) == "extinction", "r < 1 -> extinction")
check(D.regime_logistique_discrete(2.0) == "équilibre stable", "1 <= r < 3 -> équilibre stable")
check(D.regime_logistique_discrete(3.2) == "cycle de période 2", "r = 3,2 -> cycle de période 2")
check(D.regime_logistique_discrete(3.5) == "doublements de période", "r = 3,5 -> doublements")
check(D.regime_logistique_discrete(3.9) == "chaos", "r = 3,9 -> chaos")
check(D.regime_logistique_discrete(4.0) == "chaos", "r = 4 -> chaos")
check(proche(D.SEUIL_CHAOS, 3.5699456718, tol=1e-9), "seuil de Feigenbaum ≈ 3,5699456718")

# point fixe K(1 − 1/r) : r=2, K=1000 -> 500 (à la main)
check(proche(D.point_fixe_logistique_discrete(2.0, 1000.0), 500.0), "point fixe r=2, K=1000 -> 500")
check(proche(D.point_fixe_logistique_discrete(1.5, 900.0), 300.0), "point fixe r=1,5, K=900 -> 300")

# ANCRE D'HONNÊTETÉ : au-delà de la stabilité, on ABSTIENT
check(leve(D.point_fixe_logistique_discrete, 3.2, 1000.0), "cycle de période 2 -> pas de point fixe rendu")
check(leve(D.point_fixe_logistique_discrete, 3.9, 1000.0), "CHAOS -> abstention (le faux le plus tentant)")
check(leve(D.point_fixe_logistique_discrete, 0.5, 1000.0), "extinction -> pas d'équilibre non nul")

# la trajectoire converge vraiment vers le point fixe en régime stable (vérification INDÉPENDANTE)
t = D.logistique_discrete(10.0, 2.0, 1000.0, 60)
check(t["regime"] == "équilibre stable", "trajectoire r=2 : régime nommé « équilibre stable »")
check(t["chaotique"] is False, "r=2 : non chaotique")
check(proche(t["trajectoire"][-1], 500.0, tol=1e-4), "la trajectoire converge vers 500 (chemin indépendant)")
check(len(t["trajectoire"]) == 61, "trajectoire : N0 + 60 générations")

ch = D.logistique_discrete(10.0, 3.9, 1000.0, 40)
check(ch["chaotique"] is True, "r=3,9 : la trajectoire est MARQUÉE chaotique")
check(ch["regime"] == "chaos", "r=3,9 : régime « chaos »")
# sensibilité aux conditions initiales : deux N0 voisins divergent (fait du chaos)
a = D.logistique_discrete(10.0, 3.9, 1000.0, 40)["trajectoire"][-1]
b = D.logistique_discrete(10.001, 3.9, 1000.0, 40)["trajectoire"][-1]
check(abs(a - b) > 1.0, "chaos : deux N0 voisins divergent (sensibilité aux conditions initiales)")
# en régime stable, au contraire, ils convergent
a2 = D.logistique_discrete(10.0, 2.0, 1000.0, 60)["trajectoire"][-1]
b2 = D.logistique_discrete(10.001, 2.0, 1000.0, 60)["trajectoire"][-1]
check(abs(a2 - b2) < 1e-3, "équilibre stable : deux N0 voisins convergent au même point")

# ── 4) LOTKA-VOLTERRA : l'ancre contre-intuitive ──
x, y = D.equilibre_lotka_volterra(1.0, 0.1, 0.5, 0.02)
check(proche(x, 25.0), "x* = gamma/delta = 0,5/0,02 = 25")
check(proche(y, 10.0), "y* = alpha/beta = 1,0/0,1 = 10")
x2, _ = D.equilibre_lotka_volterra(2.0, 0.1, 0.5, 0.02)      # alpha doublé
check(proche(x2, 25.0), "ANCRE : doubler alpha ne change PAS x* (il ne dépend que du prédateur)")
_, y2 = D.equilibre_lotka_volterra(1.0, 0.1, 1.0, 0.02)      # gamma doublé
check(proche(y2, 10.0), "ANCRE : doubler gamma ne change PAS y*")

# ── 5) SOUNDNESS ──
check(leve(D.croissance_exponentielle, 0.0, 0.1, 1.0), "N0 = 0 -> ValueError")
check(leve(D.croissance_exponentielle, -5.0, 0.1, 1.0), "N0 < 0 -> ValueError")
check(leve(D.croissance_exponentielle, 100.0, 0.1, -1.0), "t < 0 -> ValueError")
check(leve(D.croissance_exponentielle, True, 0.1, 1.0), "bool -> ValueError")
check(leve(D.croissance_exponentielle, float("nan"), 0.1, 1.0), "NaN -> ValueError")
check(leve(D.croissance_exponentielle, float("inf"), 0.1, 1.0), "inf -> ValueError")
check(leve(D.croissance_exponentielle, "100", 0.1, 1.0), "str -> ValueError")
check(leve(D.temps_de_doublement, 0.0), "temps de doublement de r=0 -> ValueError")
check(leve(D.temps_de_doublement, -0.1), "temps de doublement de r<0 -> ValueError")
check(leve(D.croissance_logistique, 10.0, 0.5, 0.0, 1.0), "K = 0 -> ValueError")
check(leve(D.croissance_logistique, 10.0, 0.5, -100.0, 1.0), "K < 0 -> ValueError")
check(leve(D.regime_logistique_discrete, -1.0), "r < 0 -> ValueError")
check(leve(D.logistique_discrete, 10.0, 2.0, 1000.0, 0), "0 génération -> ValueError")
check(leve(D.logistique_discrete, 10.0, 2.0, 1000.0, 1.5), "generations non entier -> ValueError")
check(leve(D.logistique_discrete, 10.0, 2.0, 1000.0, True), "generations bool -> ValueError")
check(leve(D.logistique_discrete, 10.0, 2.0, 1000.0, 100000), "trop d'itérations -> ValueError (budget dit)")
check(leve(D.logistique_discrete, 2000.0, 2.0, 1000.0, 5), "N0 > K en discret -> ValueError (hors domaine)")
check(leve(D.equilibre_lotka_volterra, 0.0, 0.1, 0.5, 0.02), "alpha = 0 -> ValueError")
check(leve(D.equilibre_lotka_volterra, 1.0, 0.0, 0.5, 0.02), "beta = 0 -> ValueError (division)")
check(leve(D.equilibre_lotka_volterra, 1.0, 0.1, 0.5, 0.0), "delta = 0 -> ValueError (division)")
check(leve(D.capacite_atteinte, 100.0, 1000.0, -0.1), "tolérance négative -> ValueError")

# ── 6) DÉTERMINISME ──
check(D.croissance_logistique(10.0, 0.5, 1000.0, 5.0) == D.croissance_logistique(10.0, 0.5, 1000.0, 5.0),
      "déterminisme de la logistique")
check(D.logistique_discrete(10.0, 3.9, 1000.0, 20) == D.logistique_discrete(10.0, 3.9, 1000.0, 20),
      "déterminisme de la trajectoire chaotique (chaos ≠ aléatoire)")
check(D.equilibre_lotka_volterra(1.0, 0.1, 0.5, 0.02) == D.equilibre_lotka_volterra(1.0, 0.1, 0.5, 0.02),
      "déterminisme de l'équilibre")

print(f"\n=== valide_dynamique_populations : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
