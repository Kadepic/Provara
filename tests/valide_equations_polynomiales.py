"""
VALIDE equations_polynomiales.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT du module, jamais recalculées par lui) :
  • x³ − 6x² + 11x − 6 = (x−1)(x−2)(x−3) (factorisation vérifiable à la main) -> racines EXACTES 1, 2, 3.
  • x³ − 2 : unique racine réelle ∛2, calculée ICI par 2**(1/3) (fonction puissance de Python, hors module)
    ≈ 1.2599210498948732 ; l'intervalle rendu doit la contenir ET satisfaire le certificat EXACT
    lo³ ≤ 2 ≤ hi³ (arithmétique Fraction, second chemin indépendant de Sturm) ; + 2 complexes.
  • x³ − x = x(x−1)(x+1) -> racines exactes 0, 1, −1.
  • x⁴ − 5x² + 4 = (x²−1)(x²−4) -> racines exactes −2, −1, 1, 2.
  • x⁴ + 1 : AUCUNE racine réelle (x⁴ ≥ 0 donc x⁴ + 1 ≥ 1 > 0, preuve à la main), 4 complexes.
  • VIÈTE (exact) : Σ racines = −b/a, Π racines = (−1)ⁿ·(coeff constant)/a — relations classiques,
    vérifiées sur les racines RENDUES avec des attendus écrits EN DUR.
  • Discriminants cubiques calculés À LA MAIN dans les commentaires (Δ=4, Δ=81, Δ=−108, Δ=0) et
    confrontés à la règle : Δ > 0 ⇔ 3 racines réelles distinctes (3 exemples + contre-exemples).
  • √2 ≈ 1.4142135623730951 calculé ICI par math.sqrt(2) (hors module) pour le degré 2.
  • COEFFICIENTS GÉANTS : (x − 1)(x − (10¹³+7)) = x² − (10¹³+8)x + (10¹³+7) — développement vérifiable
    à la main : les DEUX racines (1 et 10¹³+7) sont RATIONNELLES. La recherche rationnelle renonce
    (coefficient > 10¹²) : le module ne doit RIEN affirmer irrationnel — les racines vont dans
    'reelles_non_classees' (marquées rationalité indéterminée), jamais dans 'reelles_irrationnelles'.

SOUNDNESS : degré > 4, coefficient dominant nul, degré 0, float/bool/str/complexe/NaN/inf, tol ≤ 0
ou flottant -> ValueError. DÉTERMINISME : double appel, égalité exigée.
"""
import math
from fractions import Fraction

import equations_polynomiales as E

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


def rats(res):
    """Les racines rationnelles rendues, en dict {racine: multiplicité}."""
    return dict(res["rationnelles"])


F = Fraction

# ── 1) ANCRE : x³ − 6x² + 11x − 6 = (x−1)(x−2)(x−3) -> 1, 2, 3 EXACTES ──
r = E.resout([1, -6, 11, -6])
check(rats(r) == {F(1): 1, F(2): 1, F(3): 1}, "x³−6x²+11x−6 : racines exactes {1,2,3}")
check(all(isinstance(x, Fraction) for x, _ in r["rationnelles"]), "racines rendues en Fraction (exactes)")
check(r["reelles_irrationnelles"] == [], "x³−6x²+11x−6 : aucune irrationnelle")
check(r["nb_complexes_non_reelles"] == 0, "x³−6x²+11x−6 : 0 complexe")
check(r["nb_reelles"] == 3, "x³−6x²+11x−6 : 3 réelles")
check(r["degre"] == 3, "x³−6x²+11x−6 : degré 3")
# VIÈTE en dur : Σ = 1+2+3 = 6 = −(−6)/1 ; Π = 1·2·3 = 6 = (−1)³·(−6)/1
check(sum(x for x, _ in r["rationnelles"]) == F(6), "Viète : Σ racines = 6 = −b/a")
p = F(1)
for x, _ in r["rationnelles"]:
    p *= x
check(p == F(6), "Viète : Π racines = 6 = (−1)³·d/a")

# ── 2) ANCRE : x³ − 2 -> unique réelle ∛2 (2**(1/3) HORS module) + 2 complexes ──
CBRT2 = 2 ** (1.0 / 3.0)                                # ≈ 1.2599210498948732, calcul EXTERNE au module
r = E.resout([1, 0, 0, -2])
check(r["rationnelles"] == [], "x³−2 : aucune racine rationnelle (∛2 est irrationnel)")
check(len(r["reelles_irrationnelles"]) == 1, "x³−2 : exactement 1 réelle irrationnelle")
check(r["nb_complexes_non_reelles"] == 2, "x³−2 : 2 racines complexes non réelles")
iv = r["reelles_irrationnelles"][0]
lo, hi = iv["intervalle"]
check(isinstance(lo, Fraction) and isinstance(hi, Fraction), "intervalle en Fractions (prouvé, exact)")
check(lo ** 3 <= 2 <= hi ** 3, "certificat EXACT lo³ ≤ 2 ≤ hi³ (second chemin, arithmétique Fraction)")
check(float(lo) <= CBRT2 <= float(hi), "l'intervalle contient 2**(1/3) calculé hors module")
check(hi - lo <= F(1, 10 ** 12), "largeur d'intervalle ≤ tol par défaut (10⁻¹²)")
check(abs(iv["approx"] - CBRT2) < 1e-9, "approx ≈ 1.2599210498948732 (∛2)")
check(iv["approche"] is True, "le flottant est MARQUÉ approché")
check(iv["multiplicite"] == 1, "∛2 : multiplicité 1")
check(r["exactitude_rationnelle_complete"] is True, "x³−2 : recherche rationnelle EXHAUSTIVE (petits coeffs)")
check(r["reelles_non_classees"] == [], "x³−2 : aucune racine non classée (irrationalité de ∛2 PROUVÉE)")

# ── 3) ANCRE : x³ − x = x(x−1)(x+1) -> 0, 1, −1 EXACTES ──
r = E.resout([1, 0, -1, 0])
check(rats(r) == {F(0): 1, F(1): 1, F(-1): 1}, "x³−x : racines exactes {0, 1, −1}")
check(r["nb_complexes_non_reelles"] == 0 and r["reelles_irrationnelles"] == [], "x³−x : tout rationnel")
check(sum(x for x, _ in r["rationnelles"]) == F(0), "Viète : Σ = 0 = −b/a (b = 0)")

# ── 4) ANCRE : x⁴ − 5x² + 4 = (x²−1)(x²−4) -> −2, −1, 1, 2 EXACTES ──
r = E.resout([1, 0, -5, 0, 4])
check(rats(r) == {F(-2): 1, F(-1): 1, F(1): 1, F(2): 1}, "x⁴−5x²+4 : racines exactes {−2,−1,1,2}")
check(r["nb_complexes_non_reelles"] == 0, "x⁴−5x²+4 : 0 complexe")
check(sum(x for x, _ in r["rationnelles"]) == F(0), "Viète : Σ = 0 = −b/a (b = 0)")
p = F(1)
for x, _ in r["rationnelles"]:
    p *= x
check(p == F(4), "Viète : Π = 4 = (−1)⁴·4/1")

# ── 5) ANCRE : x⁴ + 1 -> AUCUNE réelle (x⁴+1 ≥ 1 > 0), 4 complexes ──
r = E.resout([1, 0, 0, 0, 1])
check(r["rationnelles"] == [] and r["reelles_irrationnelles"] == [], "x⁴+1 : aucune racine réelle")
check(r["nb_complexes_non_reelles"] == 4, "x⁴+1 : 4 complexes non réelles")
check(r["nb_reelles"] == 0, "x⁴+1 : nb_reelles = 0")

# ── 6) MULTIPLICITÉS : (x−1)²(x−2) = x³−4x²+5x−2 et (x−1)⁴ = x⁴−4x³+6x²−4x+1 ──
r = E.resout([1, -4, 5, -2])
check(rats(r) == {F(1): 2, F(2): 1}, "(x−1)²(x−2) : multiplicités exactes {1:2, 2:1}")
r = E.resout([1, -4, 6, -4, 1])
check(rats(r) == {F(1): 4}, "(x−1)⁴ : racine 1 de multiplicité 4")
check(r["nb_reelles"] == 4, "(x−1)⁴ : 4 réelles avec multiplicité")
# (x²+1)² = x⁴+2x²+1 : 4 complexes avec multiplicité, 0 réelle
r = E.resout([1, 0, 2, 0, 1])
check(r["nb_complexes_non_reelles"] == 4 and r["nb_reelles"] == 0, "(x²+1)² : 4 complexes, 0 réelle")

# ── 7) DEGRÉS 1 et 2 ──
r = E.resout([2, -4])                                   # 2x − 4 = 0 -> x = 2 (à la main)
check(rats(r) == {F(2): 1} and r["degre"] == 1, "2x−4 : racine exacte 2")
r = E.resout([3, 1])                                    # 3x + 1 = 0 -> x = −1/3 (à la main)
check(rats(r) == {F(-1, 3): 1}, "3x+1 : racine exacte −1/3 (Fraction)")
r = E.resout([1, 0, -2])                                # x² − 2 -> ±√2
SQRT2 = math.sqrt(2)                                    # ≈ 1.4142135623730951, calcul EXTERNE au module
check(len(r["reelles_irrationnelles"]) == 2 and r["rationnelles"] == [], "x²−2 : 2 irrationnelles")
lo, hi = r["reelles_irrationnelles"][1]["intervalle"]   # la racine positive (triées par lo)
check(lo ** 2 <= 2 <= hi ** 2 and float(lo) <= SQRT2 <= float(hi), "√2 : certificat lo² ≤ 2 ≤ hi² + sqrt externe")
lo, hi = r["reelles_irrationnelles"][0]["intervalle"]   # la racine négative
check(float(lo) <= -SQRT2 <= float(hi), "−√2 dans le premier intervalle")
r = E.resout([1, 0, 1])                                 # x² + 1 : 0 réelle, 2 complexes
check(r["nb_reelles"] == 0 and r["nb_complexes_non_reelles"] == 2, "x²+1 : 0 réelle, 2 complexes")

# ── 8) DISCRIMINANT CUBIQUE — valeurs calculées À LA MAIN ──
# x³−6x²+11x−6 : a=1,b=−6,c=11,d=−6 -> 18·1·(−6)·11·(−6)=7128 ; −4b³d=−5184 ; b²c²=4356 ;
# −4ac³=−5324 ; −27a²d²=−972 ; total = 4. (Aussi a⁴Π(ri−rj)² = ((−1)(−2)(−1))² = 4.)
check(E.discriminant_cubique(1, -6, 11, -6) == F(4), "Δ(x³−6x²+11x−6) = 4 (calcul à la main)")
# x³−3x+1 : a=1,b=0,c=−3,d=1 -> −4·1·(−27) − 27 = 108 − 27 = 81
check(E.discriminant_cubique(1, 0, -3, 1) == F(81), "Δ(x³−3x+1) = 81 (calcul à la main)")
# x³−2 : a=1,b=c=0,d=−2 -> −27·4 = −108
check(E.discriminant_cubique(1, 0, 0, -2) == F(-108), "Δ(x³−2) = −108 (calcul à la main)")
# (x−1)²(x−2) = x³−4x²+5x−2 : 720 − 512 + 400 − 500 − 108 = 0 (racine double -> Δ = 0)
check(E.discriminant_cubique(1, -4, 5, -2) == F(0), "Δ((x−1)²(x−2)) = 0 (calcul à la main)")

# ── 9) Δ > 0 ⇔ 3 racines réelles distinctes (3 exemples POSITIFS + contre-exemples) ──
for a, b, c, d, nom in ((1, -6, 11, -6, "x³−6x²+11x−6"),
                        (1, 0, -3, 1, "x³−3x+1"),
                        (1, 0, -1, 0, "x³−x")):
    disc = E.discriminant_cubique(a, b, c, d)
    res = E.resout([a, b, c, d])
    distinctes = (all(m == 1 for _, m in res["rationnelles"])
                  and all(e["multiplicite"] == 1 for e in res["reelles_irrationnelles"])
                  and res["nb_reelles"] == 3)
    check(disc > 0 and distinctes, f"Δ > 0 et 3 réelles distinctes : {nom}")
# contre-exemples : Δ < 0 -> 1 réelle ; Δ = 0 -> racine multiple
check(E.discriminant_cubique(1, 0, 0, -2) < 0 and E.resout([1, 0, 0, -2])["nb_reelles"] == 1,
      "Δ < 0 ⇒ 1 seule réelle (x³−2)")
check(E.discriminant_cubique(1, -4, 5, -2) == 0 and rats(E.resout([1, -4, 5, -2]))[F(1)] == 2,
      "Δ = 0 ⇒ racine multiple ((x−1)²(x−2))")

# ── 10) CARDAN : résolution + nature croisée discriminant/Sturm ──
r = E.cardan(1, 0, -3, 1)
check(r["nature"] == E.NATURE_3_REELLES_DISTINCTES and r["discriminant"] == F(81),
      "cardan(x³−3x+1) : 3 réelles distinctes, Δ = 81")
check(len(r["reelles_irrationnelles"]) == 3, "x³−3x+1 : 3 intervalles réels prouvés")
# ancre externe : x³−3x+1 a pour racines 2cos(2π/9), 2cos(8π/9), 2cos(14π/9) (identité cos(3θ) classique)
attendues = sorted(2 * math.cos(2 * math.pi * k / 9) for k in (1, 4, 7))
for iv2, att in zip(r["reelles_irrationnelles"], attendues):
    lo2, hi2 = iv2["intervalle"]
    check(float(lo2) - 1e-12 <= att <= float(hi2) + 1e-12,
          f"x³−3x+1 : intervalle contient 2cos(...) ≈ {att:.6f} (trigonométrie, hors module)")
r = E.cardan(1, 0, 0, -2)
check(r["nature"] == E.NATURE_1_REELLE_2_COMPLEXES and r["discriminant"] == F(-108),
      "cardan(x³−2) : 1 réelle + 2 complexes, Δ = −108")
r = E.cardan(1, -4, 5, -2)
check(r["nature"] == E.NATURE_RACINE_MULTIPLE and r["discriminant"] == F(0),
      "cardan((x−1)²(x−2)) : racine multiple, Δ = 0")
r = E.cardan(1, -6, 11, -6)
check(r["nature"] == E.NATURE_3_REELLES_DISTINCTES and rats(r) == {F(1): 1, F(2): 1, F(3): 1},
      "cardan(x³−6x²+11x−6) : {1,2,3} et 3 réelles distinctes")

# ── 11) FERRARI : quartiques ──
r = E.ferrari(1, 0, -5, 0, 4)
check(rats(r) == {F(-2): 1, F(-1): 1, F(1): 1, F(2): 1}, "ferrari(x⁴−5x²+4) : {−2,−1,1,2}")
r = E.ferrari(1, 0, 0, 0, 1)
check(r["nb_complexes_non_reelles"] == 4 and r["nb_reelles"] == 0, "ferrari(x⁴+1) : 4 complexes")
r = E.ferrari(1, 0, 0, 0, -2)                           # x⁴ − 2 : ±2^(1/4) réelles + 2 complexes
QRT2 = 2 ** 0.25                                        # ≈ 1.189207115..., calcul EXTERNE au module
check(len(r["reelles_irrationnelles"]) == 2 and r["nb_complexes_non_reelles"] == 2,
      "x⁴−2 : 2 réelles irrationnelles + 2 complexes")
lo, hi = r["reelles_irrationnelles"][1]["intervalle"]
check(lo ** 4 <= 2 <= hi ** 4 and float(lo) <= QRT2 <= float(hi),
      "x⁴−2 : certificat exact lo⁴ ≤ 2 ≤ hi⁴ + 2**0.25 externe")

# ── 12) FRACTIONS en entrée : (x − 1/2)(x − 1/3) = x² − (5/6)x + 1/6 ──
r = E.resout([1, F(-5, 6), F(1, 6)])
check(rats(r) == {F(1, 3): 1, F(1, 2): 1}, "x²−(5/6)x+1/6 : racines exactes 1/2 et 1/3")

# ── 13) SOUNDNESS — degré > 4 (Abel–Ruffini) et degrés dégénérés ──
check(leve(E.resout, [1, 0, 0, 0, 0, -1]), "degré 5 -> ValueError (insoluble par radicaux en général)")
check(leve(E.resout, [1, 0, 0, 0, 0, 0, 1]), "degré 6 -> ValueError")
check(leve(E.resout, [0, 1, -2]), "coefficient dominant nul -> ValueError")
check(leve(E.resout, [0, 0, 1, -2]), "deux zéros de tête -> ValueError")
check(leve(E.resout, [5]), "degré 0 (constante) -> ValueError")
check(leve(E.resout, []), "liste vide -> ValueError")
check(leve(E.resout, "x^2-1"), "str au lieu d'une séquence -> ValueError")

# ── 14) SOUNDNESS — types de coefficients ──
check(leve(E.resout, [1.0, -2]), "float -> ValueError (0.1 n'est pas exact)")
check(leve(E.resout, [1, 0.5]), "float en coefficient -> ValueError")
check(leve(E.resout, [True, -2]), "bool -> ValueError (True n'est pas 1)")
check(leve(E.resout, [1, "2"]), "str -> ValueError")
check(leve(E.resout, [1, float("nan")]), "NaN -> ValueError")
check(leve(E.resout, [1, float("inf")]), "inf -> ValueError")
check(leve(E.resout, [1, 2 + 3j]), "complexe -> ValueError")
check(leve(E.discriminant_cubique, 0, 1, 1, 1), "discriminant a=0 -> ValueError")
check(leve(E.discriminant_cubique, 1.0, 1, 1, 1), "discriminant float -> ValueError")
check(leve(E.discriminant_cubique, True, 1, 1, 1), "discriminant bool -> ValueError")
check(leve(E.cardan, 0, 1, 1, 1), "cardan a=0 -> ValueError")
check(leve(E.cardan, 1, 0.5, 0, 0), "cardan float -> ValueError")
check(leve(E.ferrari, 0, 1, 1, 1, 1), "ferrari a=0 -> ValueError")
check(leve(E.ferrari, 1, 0, 0, 0, 1.5), "ferrari float -> ValueError")

# ── 15) SOUNDNESS — tol ──
check(leve(E.resout, [1, 0, -2], 0), "tol = 0 -> ValueError")
check(leve(E.resout, [1, 0, -2], F(-1, 10)), "tol < 0 -> ValueError")
check(leve(E.resout, [1, 0, -2], 1e-12), "tol flottant -> ValueError")
check(leve(E.resout, [1, 0, -2], True), "tol bool -> ValueError")

# ── 16) tol resserrée : l'intervalle rétrécit mais contient toujours ∛2 ──
r = E.resout([1, 0, 0, -2], F(1, 10 ** 20))
lo, hi = r["reelles_irrationnelles"][0]["intervalle"]
check(hi - lo <= F(1, 10 ** 20) and lo ** 3 <= 2 <= hi ** 3, "tol 10⁻²⁰ : intervalle prouvé plus fin")

# ── 16b) COEFFICIENTS GÉANTS (> 10¹²) : la recherche rationnelle renonce -> RIEN d'affirmé irrationnel ──
# ANCRE À LA MAIN : (x − 1)(x − N) avec N = 10¹³+7 se développe en x² − (N+1)x + N ; les deux racines
# 1 et N sont RATIONNELLES. Le cap _CAP_DIVISEURS = 10¹² (valeurs_propres) empêche de les trouver :
# l'unique réponse honnête est « réelles, rationalité indéterminée », jamais « irrationnelles ».
N = 10 ** 13 + 7
r = E.resout([1, -(N + 1), N])
check(r["exactitude_rationnelle_complete"] is False, "coeffs géants : exactitude_rationnelle_complete = False")
check(r["reelles_irrationnelles"] == [],
      "coeffs géants : AUCUNE entrée dans 'reelles_irrationnelles' (les racines 1 et N sont rationnelles)")
check(len(r["reelles_non_classees"]) == 2, "coeffs géants : 2 racines réelles non classées")
check(r["nb_reelles"] == 2 and r["nb_complexes_non_reelles"] == 0, "coeffs géants : 2 réelles, 0 complexe")
lo, hi = r["reelles_non_classees"][0]["intervalle"]
check(lo <= 1 <= hi, "coeffs géants : le 1er intervalle contient la racine 1 (Fraction, exact)")
check(isinstance(lo, Fraction) and isinstance(hi, Fraction), "coeffs géants : intervalle en Fractions")
lo, hi = r["reelles_non_classees"][1]["intervalle"]
check(lo <= F(N) <= hi, "coeffs géants : le 2e intervalle contient la racine 10¹³+7 (Fraction, exact)")
check(all(e["rationalite_indeterminee"] is True for e in r["reelles_non_classees"]),
      "coeffs géants : chaque entrée MARQUÉE 'rationalite_indeterminee'")
check(all(e["approche"] is True for e in r["reelles_non_classees"]),
      "coeffs géants : chaque flottant MARQUÉ approché")
check(all(e["multiplicite"] == 1 for e in r["reelles_non_classees"]), "coeffs géants : multiplicités 1")
check(r == E.resout([1, -(N + 1), N]), "déterminisme (coeffs géants)")
# cubique géante : (x−1)(x−2)(x−N) = x³ − (N+3)x² + (3N+2)x − 2N (développement à la main),
# 3 racines réelles distinctes -> Δ > 0, et le croisement discriminant/Sturm de cardan doit PASSER
# même quand les racines sont non classées (tol relâchée : la preuve d'isolation n'en dépend pas)
r = E.cardan(1, -(N + 3), 3 * N + 2, -2 * N, F(1, 10 ** 6))
check(r["nature"] == E.NATURE_3_REELLES_DISTINCTES,
      "cardan coeffs géants : nature '3 réelles distinctes' (Δ > 0 croisé Sturm, sans RuntimeError)")
check(r["discriminant"] > 0, "cardan coeffs géants : Δ > 0 (3 réelles distinctes, classification classique)")
check(r["reelles_irrationnelles"] == [] and len(r["reelles_non_classees"]) == 3,
      "cardan coeffs géants : 3 non classées, rien d'affirmé irrationnel (1, 2 et N sont rationnelles)")
check(r["exactitude_rationnelle_complete"] is False, "cardan coeffs géants : incomplétude déclarée")

# ── 17) DÉTERMINISME ──
check(E.resout([1, -6, 11, -6]) == E.resout([1, -6, 11, -6]), "déterminisme resout (rationnel)")
check(E.resout([1, 0, 0, -2]) == E.resout([1, 0, 0, -2]), "déterminisme resout (irrationnel)")
check(E.cardan(1, 0, -3, 1) == E.cardan(1, 0, -3, 1), "déterminisme cardan")
check(E.ferrari(1, 0, -5, 0, 4) == E.ferrari(1, 0, -5, 0, 4), "déterminisme ferrari")
check(E.discriminant_cubique(1, -6, 11, -6) == E.discriminant_cubique(1, -6, 11, -6),
      "déterminisme discriminant")

print(f"\n=== valide_equations_polynomiales : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
