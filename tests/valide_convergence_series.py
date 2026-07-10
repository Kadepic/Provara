"""
VALIDE convergence_series.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (résultats CLASSIQUES d'analyse, connus indépendamment des fonctions testées) :
  • Σ 1/n²  CONVERGE  (Riemann α=2 > 1)                         — via converge_riemann (délégué, prouvé).
  • Σ 1/n   DIVERGE   (série harmonique, α=1)                   — ANCRE PIÈGE : le terme général 1/n TEND VERS 0
        et pourtant la série DIVERGE ; un module qui conclurait 'converge' depuis uₙ→0 serait FAUX.
  • Σ 1/n!  CONVERGE  (d'Alembert : rapport u(n+1)/u(n)=1/(n+1) → 0 < 1 ; Cauchy → 0).
  • Σ 2ⁿ    DIVERGE   (d'Alembert : rapport = 2 > 1 ; Cauchy : racine = 2 > 1 ; géométrique |r|=2 ≥ 1).
  • Σ (-1)ⁿ/n CONVERGE (Leibniz) alors qu'elle NE converge PAS absolument (Σ1/n diverge) — conv. conditionnelle.
  • Σ n/(n+1) DIVERGE (terme général → 1 ≠ 0) → verdict 'diverge' CERTAIN par la condition nécessaire.
  • Σ 1/n avec d'Alembert : rapport = n/(n+1) → 1 → verdict 'indetermine' (et NON 'converge').
        ANCRE D'HONNÊTETÉ CAPITALE : le cas limite L=1 ne doit JAMAIS être tranché.
  • Σ (1/3)ⁿ CONVERGE (géométrique |r|=1/3 < 1 ; d'Alembert rapport = 1/3).
  • Comparaison : 0 ≤ 1/(n²+1) ≤ 1/n² (élémentaire) et Σ1/n² converge ⇒ Σ1/(n²+1) converge.

SOUNDNESS : u non appelable, u(n) non fini/non réel (NaN/inf/str/bool), iterations<10, n0 non entier≥1,
terme nul (rapport), v_converge non booléen, flottant/bool passés aux délégations -> ValueError.
"""
import math

import convergence_series as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


# Termes généraux (fonctions de n) — définis EN DUR ici, indépendants du module.
u_harmonique = lambda n: 1.0 / n                 # Σ1/n diverge, mais 1/n → 0 (piège)
u_factorielle = lambda n: 1.0 / math.factorial(n)  # Σ1/n! converge
u_deux_n = lambda n: 2.0 ** n                     # Σ2ⁿ diverge
u_tiers_n = lambda n: (1.0 / 3.0) ** n            # Σ(1/3)ⁿ converge (géométrique)
u_demi_n = lambda n: (1.0 / 2.0) ** n             # Σ(1/2)ⁿ converge
u_alt_harm = lambda n: ((-1.0) ** n) / n          # Σ(-1)ⁿ/n converge (Leibniz), pas absolument
u_n_sur_n1 = lambda n: n / (n + 1.0)              # terme → 1 ≠ 0 : Σ diverge (certain)

# ── 1) D'ALEMBERT — Σ1/n! CONVERGE (rapport → 0) ──
d_fact = C.critere_dalembert(u_factorielle, 1, 30)
check(d_fact["verdict"] == "converge", "d'Alembert Σ1/n! -> converge")
check(d_fact["limite_estimee"] < 0.1, "d'Alembert Σ1/n! : limite estimée ≈ 0 (<0.1)")

# ── 2) D'ALEMBERT — Σ2ⁿ DIVERGE (rapport = 2) ──
d_deux = C.critere_dalembert(u_deux_n, 1, 30)
check(d_deux["verdict"] == "diverge", "d'Alembert Σ2ⁿ -> diverge")
check(proche(d_deux["limite_estimee"], 2.0), "d'Alembert Σ2ⁿ : limite estimée = 2 (rapport exact)")

# ── 3) D'ALEMBERT — Σ(1/3)ⁿ CONVERGE (rapport = 1/3) ──
d_tiers = C.critere_dalembert(u_tiers_n, 1, 30)
check(d_tiers["verdict"] == "converge", "d'Alembert Σ(1/3)ⁿ -> converge")
check(proche(d_tiers["limite_estimee"], 1.0 / 3.0, tol=1e-6), "d'Alembert Σ(1/3)ⁿ : limite = 1/3")

# ── 4) D'ALEMBERT — Σ1/n : rapport → 1 -> INDÉTERMINÉ (HONNÊTETÉ CAPITALE) ──
d_harm = C.critere_dalembert(u_harmonique, 1, 50)
check(d_harm["verdict"] == "indetermine", "d'Alembert Σ1/n -> INDÉTERMINÉ (pas 'converge' !)")
check(d_harm["verdict"] != "converge", "d'Alembert Σ1/n : surtout PAS 'converge'")
check(d_harm["limite_estimee"] < 1.0, "d'Alembert Σ1/n : estimée < 1 mais non tranchée (tendance vers 1)")

# ── 5) CAUCHY — Σ(1/2)ⁿ CONVERGE (racine = 1/2) ──
c_demi = C.critere_cauchy(u_demi_n, 1, 30)
check(c_demi["verdict"] == "converge", "Cauchy Σ(1/2)ⁿ -> converge")
check(proche(c_demi["limite_estimee"], 0.5), "Cauchy Σ(1/2)ⁿ : racine = 1/2")

# ── 6) CAUCHY — Σ2ⁿ DIVERGE (racine = 2) ──
c_deux = C.critere_cauchy(u_deux_n, 1, 30)
check(c_deux["verdict"] == "diverge", "Cauchy Σ2ⁿ -> diverge")
check(proche(c_deux["limite_estimee"], 2.0), "Cauchy Σ2ⁿ : racine = 2")

# ── 7) CAUCHY — Σ1/n! CONVERGE (racine → 0) ──
c_fact = C.critere_cauchy(u_factorielle, 1, 30)
check(c_fact["verdict"] == "converge", "Cauchy Σ1/n! -> converge")

# ── 8) CAUCHY — Σ1/n : racine → 1 -> INDÉTERMINÉ (honnêteté) ──
c_harm = C.critere_cauchy(u_harmonique, 2, 60)
check(c_harm["verdict"] == "indetermine", "Cauchy Σ1/n -> INDÉTERMINÉ (racine n^(-1/n)→1)")
check(c_harm["verdict"] != "converge", "Cauchy Σ1/n : PAS 'converge'")

# ── 9) CONDITION NÉCESSAIRE — Σ n/(n+1) DIVERGE CERTAIN (terme → 1 ≠ 0) ──
t_nn1 = C.terme_general_tend_vers_zero(u_n_sur_n1, 1, 30)
check(t_nn1["verdict"] == "diverge", "Σ n/(n+1) : terme → 1 ≠ 0 -> DIVERGE certain")
check(t_nn1["tend_vers_zero"] is False, "Σ n/(n+1) : tend_vers_zero = False")
check(t_nn1["limite_estimee"] > 0.9, "Σ n/(n+1) : limite estimée ≈ 1")

# ── 10) CONDITION NÉCESSAIRE — Σ1/n : terme → 0 MAIS on n'ose PAS 'converge' (PIÈGE) ──
t_harm = C.terme_general_tend_vers_zero(u_harmonique, 1, 50)
check(t_harm["tend_vers_zero"] is True, "Σ1/n : terme général tend vers 0 (condition nécessaire OK)")
check(t_harm["verdict"] == "indetermine", "Σ1/n : uₙ→0 -> 'indetermine', JAMAIS 'converge' (piège harmonique)")
check(t_harm["verdict"] != "converge", "Σ1/n : condition nécessaire n'implique PAS convergence")
# ancre croisée : la vérité est que Σ1/n DIVERGE (Riemann α=1)
check(C.converge_riemann(1) == "diverge", "ancre croisée : Σ1/n DIVERGE (Riemann α=1) — le piège confirmé")

# ── 10bis) CONDITION NÉCESSAIRE — FENÊTRE CROISSANTE d'une série CONVERGENTE : NE JAMAIS conclure 'diverge' ──
# ANCRE (arithmético-géométrique) : Σ n·rⁿ avec r=1/1.01<1 CONVERGE (raison géométrique |r|<1), donc son terme
# général u(n)=n/1.01ⁿ TEND VERS 0. Mais le terme CROÎT jusqu'à son pic (n≈100) avant de décroître :
# u(50)=30.4, u(100)=37.0, u(1000)=0.048, u(5000)=1.2e-18 (valeurs calculées à la main / vérifiées en direct).
# Sur l'horizon PAR DÉFAUT [1,100] la queue est croissante -> le module DOIT s'abstenir, JAMAIS dire 'diverge'.
u_arith_geo = lambda n: n / 1.01 ** n            # Σ n·(1/1.01)ⁿ CONVERGE ; terme -> 0 après un pic
t_ag = C.terme_general_tend_vers_zero(u_arith_geo, 1, 100)
check(t_ag["verdict"] != "diverge", "n/1.01ⁿ (série CONVERGENTE) : fenêtre croissante -> PAS 'diverge' (anti FP)")
check(t_ag["verdict"] == "indetermine", "n/1.01ⁿ : verdict 'indetermine' (on ne peut conclure sur fenêtre finie)")
check(t_ag["tend_vers_zero"] is not False, "n/1.01ⁿ : ne PRÉTEND pas que le terme ne tend pas vers 0")
# ancre croisée : d'Alembert sur la MÊME série s'abstient honnêtement (rapport ≈ 1·(1/1.01) dans la bande)
check(C.critere_dalembert(u_arith_geo, 1, 100)["verdict"] != "diverge",
      "n/1.01ⁿ : d'Alembert non plus ne dit pas 'diverge' (cohérence inter-critères)")
# 2e contre-exemple : u(n)=n²/1.001ⁿ, Σ n²·(1/1.001)ⁿ CONVERGE, terme -> 0 ; pic vers n≈2000, donc croissant sur
# [1,200] -> abstention obligatoire (même à iterations=200, comme relevé par l'auditeur).
u_n2_geo = lambda n: n * n / 1.001 ** n
t_n2 = C.terme_general_tend_vers_zero(u_n2_geo, 1, 200)
check(t_n2["verdict"] != "diverge", "n²/1.001ⁿ (série CONVERGENTE) : fenêtre croissante -> PAS 'diverge'")
check(t_n2["verdict"] == "indetermine", "n²/1.001ⁿ : verdict 'indetermine'")

# 10ter) ANCRE POSITIVE conservée : un terme STABILISÉ à une valeur non nulle -> 'diverge' reste rendu.
# Σ (2 - 1/n) : terme -> 2 ≠ 0 (calcul à la main : u(30)=2-1/30=1.9667), queue quasi constante ≈ 2 -> DIVERGE.
u_vers_deux = lambda n: 2.0 - 1.0 / n
t_v2 = C.terme_general_tend_vers_zero(u_vers_deux, 1, 30)
check(t_v2["verdict"] == "diverge", "Σ (2-1/n) : terme stabilisé -> 2 ≠ 0 -> DIVERGE (verdict positif conservé)")
check(t_v2["tend_vers_zero"] is False, "Σ (2-1/n) : tend_vers_zero = False (terme ne tend pas vers 0)")
check(proche(t_v2["limite_estimee"], 2.0 - 1.0 / 30, tol=1e-6), "Σ (2-1/n) : limite estimée = 2-1/30 (à la main)")

# ── 11) SÉRIES ALTERNÉES (LEIBNIZ) — Σ(-1)ⁿ/n CONVERGE, mais PAS absolument ──
a_alt = C.critere_series_alternees(u_alt_harm, 1, 50)
check(a_alt["verdict"] == "converge", "Leibniz Σ(-1)ⁿ/n -> converge")
check(a_alt["alternee"] is True, "Σ(-1)ⁿ/n : signes alternés")
check(a_alt["decroissante"] is True, "Σ(-1)ⁿ/n : |uₙ| décroissante")
check(a_alt["tend_vers_zero"] is True, "Σ(-1)ⁿ/n : |uₙ| → 0")
check(a_alt["verifie_jusqua"] == 50, "Σ(-1)ⁿ/n : vérifié jusqu'à N=50 (honnêteté horizon fini)")
# NON absolument convergente : Σ|(-1)ⁿ/n| = Σ1/n diverge
check(C.converge_riemann(1) == "diverge", "Σ(-1)ⁿ/n : NON absolument convergente (Σ1/n diverge)")

# Leibniz refuse quand |uₙ| ne décroît pas / ne tend pas vers 0 : Σ(-1)ⁿ·(n/(n+1)) -> indetermine
u_alt_non_nul = lambda n: ((-1.0) ** n) * n / (n + 1.0)
a_bad = C.critere_series_alternees(u_alt_non_nul, 1, 30)
check(a_bad["verdict"] == "indetermine", "Leibniz Σ(-1)ⁿ·n/(n+1) : |uₙ|↛0 -> indetermine (pas converge)")

# ── 12) COMPARAISON — 0≤1/(n²+1)≤1/n² et Σ1/n² converge ⇒ Σ1/(n²+1) converge ──
v_conv = (C.converge_riemann(2) == "converge")   # SOURCÉ non circulairement : Riemann α=2 converge
check(v_conv is True, "ancre : Σ1/n² converge (Riemann α=2)")
u_maj = lambda n: 1.0 / (n * n + 1.0)
v_rie = lambda n: 1.0 / (n * n)
cmp_ok = C.critere_comparaison(u_maj, v_rie, v_conv, 1, 40)
check(cmp_ok["verdict"] == "converge", "comparaison : 1/(n²+1) ≤ 1/n², Σ1/n² conv -> Σ1/(n²+1) converge")
check(cmp_ok["domination_verifiee_jusqua"] == 40, "comparaison : domination vérifiée jusqu'à N=40")

# domination VIOLÉE (1/n > 1/n²) -> indetermine (on ne conclut rien)
cmp_viol = C.critere_comparaison(u_harmonique, v_rie, True, 2, 30)
check(cmp_viol["verdict"] == "indetermine", "comparaison : 1/n ≰ 1/n² -> indetermine (domination violée)")

# majorant DIVERGENT (Σv diverge) -> indetermine même si 0≤u≤v
cmp_divmaj = C.critere_comparaison(v_rie, u_harmonique, False, 2, 30)
check(cmp_divmaj["verdict"] == "indetermine", "comparaison : majorant divergent -> indetermine (rien prouvé)")

# ── 13) DÉLÉGATIONS À series_calcul — verdicts PROUVÉS ──
check(C.converge_riemann(2) == "converge", "délégué : Riemann α=2 -> converge")
check(C.converge_riemann(1) == "diverge", "délégué : Riemann α=1 (harmonique) -> diverge")
check(C.converge_geometrique(2) == "diverge", "délégué : géométrique r=2 -> diverge")
from fractions import Fraction
check(C.converge_geometrique(Fraction(1, 2)) == "converge", "délégué : géométrique r=1/2 -> converge")
check(C.converge_geometrique(Fraction(1, 3)) == "converge", "délégué : géométrique r=1/3 -> converge")

# ── 14) SOUNDNESS — u non appelable ──
check(leve(C.critere_dalembert, 5), "d'Alembert u=5 non appelable -> ValueError")
check(leve(C.critere_cauchy, "u"), "Cauchy u=str non appelable -> ValueError")
check(leve(C.critere_dalembert, True), "d'Alembert u=bool non appelable -> ValueError")
check(leve(C.terme_general_tend_vers_zero, None), "terme_general u=None -> ValueError")

# ── 15) SOUNDNESS — u(n) non fini / non réel ──
check(leve(C.critere_dalembert, lambda n: float("inf"), 1, 20), "u(n)=inf -> ValueError")
check(leve(C.critere_dalembert, lambda n: float("nan"), 1, 20), "u(n)=nan -> ValueError")
check(leve(C.critere_cauchy, lambda n: "x", 1, 20), "u(n)=str -> ValueError")
check(leve(C.critere_cauchy, lambda n: True, 1, 20), "u(n)=bool -> ValueError")
check(leve(C.critere_dalembert, lambda n: 1 / 0, 1, 20), "u(n) lève (division) -> ValueError")

# ── 16) SOUNDNESS — terme nul (rapport de d'Alembert indéfini) ──
check(leve(C.critere_dalembert, lambda n: 0.0, 1, 20), "d'Alembert terme nul -> ValueError")

# ── 17) SOUNDNESS — iterations < 10 ──
check(leve(C.critere_dalembert, u_harmonique, 1, 5), "iterations=5 (<10) -> ValueError")
check(leve(C.critere_cauchy, u_harmonique, 1, 9), "iterations=9 (<10) -> ValueError")
check(leve(C.critere_series_alternees, u_alt_harm, 1, 0), "iterations=0 -> ValueError")
check(leve(C.critere_comparaison, u_maj, v_rie, True, 1, 3), "comparaison iterations=3 -> ValueError")

# ── 18) SOUNDNESS — n0 non entier ≥ 1 ──
check(leve(C.critere_dalembert, u_harmonique, 0, 20), "n0=0 -> ValueError")
check(leve(C.critere_dalembert, u_harmonique, -1, 20), "n0=-1 -> ValueError")
check(leve(C.critere_dalembert, u_harmonique, 1.5, 20), "n0=1.5 (non entier) -> ValueError")
check(leve(C.critere_dalembert, u_harmonique, True, 20), "n0=True (bool) -> ValueError")

# ── 19) SOUNDNESS — v_converge non booléen (fait logique requis) ──
check(leve(C.critere_comparaison, u_maj, v_rie, 1, 1, 20), "v_converge=1 (non bool) -> ValueError")
check(leve(C.critere_comparaison, u_maj, v_rie, "oui", 1, 20), "v_converge=str -> ValueError")
check(leve(C.critere_comparaison, u_maj, 5, True, 1, 20), "comparaison v non appelable -> ValueError")

# ── 20) SOUNDNESS — délégations rejettent flottant / bool ──
check(leve(C.converge_riemann, 2.0), "Riemann α=2.0 (flottant) -> ValueError (exactitude ℚ)")
check(leve(C.converge_riemann, True), "Riemann α=True (bool) -> ValueError")
check(leve(C.converge_geometrique, 0.5), "géométrique r=0.5 (flottant) -> ValueError")
check(leve(C.converge_geometrique, True), "géométrique r=True (bool) -> ValueError")

# ── 21) DÉTERMINISME ──
check(C.critere_dalembert(u_factorielle, 1, 30) == C.critere_dalembert(u_factorielle, 1, 30),
      "déterminisme d'Alembert")
check(C.critere_cauchy(u_demi_n, 1, 30) == C.critere_cauchy(u_demi_n, 1, 30), "déterminisme Cauchy")
check(C.critere_series_alternees(u_alt_harm, 1, 50) == C.critere_series_alternees(u_alt_harm, 1, 50),
      "déterminisme Leibniz")
check(C.converge_riemann(2) == C.converge_riemann(2), "déterminisme délégation Riemann")
check(C.terme_general_tend_vers_zero(u_arith_geo, 1, 100) == C.terme_general_tend_vers_zero(u_arith_geo, 1, 100),
      "déterminisme condition nécessaire (fenêtre croissante)")

print(f"\n=== valide_convergence_series : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
