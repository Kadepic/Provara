"""
VALIDE developpement_limite.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée, écrites EN DUR) :
  • Coefficients de Maclaurin universellement connus :
        exp     -> [1, 1, 1/2, 1/6, 1/24]
        sin     -> [0, 1, 0, -1/6, 0, 1/120]
        cos     -> [1, 0, -1/2, 0, 1/24]
        ln(1+x) -> [0, 1, -1/2, 1/3, -1/4]
        1/(1-x) -> [1, 1, 1, 1, 1]
        arctan  -> [0, 1, 0, -1/3, 0, 1/5]
    Série binomiale : (1+x)^(1/2) = [1, 1/2, -1/8, 1/16] (racine) ; (1+x)^(-1) = [1,-1,1,-1,1] (= 1/(1+x)) ;
    (1+x)^3 = [1, 3, 3, 1, 0] (coefficients du binôme de Newton).
  • APPROXIMATION AVEC BORNE, confrontée à un CHEMIN INDÉPENDANT (math.exp / math.sin de la stdlib) :
        exp(0.1) ordre 4 ~ 1.10517083 ; sin(0.5) ordre 5 ; l'inégalité |vrai − approx| ≤ borne est exigée.
  • HORS RAYON : ln(1+x) et arctan ont un rayon de convergence 1 -> x=1.5, x=2 lèvent ValueError.
  • BOUCLE INDÉPENDANTE : les coefficients de sin sont ceux de cos DÉRIVÉS. cos' = −sin, donc
        taylor("sin") == −derivee(taylor("cos"))   via calcul_infinitesimal.derivee (deux entrées de
    catalogue distinctes qui coïncident par un TROISIÈME chemin de code).
  • Développement de POLYNÔME : (x³−3x+2) autour de a=1 = (x−1)³ + 3(x−1)² -> [0, 0, 3, 1] (calcul à la main).

SOUNDNESS : hors catalogue, ordre<0/non-entier, |x|≥rayon, alpha manquant/flottant, coeff/point flottant,
types (bool/str/NaN/inf), mauvaise arité -> ValueError. DÉTERMINISME exigé.
"""
import math
from fractions import Fraction

import calcul_infinitesimal as ci
import developpement_limite as DL

F = Fraction
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
    """True ssi fn(*a, **k) lève ValueError (abstention structurelle)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(float(x) - attendu) <= tol


# ── 1) COEFFICIENTS EXACTS — ancres écrites EN DUR ──
check(DL.taylor("exp", 4) == [F(1), F(1), F(1, 2), F(1, 6), F(1, 24)], "exp -> [1,1,1/2,1/6,1/24]")
check(DL.taylor("sin", 5) == [F(0), F(1), F(0), F(-1, 6), F(0), F(1, 120)], "sin -> [0,1,0,-1/6,0,1/120]")
check(DL.taylor("cos", 4) == [F(1), F(0), F(-1, 2), F(0), F(1, 24)], "cos -> [1,0,-1/2,0,1/24]")
check(DL.taylor("ln1p", 4) == [F(0), F(1), F(-1, 2), F(1, 3), F(-1, 4)], "ln(1+x) -> [0,1,-1/2,1/3,-1/4]")
check(DL.taylor("geometrique", 4) == [F(1), F(1), F(1), F(1), F(1)], "1/(1-x) -> [1,1,1,1,1]")
check(DL.taylor("arctan", 5) == [F(0), F(1), F(0), F(-1, 3), F(0), F(1, 5)], "arctan -> [0,1,0,-1/3,0,1/5]")
# sinh / cosh
check(DL.taylor("sinh", 5) == [F(0), F(1), F(0), F(1, 6), F(0), F(1, 120)], "sinh -> [0,1,0,1/6,0,1/120]")
check(DL.taylor("cosh", 4) == [F(1), F(0), F(1, 2), F(0), F(1, 24)], "cosh -> [1,0,1/2,0,1/24]")
# longueur = ordre+1
check(len(DL.taylor("exp", 7)) == 8, "longueur exp ordre 7 = 8")
check(DL.taylor("exp", 0) == [F(1)], "exp ordre 0 = [1]")

# ── 2) SÉRIE BINOMIALE (α rationnel) — ancres connues ──
check(DL.taylor("binome", 3, alpha=F(1, 2)) == [F(1), F(1, 2), F(-1, 8), F(1, 16)], "(1+x)^(1/2) = [1,1/2,-1/8,1/16]")
check(DL.taylor("binome", 4, alpha=-1) == [F(1), F(-1), F(1), F(-1), F(1)], "(1+x)^(-1) = [1,-1,1,-1,1]")
check(DL.taylor("binome", 4, alpha=3) == [F(1), F(3), F(3), F(1), F(0)], "(1+x)^3 = [1,3,3,1,0] (Newton)")
# α = -1 doit coïncider avec 1/(1+x) : évaluer les deux séries en un point rationnel
xb = F(1, 4)
serie_bin = sum(c * xb ** k for k, c in enumerate(DL.taylor("binome", 8, alpha=-1)))
check(serie_bin == sum(F((-1) ** k) * xb ** k for k in range(9)), "binome α=-1 == série alternée (chemin indépendant)")

# ── 3) BOUCLE : sin == −derivee(cos) via calcul_infinitesimal (troisième chemin) ──
cos_coeffs = DL.taylor("cos", 6)                     # [1,0,-1/2,0,1/24,0,-1/720]
d_cos = ci.derivee(cos_coeffs)                       # = coefficients de −sin
sin_via_cos = [-c for c in d_cos]                    # = coefficients de sin
sin_direct = DL.taylor("sin", 5)                     # entrée de catalogue INDÉPENDANTE
check(sin_via_cos == sin_direct, "sin == −derivee(cos) (cos et sin coïncident via calcul_infinitesimal)")
# symétrique : cos == derivee(sin) — ordre 7 pour éviter le zéro de tête retiré par ci.derivee
d_sin = ci.derivee(DL.taylor("sin", 7))
check(d_sin == DL.taylor("cos", 6), "cos == derivee(sin)")

# ── 4) DÉVELOPPEMENT DE POLYNÔME autour de a ──
# (x³−3x+2) autour de a=1 = (x−1)³ + 3(x−1)² -> [0,0,3,1] (calcul à la main)
check(DL.taylor_polynome([2, -3, 0, 1], 1, 3) == [F(0), F(0), F(3), F(1)], "Taylor(x³-3x+2) en 1 = [0,0,3,1]")
# x² autour de a=1 = (x−1)² + 2(x−1) + 1 -> [1,2,1]
check(DL.taylor_polynome([0, 0, 1], 1, 2) == [F(1), F(2), F(1)], "Taylor(x²) en 1 = [1,2,1]")
# Taylor autour de a=0 rend le polynôme lui-même
check(DL.taylor_polynome([2, -3, 0, 1], 0, 3) == [F(2), F(-3), F(0), F(1)], "Taylor en 0 = polynôme original")
# CHEMIN INDÉPENDANT : évaluer q(u) en u = x−a doit reproduire p(x) (via ci.evalue)
p = [F(5), F(-2), F(7), F(-1), F(3)]
a = F(2)
q = DL.taylor_polynome(p, a, 4)                      # coefficients en (x−a)
for xt in (F(0), F(1), F(3), F(-1)):
    val_q = ci.evalue(q, xt - a)
    val_p = ci.evalue(p, xt)
    check(val_q == val_p, f"q(x-a) == p(x) en x={xt} (reconstruction exacte)")

# ── 5) APPROXIMATION AVEC BORNE — chemin indépendant math.* ──
val_e, b_e = DL.approxime("exp", 4, 0.1)
check(proche(val_e, 1.10517083, tol=1e-6), "exp(0.1) ordre 4 ~ 1.10517083")
check(abs(math.exp(0.1) - float(val_e)) <= float(b_e), "|exp(0.1) vrai − approx| ≤ borne (Lagrange)")
check(float(b_e) > 0, "borne exp(0.1) strictement positive")
val_s, b_s = DL.approxime("sin", 5, 0.5)
check(abs(math.sin(0.5) - float(val_s)) <= float(b_s), "|sin(0.5) vrai − approx| ≤ borne")
check(proche(val_s, math.sin(0.5), tol=1e-3), "sin(0.5) ordre 5 proche de math.sin")
val_c, b_c = DL.approxime("cos", 6, 0.3)
check(abs(math.cos(0.3) - float(val_c)) <= float(b_c), "|cos(0.3) vrai − approx| ≤ borne")
# borne décroît quand l'ordre monte (à x fixé, |x|<1)
_, b_e2 = DL.approxime("exp", 4, F(1, 4))
_, b_e8 = DL.approxime("exp", 8, F(1, 4))
check(b_e8 < b_e2, "borne exp décroît quand l'ordre augmente (x=1/4)")
# approxime rend TOUJOURS un couple (jamais une valeur nue)
res = DL.approxime("exp", 3, 0.0)
check(isinstance(res, tuple) and len(res) == 2, "approxime renvoie un couple (valeur, borne)")
check(res[0] == F(1) and res[1] == F(0), "approxime exp en 0 = (1, 0) exact")
# valeur = Fraction exacte
check(isinstance(val_e, Fraction) and isinstance(b_e, Fraction), "approxime rend des Fraction exactes")

# ── 6) RESTE DE LAGRANGE explicite ──
# borne exp ordre 4 en x=1/2, M=3 (majorant de e^0.5 fourni) = 3·(1/2)^5/5! = 3/(32·120) = 1/1280
check(DL.borne_reste_lagrange("exp", 4, F(1, 2), 3) == F(1, 1280), "Lagrange exp o4 x=1/2 M=3 = 1/1280")
# borne sin ordre 3 en x=1, M=1 = 1·1^4/4! = 1/24
check(DL.borne_reste_lagrange("sin", 3, 1, 1) == F(1, 24), "Lagrange sin o3 x=1 M=1 = 1/24")
# la borne fournie majore effectivement l'erreur réelle pour cos
b_cos = DL.borne_reste_lagrange("cos", 4, F(1, 2), 1)   # M=1 valide pour cos
approx_cos = sum(c * F(1, 2) ** k for k, c in enumerate(DL.taylor("cos", 4)))
check(abs(math.cos(0.5) - float(approx_cos)) <= float(b_cos), "borne Lagrange cos majore l'erreur réelle")

# ── 7) RAYON DE CONVERGENCE ──
check(DL.rayon_convergence("exp") == math.inf, "rayon exp = +inf")
check(DL.rayon_convergence("sin") == math.inf, "rayon sin = +inf")
check(DL.rayon_convergence("ln1p") == 1, "rayon ln(1+x) = 1")
check(DL.rayon_convergence("arctan") == 1, "rayon arctan = 1")
check(DL.rayon_convergence("geometrique") == 1, "rayon 1/(1-x) = 1")
check(DL.rayon_convergence("binome") == 1, "rayon binome = 1")

# ── 8) SOUNDNESS — hors rayon de convergence (ancre imposée : ln(1+x) en 1.5) ──
check(leve(DL.borne_reste_lagrange, "ln1p", 3, 1.5, 1), "ln(1+x) en x=1.5 -> ValueError (hors rayon)")
check(leve(DL.borne_reste_lagrange, "arctan", 3, 2.0, 1), "arctan en x=2 -> ValueError (hors rayon)")
check(leve(DL.borne_reste_lagrange, "geometrique", 3, 1, 1), "1/(1-x) en x=1 -> ValueError (|x|=rayon)")
check(leve(DL.borne_reste_lagrange, "ln1p", 3, F(-3, 2), 1), "ln(1+x) en x=-3/2 -> ValueError (hors rayon)")
# exp/sin convergent partout : pas d'abstention rayon
check(DL.borne_reste_lagrange("exp", 4, 5.0, 200) > 0, "exp en x=5 : borne définie (rayon infini)")

# ── 9) SOUNDNESS — hors catalogue / ordre ──
check(leve(DL.taylor, "tan", 4), "fonction hors catalogue -> ValueError")
check(leve(DL.taylor, "EXP", 4), "nom sensible à la casse -> ValueError")
check(leve(DL.taylor, "exp", -1), "ordre <0 -> ValueError")
check(leve(DL.taylor, "exp", 2.0), "ordre flottant -> ValueError")
check(leve(DL.taylor, "exp", True), "ordre bool -> ValueError")
check(leve(DL.rayon_convergence, "inconnue"), "rayon hors catalogue -> ValueError")
check(leve(DL.approxime, "ln1p", 3, 0.5), "approxime ln1p (pas de majorant auto) -> ValueError")
check(leve(DL.approxime, "arctan", 3, 0.5), "approxime arctan (pas de majorant auto) -> ValueError")

# ── 10) SOUNDNESS — série binomiale ──
check(leve(DL.taylor, "binome", 4), "binome sans alpha -> ValueError")
check(leve(DL.taylor, "binome", 4, alpha=0.5), "binome alpha flottant -> ValueError")
check(leve(DL.taylor, "binome", 4, alpha=True), "binome alpha bool -> ValueError")
check(leve(DL.taylor, "binome", 4, alpha="pas_un_nombre"), "binome alpha str non rationnel -> ValueError")
# alpha rationnel en chaîne accepté
check(DL.taylor("binome", 2, alpha="1/2") == [F(1), F(1, 2), F(-1, 8)], "binome alpha='1/2' accepté (str rationnelle)")

# ── 11) SOUNDNESS — taylor_polynome (exactitude : flottants refusés) ──
check(leve(DL.taylor_polynome, [1, 2, 0.5], 1, 2), "coeff flottant -> ValueError")
check(leve(DL.taylor_polynome, [1, 2, 3], 1.5, 2), "point a flottant -> ValueError")
check(leve(DL.taylor_polynome, [1, True, 3], 1, 2), "coeff bool -> ValueError")
check(leve(DL.taylor_polynome, [], 1, 2), "coeffs vide -> ValueError")
check(leve(DL.taylor_polynome, 5, 1, 2), "coeffs non-séquence -> ValueError")
check(leve(DL.taylor_polynome, [1, 2, 3], 1, -1), "taylor_polynome ordre<0 -> ValueError")
# a rationnel en chaîne accepté
check(DL.taylor_polynome([0, 0, 1], "1", 2) == [F(1), F(2), F(1)], "taylor_polynome a='1' accepté")

# ── 12) SOUNDNESS — types (bool / str / NaN / inf) sur les points d'évaluation ──
check(leve(DL.approxime, "exp", 4, float("nan")), "approxime x=NaN -> ValueError")
check(leve(DL.approxime, "exp", 4, float("inf")), "approxime x=inf -> ValueError")
check(leve(DL.approxime, "exp", 4, "abc"), "approxime x=str non numérique -> ValueError")
check(leve(DL.approxime, "exp", 4, True), "approxime x=bool -> ValueError")
check(leve(DL.borne_reste_lagrange, "exp", 4, 1.0, float("inf")), "majorant=inf -> ValueError")
check(leve(DL.borne_reste_lagrange, "exp", 4, 1.0, -2), "majorant négatif -> ValueError")
check(leve(DL.approxime, "exp", 4, 1j), "approxime x complexe -> ValueError")
# x flottant fini accepté sur approxime (point d'évaluation)
check(isinstance(DL.approxime("exp", 4, 0.25)[0], Fraction), "approxime x flottant fini accepté")

# ── 13) DÉTERMINISME ──
check(DL.taylor("exp", 6) == DL.taylor("exp", 6), "déterminisme taylor")
check(DL.approxime("exp", 4, 0.1) == DL.approxime("exp", 4, 0.1), "déterminisme approxime")
check(DL.taylor_polynome([2, -3, 0, 1], 1, 3) == DL.taylor_polynome([2, -3, 0, 1], 1, 3), "déterminisme taylor_polynome")
check(DL.borne_reste_lagrange("exp", 4, F(1, 2), 3) == DL.borne_reste_lagrange("exp", 4, F(1, 2), 3), "déterminisme borne")

print(f"\n=== valide_developpement_limite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
