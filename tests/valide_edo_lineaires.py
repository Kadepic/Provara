"""
VALIDE edo_lineaires.py — held-out ADVERSE (EDO linéaires du 2e ordre à coefficients constants).

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée, écrites en dur avec leur provenance) :
  • y'' − 3y' + 2y = 0 : équation caractéristique r²−3r+2=(r−1)(r−2) -> racines 1 et 2 (régime apériodique).
      CI y(0)=0, y'(0)=1 -> C1=−1, C2=1 (résolus À LA MAIN), solution e^(2x)−e^x.
      Ancre numérique : en x=1, e²−e ≈ 4.6707742705 (e²=7.389056099, e=2.718281828).
  • y'' + 2y' + y = 0 : r²+2r+1=(r+1)² -> racine double −1 (régime critique).
      CI y(0)=1, y'(0)=0 -> (1+x)e^(−x). Ancre : en x=1, 2/e ≈ 0.7357588823.
  • y'' + y = 0 : r²+1=0 -> racines ±i (régime pseudo-périodique).
      CI y(0)=0, y'(0)=1 -> sin(x). Ancre : en x=π/2, sin=1.0 (±1e-9).
  • ANCRE CROISÉE : la solution de resout_cauchy, réinjectée dans a·y''+b·y'+c·y, doit valoir 0 —
      testé par DIFFÉRENCES FINIES CENTRÉES (h=1e-4) sur 10 points, indépendamment des constantes.
  • Oscillateur amorti : régime par le signe de c²−4mk (ancre physique), ω₀=√(k/m), ζ=c/(2√(mk)).

SOUNDNESS : a=0, bool, str, NaN, inf, mauvaise arité -> ValueError ; RuntimeError jamais sur cas valides.
DÉTERMINISME : deux appels identiques -> mêmes valeurs.
"""
import math
from fractions import Fraction

import edo_lineaires as E

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


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


PI = math.pi
E2 = math.e * math.e  # e² ≈ 7.389056099

# ══ 1) ÉQUATION CARACTÉRISTIQUE — discriminant EXACT + nature + racines ═══════════════════════════════════════════
eq1 = E.equation_caracteristique(1, -3, 2)
check(eq1["discriminant"] == Fraction(1), "Δ(1,-3,2)=1 exact")                       # 9-8=1
check(isinstance(eq1["discriminant"], Fraction), "Δ est une Fraction (entrées exactes)")
check(eq1["nature"] == "reelles_distinctes", "nature apériodique")
check(eq1["racines"][0] == 1 and eq1["racines"][1] == 2, "racines (1,2) ascendantes")  # (r-1)(r-2)

eq2 = E.equation_caracteristique(1, 2, 1)
check(eq2["discriminant"] == Fraction(0), "Δ(1,2,1)=0 exact")                        # 4-4=0
check(eq2["nature"] == "reelle_double", "nature critique (racine double)")
check(eq2["racines"][0] == -1 and eq2["racines"][1] == -1, "racine double -1")       # (r+1)²

eq3 = E.equation_caracteristique(1, 0, 1)
check(eq3["discriminant"] == Fraction(-4), "Δ(1,0,1)=-4 exact")                      # 0-4=-4
check(eq3["nature"] == "complexes", "nature pseudo-périodique")
check(proche(eq3["racines"][0].real, 0.0) and proche(eq3["racines"][0].imag, 1.0),
      "racines ±i (α=0, β=1)")

# discriminant flottant si une entrée flottante (valeur APPROCHÉE, pas Fraction)
eqf = E.equation_caracteristique(1.0, -3.0, 2.0)
check(isinstance(eqf["discriminant"], float), "Δ flottant si entrée flottante")
check(proche(eqf["discriminant"], 1.0), "Δ(1.0,-3.0,2.0) ≈ 1")

# ══ 2) SOLUTION HOMOGÈNE — les trois régimes + forme littérale ═══════════════════════════════════════════════════
sh1 = E.solution_homogene(1, -3, 2)
check(sh1["regime"] == "aperiodique", "régime apériodique")
check("exp" in sh1["forme"] and "C1" in sh1["forme"] and "C2" in sh1["forme"], "forme apériodique littérale")
sh2 = E.solution_homogene(1, 2, 1)
check(sh2["regime"] == "critique", "régime critique")
check("x)*exp" in sh2["forme"] or "C2*x" in sh2["forme"], "forme critique (C1+C2 x) e^(rx)")
sh3 = E.solution_homogene(1, 0, 1)
check(sh3["regime"] == "pseudo-periodique", "régime pseudo-périodique")
check("cos" in sh3["forme"] and "sin" in sh3["forme"], "forme pseudo-périodique cos/sin")

# ══ 3) CAUCHY apériodique : y(0)=0,y'(0)=1 -> e^(2x)-e^x (C1=-1, C2=1 à la main) ══════════════════════════════════
c1 = E.resout_cauchy(1, -3, 2, 0, 1)
check(c1["C1"] == -1 and c1["C2"] == 1, "constantes C1=-1, C2=1 (résolues à la main)")
check(proche(c1["solution"](1.0), E2 - math.e), "y(1) = e²-e ≈ 4.6707742705")
check(proche(c1["solution"](1.0), 4.6707742705, tol=1e-9), "ancre numérique 4.6707742705")
check(proche(c1["solution"](0.0), 0.0), "y(0)=0 respecté")
# y'(0)=1 : différence finie centrée
dfd = (c1["solution"](1e-6) - c1["solution"](-1e-6)) / (2e-6)
check(proche(dfd, 1.0, tol=1e-5), "y'(0)=1 (différence finie)")

# ══ 4) CAUCHY critique : y(0)=1,y'(0)=0 -> (1+x)e^(-x) ; en x=1 : 2/e ═══════════════════════════════════════════
c2 = E.resout_cauchy(1, 2, 1, 1, 0)
check(c2["C1"] == 1 and c2["C2"] == 1, "constantes C1=1, C2=1")
check(proche(c2["solution"](1.0), 2.0 / math.e), "y(1)=2/e")
check(proche(c2["solution"](1.0), 0.7357588823, tol=1e-9), "ancre numérique 0.7357588823")
check(proche(c2["solution"](0.0), 1.0), "y(0)=1 respecté")

# ══ 5) CAUCHY pseudo-périodique : y(0)=0,y'(0)=1 -> sin(x) ; en x=π/2 : 1.0 ═════════════════════════════════════
c3 = E.resout_cauchy(1, 0, 1, 0, 1)
check(c3["C1"] == 0 and c3["C2"] == 1, "constantes C1=0, C2=1 -> sin(x)")
check(proche(c3["solution"](PI / 2), 1.0, tol=1e-9), "y(π/2)=1.0 (±1e-9)")
check(proche(c3["solution"](PI), 0.0, tol=1e-9), "y(π)=sin(π)=0")
check(proche(c3["solution"](PI / 6), 0.5, tol=1e-9), "y(π/6)=sin(π/6)=1/2")

# ══ 6) ANCRE CROISÉE : la solution SATISFAIT l'EDO (différences finies centrées, 10 points) ═════════════════════
def residu_max(a, b, c, y0, yp0, h=1e-4):
    sol = E.resout_cauchy(a, b, c, y0, yp0)["solution"]
    pire = 0.0
    for i in range(1, 11):                       # 10 points x = 0.1 .. 1.0
        x = 0.1 * i
        ypp = (sol(x + h) - 2 * sol(x) + sol(x - h)) / (h * h)
        yp = (sol(x + h) - sol(x - h)) / (2 * h)
        r = a * ypp + b * yp + c * sol(x)
        pire = max(pire, abs(r))
    return pire

check(residu_max(1, -3, 2, 0, 1) < 1e-3, "EDO apériodique satisfaite (résidu < 1e-3)")
check(residu_max(1, 2, 1, 1, 0) < 1e-3, "EDO critique satisfaite (résidu < 1e-3)")
check(residu_max(1, 0, 1, 0, 1) < 1e-3, "EDO pseudo-périodique satisfaite (résidu < 1e-3)")
# un cas non trivial supplémentaire : 2y'' + 3y' + 1y = 0 (racines -1/2, -1), CI quelconques
check(residu_max(2, 3, 1, 5, -2) < 1e-3, "EDO générique 2y''+3y'+y satisfaite")

# ══ 7) OSCILLATEUR AMORTI — régimes + ω₀ + ζ (ancres physiques) ═════════════════════════════════════════════════
o1 = E.oscillateur_amorti(1, 0, 4)               # c=0 : non amorti -> sous-amorti, ω₀=√4=2, ζ=0
check(o1["regime"] == "sous-amorti", "non amorti -> sous-amorti")
check(proche(o1["pulsation_propre"], 2.0), "ω₀=√(4/1)=2")
check(proche(o1["facteur_amortissement"], 0.0), "ζ=0 (c=0)")

o2 = E.oscillateur_amorti(1, 2, 1)               # c²-4mk=4-4=0 -> critique, ζ=2/(2√1)=1
check(o2["regime"] == "critique", "c²=4mk -> critique")
check(proche(o2["pulsation_propre"], 1.0), "ω₀=1")
check(proche(o2["facteur_amortissement"], 1.0), "ζ=1 (critique)")

o3 = E.oscillateur_amorti(1, 3, 1)               # 9-4=5>0 -> sur-amorti, ζ=3/(2√1)=1.5
check(o3["regime"] == "sur-amorti", "c²>4mk -> sur-amorti")
check(proche(o3["facteur_amortissement"], 1.5), "ζ=1.5")

o4 = E.oscillateur_amorti(2, 1, 8)               # ω₀=√(8/2)=2 ; ζ=1/(2√16)=1/8=0.125 ; 1-64<0 sous-amorti
check(o4["regime"] == "sous-amorti", "sous-amorti (faible c)")
check(proche(o4["pulsation_propre"], 2.0), "ω₀=√(8/2)=2")
check(proche(o4["facteur_amortissement"], 0.125), "ζ=1/(2√16)=0.125")

# ══ 8) 1er ORDRE délégué à equa_diff ═══════════════════════════════════════════════════════════════════════════
check(proche(E.resout_premier_ordre(1, 1, 1), math.e, tol=1e-8), "y'=y, y0=1, t=1 -> e (délégation)")
check(proche(E.resout_premier_ordre(100, -0.1, 0), 100.0), "y'=-0.1y, t=0 -> 100")
check(proche(E.resout_premier_ordre_affine(100, -1, 20, 0), 100.0), "affine t=0 -> y0")

# ══ 9) SOUNDNESS — a=0 (plus du 2e ordre) ═══════════════════════════════════════════════════════════════════════
check(leve(E.equation_caracteristique, 0, 1, 1), "eq. carac. a=0 -> ValueError")
check(leve(E.solution_homogene, 0, 1, 1), "solution_homogene a=0 -> ValueError")
check(leve(E.resout_cauchy, 0, 1, 1, 1, 1), "resout_cauchy a=0 -> ValueError")

# ══ 10) SOUNDNESS — bool / str / NaN / inf ═════════════════════════════════════════════════════════════════════
check(leve(E.equation_caracteristique, True, 1, 1), "a=bool -> ValueError")
check(leve(E.equation_caracteristique, 1, "0", 1), "b=str -> ValueError")
check(leve(E.equation_caracteristique, 1, 0, float("nan")), "c=NaN -> ValueError")
check(leve(E.equation_caracteristique, float("inf"), 0, 1), "a=inf -> ValueError")
check(leve(E.resout_cauchy, 1, -3, 2, True, 1), "y0=bool -> ValueError")
check(leve(E.resout_cauchy, 1, -3, 2, 0, "1"), "yp0=str -> ValueError")
check(leve(E.resout_cauchy, 1, -3, 2, 0, float("inf")), "yp0=inf -> ValueError")

# ══ 11) SOUNDNESS — oscillateur (m>0, k>0, c≥0) ════════════════════════════════════════════════════════════════
check(leve(E.oscillateur_amorti, 0, 1, 1), "m=0 -> ValueError")
check(leve(E.oscillateur_amorti, -1, 1, 1), "m<0 -> ValueError")
check(leve(E.oscillateur_amorti, 1, 1, 0), "k=0 -> ValueError")
check(leve(E.oscillateur_amorti, 1, 1, -1), "k<0 -> ValueError")
check(leve(E.oscillateur_amorti, 1, -1, 1), "c<0 -> ValueError")
check(leve(E.oscillateur_amorti, 1, True, 1), "c=bool -> ValueError")
check(leve(E.oscillateur_amorti, 1, float("nan"), 1), "c=NaN -> ValueError")

# ══ 12) DÉTERMINISME ═══════════════════════════════════════════════════════════════════════════════════════════
check(E.equation_caracteristique(1, -3, 2) == E.equation_caracteristique(1, -3, 2), "déterminisme eq. carac.")
check(E.oscillateur_amorti(1, 2, 1) == E.oscillateur_amorti(1, 2, 1), "déterminisme oscillateur")
check(E.resout_cauchy(1, -3, 2, 0, 1)["solution"](1.3)
      == E.resout_cauchy(1, -3, 2, 0, 1)["solution"](1.3), "déterminisme solution évaluée")

# ══ 13) EXACTITUDE Fraction en entrée -> racines/constantes exactes ═════════════════════════════════════════════
cf = E.resout_cauchy(Fraction(1), Fraction(-3), Fraction(2), Fraction(0), Fraction(1))
check(isinstance(cf["C1"], Fraction) and cf["C1"] == -1, "C1 exact (Fraction) = -1")
check(cf["racines"][0] == 1 and cf["racines"][1] == 2, "racines exactes (1,2) en Fraction")

print(f"\n=== valide_edo_lineaires : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
