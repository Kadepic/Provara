"""
VALIDE essais_cliniques.py — held-out ADVERSE.

Ancres = mesures d'effet CALCULÉES À LA MAIN (non re-dérivées par le module) :
  • RR = Ie/Ine posé numériquement (surrisque / protection / pas d'effet) ;
  • RRA = Rc−Rt exact, signe préservé (RRA<0 = augmentation = valeur légitime) ;
  • NNT = ⌈1/RRA⌉ avec le cas-pivot RRA=0.20−0.15=0.05 -> 20 ;
  • OR = ad/bc posé numériquement (table 2×2) ;
  • PROPRIÉTÉS non circulaires : NNT round-trip (NNT·RRA==1 si 1/RRA entier),
    OR invariant par transposition OR(a,b,c,d)==OR(d,c,b,a), OR réciproque OR·OR⁻¹==1.
+ SOUNDNESS (incidence ∉ [0,1], dénominateur nul, RRA≤0/RRA>1, effectif non entier/négatif,
  non numérique / booléen / non fini -> ValueError)
+ DÉTERMINISME.
"""
import math
import essais_cliniques as A

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


TOL = 1e-9
RTOL = 1e-5


def proche(got, exp, rel=RTOL):
    return abs(got - exp) <= abs(exp) * rel + 1e-9


# ── 1) ANCRES RISQUE RELATIF — RR = Ie/Ine, posées à la main ──
# 0.15/0.10 = 1.5 (surrisque)
check(abs(A.risque_relatif(0.15, 0.10) - 1.5) < TOL, "RR(0.15,0.10) = 1.5")
# 0.20/0.40 = 0.5 (protection)
check(abs(A.risque_relatif(0.20, 0.40) - 0.5) < TOL, "RR(0.20,0.40) = 0.5")
# 0.10/0.10 = 1.0 (pas d'effet)
check(abs(A.risque_relatif(0.10, 0.10) - 1.0) < TOL, "RR(0.10,0.10) = 1.0")
# Ie = 0 -> RR = 0 (formule exacte, PAS une abstention)
check(A.risque_relatif(0.0, 0.25) == 0.0, "RR(0,0.25) = 0")
# 0.30/0.12 = 2.5
check(abs(A.risque_relatif(0.30, 0.12) - 2.5) < TOL, "RR(0.30,0.12) = 2.5")
# Cohérence : RR == Ie/Ine (définition), non circulaire car le quotient est posé ici
check(proche(A.risque_relatif(0.18, 0.24), 0.18 / 0.24), "RR == Ie/Ine (0.18,0.24)")

# ── 2) ANCRES RÉDUCTION DU RISQUE ABSOLUE — RRA = Rc−Rt ──
# 0.20 − 0.15 = 0.05  (cas-pivot du sujet)
check(abs(A.reduction_risque_absolue(0.20, 0.15) - 0.05) < TOL, "RRA(0.20,0.15) = 0.05")
# 0.50 − 0.30 = 0.20
check(abs(A.reduction_risque_absolue(0.50, 0.30) - 0.20) < TOL, "RRA(0.50,0.30) = 0.20")
# 0.10 − 0.15 = −0.05 (augmentation, signe préservé)
check(abs(A.reduction_risque_absolue(0.10, 0.15) - (-0.05)) < TOL, "RRA(0.10,0.15) = -0.05 (signe)")
# Rc = Rt -> RRA = 0 (valeur exacte)
check(A.reduction_risque_absolue(0.30, 0.30) == 0.0, "RRA(0.30,0.30) = 0")

# ── 3) ANCRES NNT — NNT = ⌈1/RRA⌉ ──
# 1/0.05 = 20 -> NNT = 20  (cas-pivot)
check(A.nombre_sujets_a_traiter(0.05) == 20, "NNT(0.05) = 20")
# 1/0.20 = 5 -> 5
check(A.nombre_sujets_a_traiter(0.20) == 5, "NNT(0.20) = 5")
# 1/0.25 = 4 -> 4
check(A.nombre_sujets_a_traiter(0.25) == 4, "NNT(0.25) = 4")
# 1/0.04 = 25 -> 25
check(A.nombre_sujets_a_traiter(0.04) == 25, "NNT(0.04) = 25")
# 1/0.03 = 33.33 -> ⌈⌉ = 34 (arrondi SUPÉRIEUR, pas 33)
check(A.nombre_sujets_a_traiter(0.03) == 34, "NNT(0.03) = 34 (arrondi sup)")
# 1/0.10 = 10 -> 10
check(A.nombre_sujets_a_traiter(0.10) == 10, "NNT(0.10) = 10")
# RRA = 1 -> NNT = 1 (borne)
check(A.nombre_sujets_a_traiter(1.0) == 1, "NNT(1.0) = 1")
# 1/0.07 = 14.28 -> 15
check(A.nombre_sujets_a_traiter(0.07) == 15, "NNT(0.07) = 15")
# NNT est bien un entier
check(isinstance(A.nombre_sujets_a_traiter(0.05), int), "NNT renvoie un int")
# PROPRIÉTÉ round-trip (non circulaire) : si 1/RRA entier, NNT·RRA == 1
for rra in (0.05, 0.20, 0.25, 0.10, 1.0):
    n = A.nombre_sujets_a_traiter(rra)
    check(proche(n * rra, 1.0), f"round-trip NNT·RRA==1 (RRA={rra})")
# PROPRIÉTÉ : NNT majore strictement 1/RRA quand non entier (arrondi SUP)
check(A.nombre_sujets_a_traiter(0.03) >= 1.0 / 0.03, "NNT(0.03) >= 1/RRA (majorant)")

# ── 4) ANCRES ODDS RATIO — OR = (a·d)/(b·c), table 2×2 ──
# (20·90)/(80·10) = 1800/800 = 2.25
check(abs(A.odds_ratio(20, 80, 10, 90) - 2.25) < TOL, "OR(20,80,10,90) = 2.25")
# (10·10)/(10·10) = 1.0
check(abs(A.odds_ratio(10, 10, 10, 10) - 1.0) < TOL, "OR(10,10,10,10) = 1.0")
# (9·9)/(1·1) = 81
check(abs(A.odds_ratio(9, 1, 1, 9) - 81.0) < TOL, "OR(9,1,1,9) = 81")
# (30·85)/(70·15) = 2550/1050 = 2.428571… -> 6 sig = 2.42857
check(proche(A.odds_ratio(30, 70, 15, 85), 2550.0 / 1050.0), "OR(30,70,15,85) ≈ 2.42857")
# a = 0 -> OR = 0 (valeur exacte, PAS une abstention ; numérateur nul)
check(A.odds_ratio(0, 80, 10, 90) == 0.0, "OR(0,80,10,90) = 0")
# PROPRIÉTÉ : OR invariant par transposition OR(a,b,c,d) == OR(d,c,b,a)
check(abs(A.odds_ratio(20, 80, 10, 90) - A.odds_ratio(90, 10, 80, 20)) < TOL,
      "OR invariant transposition : OR(a,b,c,d)==OR(d,c,b,a)")
# PROPRIÉTÉ : OR réciproque OR(a,b,c,d)·OR(b,a,d,c) == 1
check(proche(A.odds_ratio(20, 80, 10, 90) * A.odds_ratio(80, 20, 90, 10), 1.0),
      "OR · OR⁻¹ == 1 (réciproque)")
# Accepte les flottants entiers (20.0 == 20)
check(A.odds_ratio(20.0, 80.0, 10.0, 90.0) == A.odds_ratio(20, 80, 10, 90),
      "OR accepte flottants entiers (20.0)")

# ── 5) SOUNDNESS — entrée invalide -> ValueError (abstention, JAMAIS un faux) ──
# Risque relatif : dénominateur nul, incidences hors [0,1]
check(_leve_v(A.risque_relatif, 0.15, 0.0), "RR Ine=0 -> ValueError")
check(_leve_v(A.risque_relatif, 1.5, 0.10), "RR Ie>1 -> ValueError")
check(_leve_v(A.risque_relatif, -0.1, 0.10), "RR Ie<0 -> ValueError")
check(_leve_v(A.risque_relatif, 0.15, 1.5), "RR Ine>1 -> ValueError")
check(_leve_v(A.risque_relatif, 0.15, -0.1), "RR Ine<0 -> ValueError")
# RRA : risques hors [0,1]
check(_leve_v(A.reduction_risque_absolue, 1.5, 0.15), "RRA Rc>1 -> ValueError")
check(_leve_v(A.reduction_risque_absolue, 0.20, -0.1), "RRA Rt<0 -> ValueError")
check(_leve_v(A.reduction_risque_absolue, -0.2, 0.15), "RRA Rc<0 -> ValueError")
check(_leve_v(A.reduction_risque_absolue, 0.20, 1.2), "RRA Rt>1 -> ValueError")
# NNT : RRA <= 0 (pas de bénéfice) et RRA > 1 (impossible)
check(_leve_v(A.nombre_sujets_a_traiter, 0.0), "NNT RRA=0 -> ValueError")
check(_leve_v(A.nombre_sujets_a_traiter, -0.05), "NNT RRA<0 -> ValueError")
check(_leve_v(A.nombre_sujets_a_traiter, 1.5), "NNT RRA>1 -> ValueError")
# Odds ratio : dénominateur nul (b=0 ou c=0), effectifs invalides
check(_leve_v(A.odds_ratio, 20, 0, 10, 90), "OR b=0 -> ValueError")
check(_leve_v(A.odds_ratio, 20, 80, 0, 90), "OR c=0 -> ValueError")
check(_leve_v(A.odds_ratio, -1, 80, 10, 90), "OR a<0 -> ValueError")
check(_leve_v(A.odds_ratio, 20, -5, 10, 90), "OR b<0 -> ValueError")
check(_leve_v(A.odds_ratio, 20.5, 80, 10, 90), "OR a non entier -> ValueError")
check(_leve_v(A.odds_ratio, 20, 80, 10, 90.7), "OR d non entier -> ValueError")

# Non numérique / booléen / non fini -> ValueError (jamais une coercition silencieuse)
check(_leve_v(A.risque_relatif, True, 0.10), "RR booléen -> ValueError")
check(_leve_v(A.risque_relatif, "0.15", 0.10), "RR str -> ValueError")
check(_leve_v(A.risque_relatif, None, 0.10), "RR None -> ValueError")
check(_leve_v(A.risque_relatif, float("nan"), 0.10), "RR NaN -> ValueError")
check(_leve_v(A.risque_relatif, float("inf"), 0.10), "RR inf -> ValueError")
check(_leve_v(A.reduction_risque_absolue, float("nan"), 0.15), "RRA NaN -> ValueError")
check(_leve_v(A.nombre_sujets_a_traiter, True), "NNT booléen -> ValueError")
check(_leve_v(A.nombre_sujets_a_traiter, "0.05"), "NNT str -> ValueError")
check(_leve_v(A.nombre_sujets_a_traiter, float("inf")), "NNT inf -> ValueError")
check(_leve_v(A.nombre_sujets_a_traiter, float("nan")), "NNT NaN -> ValueError")
check(_leve_v(A.odds_ratio, True, 80, 10, 90), "OR booléen -> ValueError")
check(_leve_v(A.odds_ratio, "20", 80, 10, 90), "OR str -> ValueError")
check(_leve_v(A.odds_ratio, 20, 80, 10, float("inf")), "OR inf -> ValueError")
check(_leve_v(A.odds_ratio, 20, 80, 10, float("nan")), "OR NaN -> ValueError")

# ── 6) DÉTERMINISME — fonctions pures, mêmes entrées -> mêmes sorties ──
check(A.risque_relatif(0.15, 0.10) == A.risque_relatif(0.15, 0.10), "RR déterministe")
check(A.reduction_risque_absolue(0.20, 0.15) == A.reduction_risque_absolue(0.20, 0.15), "RRA déterministe")
check([A.nombre_sujets_a_traiter(0.05) for _ in range(5)] == [20] * 5, "NNT 5 appels identiques")
check(A.odds_ratio(20, 80, 10, 90) == A.odds_ratio(20, 80, 10, 90), "OR déterministe")

# ── 7) PREUVE auto-portée intégrée ──
check(A._p_essais_cliniques() is True, "_p_essais_cliniques() == True")

print(f"\n=== valide_essais_cliniques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
