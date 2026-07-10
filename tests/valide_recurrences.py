"""Gate adverse de `recurrences` — ANCRES NON CIRCULAIRES (résultats universellement connus), soundness,
déterminisme. Chaque valeur attendue est connue INDÉPENDAMMENT de la formule testée (constante classique,
calcul à la main écrit ici, ou SECOND chemin de code : itération vs formule close)."""
from __future__ import annotations

from fractions import Fraction

from recurrences import (
    theoreme_maitre, theoreme_maitre_general, resout_recurrence_lineaire,
    terme_recurrence, complexite_diviser_regner, exposant_inferieur, compare_asymptotique,
)

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
    except (ValueError, TypeError):
        return True


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 1) THÉORÈME MAÎTRE — ancres NON CIRCULAIRES (résultats de cours universels, DÉRIVÉS ici, pas recopiés)
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Tri fusion a=2,b=2,k=1 : log_2(2)=1=k -> cas 2 -> Θ(n log n)
tf = theoreme_maitre(2, 2, 1)
check(tf["cas"] == 2, "tri fusion -> cas 2")
check(tf["log_b_a"] == Fraction(1), "log_2(2) = 1 (exact)")
check("n log n" in tf["complexite"], "tri fusion -> Θ(n log n)")
check(tf["classe"] == "n log n", "tri fusion classe = n log n")

# Recherche dichotomique a=1,b=2,k=0 : log_2(1)=0=k -> cas 2 -> Θ(log n)
rd = theoreme_maitre(1, 2, 0)
check(rd["cas"] == 2, "dichotomie -> cas 2")
check(rd["log_b_a"] == Fraction(0), "log_2(1) = 0 (exact)")
check(rd["complexite"] == "Θ(log n)", "dichotomie -> Θ(log n)")
check(rd["classe"] == "log n", "dichotomie classe = log n")

# Karatsuba a=3,b=2,k=1 : log_2(3)≈1.585 > 1 -> cas 1 (ANCRE FORTE : sous-quadratique)
ka = theoreme_maitre(3, 2, 1)
check(ka["cas"] == 1, "karatsuba -> cas 1")
# log_2(3) = 1.5849625007211562 (constante connue)
check(abs(ka["log_b_a"] - 1.5849625007) < 1e-6, "log_2(3) ≈ 1.585")
check(ka["classe"] is None, "karatsuba : exposant irrationnel, hors ORDRE_ASYMPTOTIQUE")

# Strassen a=7,b=2,k=2 : log_2(7)≈2.807 > 2 -> cas 1 (MOINS que le n³ naïf)
st = theoreme_maitre(7, 2, 2)
check(st["cas"] == 1, "strassen -> cas 1")
# log_2(7) = 2.807354922057604 (constante connue)
check(abs(st["log_b_a"] - 2.8073549220) < 1e-6, "log_2(7) ≈ 2.807")

# a=2,b=2,k=2 : log_2(2)=1 < 2 -> cas 3 -> Θ(n²)
c3 = theoreme_maitre(2, 2, 2)
check(c3["cas"] == 3, "a=2,b=2,k=2 -> cas 3")
check(c3["complexite"] == "Θ(n^2)", "cas 3 -> Θ(n^2)")
check(c3["classe"] == "n^2", "cas 3 classe = n^2")
check("régularité" in c3["justification"], "cas 3 énonce la condition de régularité")

# log rationnel exact : log_2(4)=2, log_2(8)=3 (connus) — cas 1
q4 = theoreme_maitre(4, 2, 1)   # log_2(4)=2 > 1 -> cas 1 -> Θ(n^2)
check(q4["cas"] == 1 and q4["log_b_a"] == Fraction(2), "log_2(4) = 2 (exact) -> cas 1")
check(q4["complexite"] == "Θ(n^2)", "a=4,b=2,k=1 -> Θ(n^2)")
q8 = theoreme_maitre(8, 2, 2)   # log_2(8)=3 > 2 -> cas 1 -> Θ(n^3)
check(q8["cas"] == 1 and q8["log_b_a"] == Fraction(3), "log_2(8) = 3 (exact) -> cas 1")
check(q8["complexite"] == "Θ(n^3)", "a=8,b=2,k=2 -> Θ(n^3)")

# k FRACTIONNAIRE : log_4(2) = 1/2 (connu). a=2,b=4,k=1/2 -> égal -> cas 2
half = theoreme_maitre(2, 4, Fraction(1, 2))
check(half["cas"] == 2, "log_4(2)=1/2=k -> cas 2")
check(half["log_b_a"] == Fraction(1, 2), "log_4(2) = 1/2 (exact)")

# Déterminisme
check(theoreme_maitre(7, 2, 2) == theoreme_maitre(7, 2, 2), "theoreme_maitre déterministe")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 2) THÉORÈME MAÎTRE GÉNÉRAL — n'accepte que f polynomiale, sinon ABSTENTION
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
g = theoreme_maitre_general(2, 2, "n")          # = theoreme_maitre(2,2,1) -> cas 2
check(g["cas"] == 2 and "n log n" in g["complexite"], "general f='n' -> cas 2 Θ(n log n)")
g2 = theoreme_maitre_general(2, 2, "n^2")       # cas 3
check(g2["cas"] == 3 and g2["complexite"] == "Θ(n^2)", "general f='n^2' -> cas 3 Θ(n^2)")
check(leve(theoreme_maitre_general, 2, 2, "n log n"), "general f='n log n' -> abstention (non polynomial)")
check(leve(theoreme_maitre_general, 2, 2, "2^n"), "general f='2^n' -> abstention")
check(leve(theoreme_maitre_general, 2, 2, "log n"), "general f='log n' -> abstention")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 3) DIVISER-POUR-RÉGNER — chaque récurrence RÉSOLUE par le théorème maître (pas de table)
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
cf = complexite_diviser_regner("tri_fusion")
check(cf["cas"] == 2 and cf["classe"] == "n log n", "tri_fusion résolu -> Θ(n log n)")
cd = complexite_diviser_regner("recherche_dichotomique")
check(cd["cas"] == 2 and cd["complexite"] == "Θ(log n)", "recherche_dichotomique -> Θ(log n)")
ck = complexite_diviser_regner("karatsuba")
check(ck["cas"] == 1 and abs(ck["log_b_a"] - 1.5849625007) < 1e-6, "karatsuba -> cas 1, ~n^1.585")
cs = complexite_diviser_regner("strassen")
check(cs["cas"] == 1 and abs(cs["log_b_a"] - 2.8073549220) < 1e-6, "strassen -> cas 1, ~n^2.807")
check(leve(complexite_diviser_regner, "tri_bulle"), "algo hors catalogue -> abstention")
check(complexite_diviser_regner("tri_fusion") == complexite_diviser_regner("tri_fusion"), "diviser_regner déterministe")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 4) OPTIMALITÉ ASYMPTOTIQUE — exposant_inferieur (décision entière EXACTE)
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
check(exposant_inferieur(3, 2, 2) is True, "Karatsuba sous-quadratique : log_2(3) < 2 (3 < 4)")
check(exposant_inferieur(3, 2, 1) is False, "log_2(3) NON < 1 (3 > 2)")
check(exposant_inferieur(7, 2, 3) is True, "Strassen sous-cubique : log_2(7) < 3 (7 < 8)")
check(exposant_inferieur(7, 2, 2) is False, "log_2(7) NON < 2 (7 > 4)")

# Comparaison asymptotique déléguée à algo_analyse (ordre de croissance établi)
check(compare_asymptotique("n log n", "n^2") == "n^2", "n^2 domine n log n")
check(compare_asymptotique("log n", "n") == "n", "n domine log n")
check(leve(compare_asymptotique, "n^2.807", "n^3"), "classe irrationnelle inconnue d'algo_analyse -> abstention")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 5) SUITES RÉCURRENTES LINÉAIRES — Fibonacci (nombre d'or) + formule close exacte
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Fibonacci coeffs [1,1], initiaux [0,1] : x²-x-1=0, Δ=5 (non carré) -> racines irrationnelles
fib = resout_recurrence_lineaire([1, 1], [0, 1])
check(fib["exact"] is False, "Fibonacci : racines irrationnelles (pas de formule rationnelle close)")
check(fib["discriminant"] == 5, "Fibonacci : discriminant = 5 (1 + 4·1)")
lo, hi = fib["racine_dominante_encadree"]
# nombre d'or φ = (1+√5)/2 = 1.6180339887498949 (constante connue, non circulaire)
phi = 1.6180339887498949
check(float(lo) < phi < float(hi), "encadrement contient le nombre d'or φ")
check(hi - lo <= Fraction(1, 10 ** 8), "encadrement de φ serré (≤ 1e-8)")

# Fibonacci — valeurs EN DUR (connues) vérifiées par itération INDÉPENDANTE du module
check(terme_recurrence([1, 1], [0, 1], 10) == 55, "F(10) = 55 (valeur connue)")
check(terme_recurrence([1, 1], [0, 1], 20) == 6765, "F(20) = 6765 (valeur connue)")
# Second contrôle : itération autonome écrite ICI (chemin totalement séparé)
a_, b_ = 0, 1
for _ in range(20):
    a_, b_ = b_, a_ + b_
check(a_ == 6765, "itération autonome de la gate : F(20) = 6765")
check(terme_recurrence([1, 1], [0, 1], 0) == 0 and terme_recurrence([1, 1], [0, 1], 1) == 1, "F(0)=0, F(1)=1")

# Récurrence à racines RATIONNELLES : F(n)=3F(n-1)-2F(n-2), F0=0,F1=1 -> x²-3x+2=(x-1)(x-2)
# racines 1 et 2 (connues) ; formule close F(n)=2^n - 1 (dérivée à la main)
rat = resout_recurrence_lineaire([3, -2], [0, 1])
check(rat["exact"] is True, "x²-3x+2 : racines rationnelles -> formule close exacte")
check(rat["discriminant"] == 1, "x²-3x+2 : discriminant = 9 - 8 = 1")
check(set(rat["racines"]) == {Fraction(1), Fraction(2)}, "racines = {1, 2} (connues)")
# La formule close doit coïncider avec l'itération ET avec 2^n - 1 (ancre indépendante)
for nn in (0, 1, 2, 3, 5, 8):
    attendu = 2 ** nn - 1                         # ancre non circulaire : 2^n - 1
    check(terme_recurrence([3, -2], [0, 1], nn) == attendu, f"F({nn}) = 2^{nn}-1 = {attendu}")

# Racine double : F(n)=4F(n-1)-4F(n-2), F0=0,F1=2 -> x²-4x+4=(x-2)² -> F(n)=n·2^n (dérivé à la main)
dbl = resout_recurrence_lineaire([4, -4], [0, 2])
check(dbl["exact"] is True and dbl.get("racine_double") is True, "x²-4x+4 : racine double 2")
check(dbl["racines"] == (Fraction(2), Fraction(2)), "racine double = 2")
for nn in (0, 1, 2, 3, 4):
    attendu = nn * 2 ** nn                        # ancre : n·2^n
    check(terme_recurrence([4, -4], [0, 2], nn) == attendu, f"F({nn}) = {nn}·2^{nn} = {attendu}")

# Déterminisme
check(resout_recurrence_lineaire([1, 1], [0, 1]) == resout_recurrence_lineaire([1, 1], [0, 1]), "resout déterministe")
check(terme_recurrence([1, 1], [0, 1], 30) == terme_recurrence([1, 1], [0, 1], 30), "terme déterministe")

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 6) SOUNDNESS — abstention structurelle (bool/str/flottant/NaN/inf/hors-domaine/arité)
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
nan = float("nan")
inf = float("inf")
# theoreme_maitre : hypothèses violées
check(leve(theoreme_maitre, 2, 1, 1), "b ≤ 1 -> abstention")
check(leve(theoreme_maitre, 0, 2, 1), "a < 1 -> abstention")
check(leve(theoreme_maitre, 2, 2, -1), "k < 0 -> abstention")
# bool refusé (True n'est pas 1)
check(leve(theoreme_maitre, True, 2, 1), "a booléen -> abstention")
check(leve(theoreme_maitre, 2, True, 1), "b booléen -> abstention")
check(leve(theoreme_maitre, 2, 2, True), "k booléen -> abstention")
# flottant / str / NaN / inf refusés
check(leve(theoreme_maitre, 2, 2, 1.0), "k flottant -> abstention")
check(leve(theoreme_maitre, 2.0, 2, 1), "a flottant -> abstention")
check(leve(theoreme_maitre, "2", 2, 1), "a str -> abstention")
check(leve(theoreme_maitre, 2, 2, nan), "k NaN -> abstention")
check(leve(theoreme_maitre, 2, 2, inf), "k inf -> abstention")
# mauvaise arité
check(leve(theoreme_maitre, 2, 2), "theoreme_maitre arité insuffisante -> abstention")
# theoreme_maitre_general
check(leve(theoreme_maitre_general, 2, 2, 5), "general f non-str -> abstention")
check(leve(theoreme_maitre_general, 2, 1, "n"), "general b ≤ 1 -> abstention")
# complexite_diviser_regner
check(leve(complexite_diviser_regner, 42), "diviser_regner non-str -> abstention")
# resout_recurrence_lineaire
check(leve(resout_recurrence_lineaire, [1.0, 1], [0, 1]), "coeff flottant -> abstention")
check(leve(resout_recurrence_lineaire, [1, True], [0, 1]), "coeff booléen -> abstention")
check(leve(resout_recurrence_lineaire, [1, 1], [0]), "initiaux longueur ≠ degré -> abstention")
check(leve(resout_recurrence_lineaire, [0, -1], [0, 1]), "x²+1 : discriminant < 0 (racines complexes) -> abstention")
check(leve(resout_recurrence_lineaire, [1, 1, 1], [0, 1, 1]), "degré 3 non supporté -> abstention")
check(leve(resout_recurrence_lineaire, "11", [0, 1]), "coeffs non liste -> abstention")
# terme_recurrence
check(leve(terme_recurrence, [1, 1], [0, 1], -1), "terme n < 0 -> abstention")
check(leve(terme_recurrence, [1, 1], [0, 1], 1.0), "terme n flottant -> abstention")
check(leve(terme_recurrence, [1, 1], [0, 1], True), "terme n booléen -> abstention")
# exposant_inferieur
check(leve(exposant_inferieur, 3, 1, 2), "exposant_inferieur b ≤ 1 -> abstention")
check(leve(exposant_inferieur, 3, 2, -1), "exposant_inferieur k_ref < 0 -> abstention")

print(f"\n=== valide_recurrences : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
