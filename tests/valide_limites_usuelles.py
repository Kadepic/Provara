"""
VALIDE limites_usuelles.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par la formule testée) :
  • (3x²+1)/(2x²+x) -> 3/2 : rapport des dominants, calcul à la main (3/2 écrit EN DUR).
    Contre-vérifié NUMÉRIQUEMENT par évaluation directe du quotient en x = 10⁷ (second chemin, math pur).
  • (x+1)/(x²+1) -> 0 ; (x²+1)/(x+1) -> +∞ ; (−x²)/(x+1) -> −∞ : théorème du terme dominant, valeurs
    classiques de cours, contre-vérifiées numériquement en x = 10⁷.
  • Géométrique : r=1/2 -> 0 ; r=2 -> +∞ ; r=1 -> 1 ; r=−1 -> divergente. (0.5)^50 ≈ 8.9e−16 (math.pow,
    second chemin) confirme la fuite vers 0 ; 2^50 ≈ 1.1e15 confirme l'explosion.
  • CATALOGUE : chaque limite est contre-vérifiée par un SECOND chemin numérique indépendant (math) :
    sin(1e−9)/1e−9 ≈ 1 ; (1−cos(1e−4))/(1e−4)² ≈ 0.5 ; expm1/log1p en 1e−9 ≈ 1 ; (1+1e−7)^(10⁷) ≈ e =
    2.718281828 (constante écrite EN DUR) ; ln(10⁷)/10⁷ ≈ 0 ; 1e−9·ln(1e−9) ≈ 0 ; e¹⁰⁰/100³ énorme et
    croissant ; Stirling via math.lgamma : exp(lgamma(n+1)/n − ln n) ≈ 1/e = 0.3678794412 (EN DUR).

SOUNDNESS : flottants dans la partie exacte, bool, str, NaN, inf, dénominateur nul, listes vides,
forme inventée hors catalogue -> ValueError.
"""
import math
from fractions import Fraction

import limites_usuelles as L

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


def proche(x, attendu, tol=1e-5):
    return abs(x - attendu) <= tol


E_REF = 2.718281828       # e, constante mathématique connue (Euler) — écrite EN DUR, pas recalculée
INV_E_REF = 0.3678794412  # 1/e, constante connue — écrite EN DUR

# ── 1) RATIONNELLES EN +∞ — ancres à la main (degré décroissant, dominant en tête) ──
# (3x²+1)/(2x²+x) : degrés égaux, dominants 3 et 2 -> 3/2 EXACT (calcul à la main)
r1 = L.limite_rationnelle_infini([3, 0, 1], [2, 1, 0])
check(r1 == Fraction(3, 2), "(3x²+1)/(2x²+x) -> 3/2 exact")
check(isinstance(r1, Fraction), "résultat degrés égaux est une Fraction (exact)")
# second chemin NUMÉRIQUE indépendant : évaluation directe du quotient en x=1e7
x = 1e7
check(proche((3 * x * x + 1) / (2 * x * x + x), 1.5), "second chemin : quotient en x=10⁷ ≈ 1.5")

# (x+1)/(x²+1) : deg 1 < deg 2 -> 0
r2 = L.limite_rationnelle_infini([1, 1], [1, 0, 1])
check(r2 == Fraction(0), "(x+1)/(x²+1) -> 0")
check(proche((x + 1) / (x * x + 1), 0.0), "second chemin : (x+1)/(x²+1) en x=10⁷ ≈ 0")

# (x²+1)/(x+1) : deg 2 > deg 1, dominants 1/1 > 0 -> +inf
check(L.limite_rationnelle_infini([1, 0, 1], [1, 1]) == "+inf", "(x²+1)/(x+1) -> '+inf'")
check((x * x + 1) / (x + 1) > 1e6, "second chemin : (x²+1)/(x+1) en x=10⁷ est énorme (>10⁶)")

# (−x²)/(x+1) : deg 2 > deg 1, dominants −1/1 < 0 -> -inf
check(L.limite_rationnelle_infini([-1, 0, 0], [1, 1]) == "-inf", "(−x²)/(x+1) -> '-inf'")
check((-x * x) / (x + 1) < -1e6, "second chemin : (−x²)/(x+1) en x=10⁷ très négatif (<−10⁶)")

# zéros de tête retirés : [0, 3, 0, 1] est le MÊME polynôme 3x²+1 -> même limite 3/2
check(L.limite_rationnelle_infini([0, 3, 0, 1], [2, 1, 0]) == Fraction(3, 2),
      "zéro de tête au numérateur ignoré : toujours 3/2")
check(L.limite_rationnelle_infini([1, 1], [0, 1, 0, 1]) == Fraction(0),
      "zéro de tête au dénominateur ignoré : (x+1)/(x²+1) -> 0")
# coefficients Fraction acceptés : (x/2 + 1)/(x/3) -> (1/2)/(1/3) = 3/2 (à la main)
check(L.limite_rationnelle_infini([Fraction(1, 2), 1], [Fraction(1, 3), 0]) == Fraction(3, 2),
      "coefficients Fraction : (x/2+1)/(x/3) -> 3/2")
# numérateur identiquement nul : 0/Q -> 0
check(L.limite_rationnelle_infini([0, 0], [1, 1]) == Fraction(0), "numérateur nul -> 0")
# constantes : 6/4 -> 3/2 (degrés 0 égaux)
check(L.limite_rationnelle_infini([6], [4]) == Fraction(3, 2), "constantes 6/4 -> 3/2")

# ── 2) SUITE GÉOMÉTRIQUE ──
check(L.limite_suite_geometrique(Fraction(1, 2)) == Fraction(0), "géométrique r=1/2 -> 0")
check(L.limite_suite_geometrique(2) == "+inf", "géométrique r=2 -> '+inf'")
check(L.limite_suite_geometrique(1) == Fraction(1), "géométrique r=1 -> 1")
check(L.limite_suite_geometrique(-1) == "divergente_sans_limite", "géométrique r=−1 -> divergente")
check(L.limite_suite_geometrique(Fraction(-3, 2)) == "divergente_sans_limite", "géométrique r=−3/2 -> divergente")
check(L.limite_suite_geometrique(Fraction(-1, 2)) == Fraction(0), "géométrique r=−1/2 -> 0 (|r|<1)")
check(L.limite_suite_geometrique(0) == Fraction(0), "géométrique r=0 -> 0")
# second chemin numérique : (1/2)^50 et 2^50 confirment fuite vers 0 / explosion
check(math.pow(0.5, 50) < 1e-10, "second chemin : (1/2)^50 ≈ 0")
check(math.pow(2.0, 50) > 1e10, "second chemin : 2^50 énorme")

# ── 3) CATALOGUE — valeurs + contre-vérification NUMÉRIQUE indépendante (math, second chemin) ──
# sin(x)/x -> 1 en 0
u = L.limite_usuelle("sin(x)/x")
check(u["valeur"] == Fraction(1) and u["approchee"] is False, "catalogue sin(x)/x -> 1 exact")
check(proche(math.sin(1e-9) / 1e-9, 1.0), "numérique : sin(1e−9)/1e−9 ≈ 1")

# (1−cos x)/x² -> 1/2 en 0  (x=1e−4 : assez petit pour la limite, assez grand pour éviter la cancellation)
u = L.limite_usuelle("(1-cos(x))/x^2")
check(u["valeur"] == Fraction(1, 2) and u["approchee"] is False, "catalogue (1−cos x)/x² -> 1/2 exact")
check(proche((1.0 - math.cos(1e-4)) / (1e-4 ** 2), 0.5), "numérique : (1−cos(1e−4))/(1e−4)² ≈ 0.5")

# (e^x−1)/x -> 1 en 0
u = L.limite_usuelle("(exp(x)-1)/x")
check(u["valeur"] == Fraction(1) and u["approchee"] is False, "catalogue (e^x−1)/x -> 1 exact")
check(proche(math.expm1(1e-9) / 1e-9, 1.0), "numérique : expm1(1e−9)/1e−9 ≈ 1")

# ln(1+x)/x -> 1 en 0
u = L.limite_usuelle("ln(1+x)/x")
check(u["valeur"] == Fraction(1) and u["approchee"] is False, "catalogue ln(1+x)/x -> 1 exact")
check(proche(math.log1p(1e-9) / 1e-9, 1.0), "numérique : log1p(1e−9)/1e−9 ≈ 1")

# (1+1/n)^n -> e (APPROCHÉ et marqué tel)
u = L.limite_usuelle("(1+1/n)^n")
check(proche(u["valeur"], E_REF, tol=1e-8), "catalogue (1+1/n)^n -> e = 2.718281828 (constante en dur)")
check(u["approchee"] is True, "e est MARQUÉ approché")
check(proche((1.0 + 1e-7) ** 1e7, E_REF), "numérique : (1+1e−7)^(10⁷) ≈ e")

# ln(x)/x -> 0 en +∞
u = L.limite_usuelle("ln(x)/x")
check(u["valeur"] == Fraction(0) and u["approchee"] is False, "catalogue ln(x)/x -> 0 exact")
check(proche(math.log(1e7) / 1e7, 0.0), "numérique : ln(10⁷)/10⁷ ≈ 0")

# x·ln(x) -> 0 en 0⁺
u = L.limite_usuelle("x*ln(x)")
check(u["valeur"] == Fraction(0) and u["approchee"] is False, "catalogue x·ln(x) -> 0 exact")
check(proche(1e-9 * math.log(1e-9), 0.0), "numérique : 1e−9·ln(1e−9) ≈ 0")

# e^x/x^n -> +∞ (n=3 : valeur énorme ET croissante entre x=50 et x=100)
u = L.limite_usuelle("exp(x)/x^n")
check(u["valeur"] == "+inf", "catalogue e^x/x^n -> '+inf'")
v50 = math.exp(50) / 50 ** 3
v100 = math.exp(100) / 100 ** 3
check(v100 > v50 > 1e10, "numérique : e^x/x³ énorme et croissant (x=50 puis 100)")

# n!^(1/n)/n -> 1/e (Stirling ; second chemin via math.lgamma, JAMAIS la valeur du module)
u = L.limite_usuelle("n!^(1/n)/n")
check(proche(u["valeur"], INV_E_REF, tol=1e-8), "catalogue n!^(1/n)/n -> 1/e = 0.3678794412 (constante en dur)")
check(u["approchee"] is True, "1/e est MARQUÉ approché")
n = 1e7
stirling = math.exp(math.lgamma(n + 1) / n - math.log(n))   # (n!)^(1/n)/n via lgamma — chemin indépendant
check(proche(stirling, INV_E_REF), "numérique : lgamma(10⁷+1)/10⁷ − ln(10⁷), exp ≈ 1/e")

# structure de la réponse + catalogue complet
check(u["reference"] != "" and "Stirling" in u["reference"], "référence textuelle fournie (Stirling)")
check(len(L.catalogue_limites()) == 9, "catalogue : exactement 9 formes établies")
check("sin(x)/x" in L.catalogue_limites(), "catalogue expose sin(x)/x")

# ── 4) SOUNDNESS — rationnelles : flottants et types refusés ──
check(leve(L.limite_rationnelle_infini, [3.0, 0, 1], [2, 1, 0]), "coefficient flottant num -> ValueError")
check(leve(L.limite_rationnelle_infini, [3, 0, 1], [2, 1.5, 0]), "coefficient flottant den -> ValueError")
check(leve(L.limite_rationnelle_infini, [True, 1], [1, 0]), "coefficient bool -> ValueError")
check(leve(L.limite_rationnelle_infini, ["3", 1], [1, 0]), "coefficient str -> ValueError")
check(leve(L.limite_rationnelle_infini, [float("nan")], [1]), "coefficient NaN -> ValueError")
check(leve(L.limite_rationnelle_infini, [float("inf")], [1]), "coefficient inf -> ValueError")
check(leve(L.limite_rationnelle_infini, [], [1, 0]), "num vide -> ValueError")
check(leve(L.limite_rationnelle_infini, [1, 0], []), "den vide -> ValueError")
check(leve(L.limite_rationnelle_infini, [1, 1], [0, 0, 0]), "dénominateur identiquement nul -> ValueError")
check(leve(L.limite_rationnelle_infini, 3, [1, 0]), "num non-séquence -> ValueError")
check(leve(L.limite_rationnelle_infini, [1, 1], 2), "den non-séquence -> ValueError")

# ── 5) SOUNDNESS — géométrique : flottants et types refusés ──
check(leve(L.limite_suite_geometrique, 0.5), "raison flottante -> ValueError (Fraction(1,2) requis)")
check(leve(L.limite_suite_geometrique, True), "raison bool -> ValueError")
check(leve(L.limite_suite_geometrique, "1/2"), "raison str -> ValueError")
check(leve(L.limite_suite_geometrique, float("nan")), "raison NaN -> ValueError")
check(leve(L.limite_suite_geometrique, float("inf")), "raison inf -> ValueError")

# ── 6) SOUNDNESS — catalogue : forme inventée -> abstention ──
check(leve(L.limite_usuelle, "tan(x)/x"), "forme hors catalogue (tan(x)/x) -> ValueError")
check(leve(L.limite_usuelle, "x^x"), "forme inventée (x^x) -> ValueError")
check(leve(L.limite_usuelle, ""), "forme vide -> ValueError")
check(leve(L.limite_usuelle, 42), "nom non-str -> ValueError")
check(leve(L.limite_usuelle, True), "nom bool -> ValueError")

# ── 7) DÉTERMINISME ──
check(L.limite_rationnelle_infini([3, 0, 1], [2, 1, 0]) == L.limite_rationnelle_infini([3, 0, 1], [2, 1, 0]),
      "déterminisme rationnelle")
check(L.limite_suite_geometrique(Fraction(-3, 2)) == L.limite_suite_geometrique(Fraction(-3, 2)),
      "déterminisme géométrique")
check(L.limite_usuelle("sin(x)/x") == L.limite_usuelle("sin(x)/x"), "déterminisme catalogue")
check(L.catalogue_limites() == L.catalogue_limites(), "déterminisme liste du catalogue")

print(f"\n=== valide_limites_usuelles : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
