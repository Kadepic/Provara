"""
VALIDE geometrie_hyperbolique.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN, PAS recalculées par la formule
testée) :
  • Courbure : K(R=1) = −1 ; K(R=2) = −0.25 (valeurs de référence, dual exact de la sphère K = +1/R²).
  • Triangle d'angles (π/4, π/4, π/4) sur R=1 : Σ = 3π/4 ; défaut δ = π − 3π/4 = π/4 ; aire = R²·δ = π/4
    ≈ 0.7853981634 — calcul À LA MAIN écrit en dur ici, indépendant du code testé.
  • Triangle idéal : quand les angles -> 0, l'aire -> π·R² (supremum). On vérifie que l'aire d'un triangle
    à angles minuscules approche π·R² PAR EN DESSOUS, et que aire_maximale(R) = π·R² (π en dur via math.pi).
  • Le triangle EUCLIDIEN (Σ = π exactement, ex. π/3,π/3,π/3) est REFUSÉ ; le cas SPHÉRIQUE (Σ > π,
    ex. π/2,π/2,π/2) est REFUSÉ.
  • Poincaré : d((0,0),(0.5,0)) = arcosh(1 + 2·0.25/(1·0.75)) = arcosh(5/3) = ln(3) — ANCRE EXACTE
    remarquable : arcosh(5/3) = ln(5/3 + √(25/9 − 1)) = ln(5/3 + 4/3) = ln(3), vérifiée contre math.log(3)
    (SECOND chemin de code, distinct de math.acosh/asinh). d(0,0) = 0 ; symétrie d(u,v) = d(v,u) ; le bord
    |u| = 1 est hors modèle -> ValueError.
  • STABILITÉ (fix cancellation arcosh(1+2t) -> 2·arsinh(√t)) — ancres calculées INDÉPENDAMMENT en
    Decimal 60 chiffres (module decimal, hors du code testé) sur les MÊMES flottants d'entrée :
      d((0,0),(1e-9,0))  = 2.0000000000000001e-9  (≈ 2·arsinh(1e-9), série arsinh x = x − x³/6) ;
      d((0,0),(1e-8,0))  = 2.0000000000000001e-8 ;
      d((0.1,0.1),(0.1,0.1000001)) = 2.0408163471307407e-7 ;
      d((0,0),(1e-200,0)) = 2e-200 (arsinh x = x au grain flottant ; le carré ne doit PAS être formé).
    SECOND chemin de code radial : d((0,0),(r,0)) = 2·artanh(r) = ln((1+r)/(1−r)) — vérifié via
    math.atanh (fonction distincte de asinh/acosh) en r = 0.5, 0.999 et 0.99999999 (près du bord).
    Et la garantie métrique : d(u,v) > 0 pour u ≠ v, y compris à séparation 1e-9 (le zéro faux est mort).
  • coherence_relative() : FAIT sourcé Beltrami 1868 / Klein / Poincaré (mots-clés exigés en dur).

SOUNDNESS : R≤0, angle hors ]0,π[, Σ ≥ π, point hors disque ouvert, mauvaise arité,
types (bool/str/NaN/inf) -> ValueError. DÉTERMINISME : deux appels, égalité exigée.
"""
import math

import geometrie_hyperbolique as H

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

# ── 1) COURBURE K = −1/R² (ancres de référence en dur) ──
check(proche(H.courbure_gauss_hyperbolique(1.0), -1.0), "K(R=1) = −1")
check(proche(H.courbure_gauss_hyperbolique(2.0), -0.25), "K(R=2) = −0.25")
check(proche(H.courbure_gauss_hyperbolique(0.5), -4.0), "K(R=0.5) = −4")
check(H.courbure_gauss_hyperbolique(3.0) < 0, "K toujours strictement négative")

# ── 2) ANCRE À LA MAIN : triangle (π/4, π/4, π/4) sur R=1 ──
# Σ = 3π/4 ; δ = π − 3π/4 = π/4 = 0.7853981633974483… (calculé à la main, en dur)
check(proche(H.defaut_angulaire(PI / 4, PI / 4, PI / 4), 0.7853981634, tol=1e-9),
      "défaut (π/4,π/4,π/4) = π/4 ≈ 0.7853981634 (à la main)")
check(proche(H.aire_triangle_hyperbolique((PI / 4, PI / 4, PI / 4), 1.0), 0.7853981634, tol=1e-9),
      "aire (π/4,π/4,π/4 ; R=1) = π/4 ≈ 0.7853981634 (à la main)")
# Sur R=2, l'aire est multipliée par R²=4 : aire = 4·π/4 = π (échelle de Gauss-Bonnet)
check(proche(H.aire_triangle_hyperbolique((PI / 4, PI / 4, PI / 4), 2.0), PI, tol=1e-8),
      "aire (π/4,π/4,π/4 ; R=2) = π (échelle R²)")
# Cohérence aire = R²·défaut via deux fonctions DISTINCTES du module (double chemin)
check(proche(H.aire_triangle_hyperbolique((0.3, 0.4, 0.5), 1.0),
             H.defaut_angulaire(0.3, 0.4, 0.5), tol=1e-9),
      "aire (R=1) = défaut angulaire (cohérence Gauss-Bonnet)")

# ── 3) SOMME DES ANGLES : toujours < π ──
s, inf_pi = H.somme_angles_triangle_hyperbolique(PI / 4, PI / 4, PI / 4)
check(proche(s, 3.0 * PI / 4, tol=1e-9), "somme (π/4,π/4,π/4) = 3π/4")
check(inf_pi is True, "somme < π signalée (vrai)")
s2, inf2 = H.somme_angles_triangle_hyperbolique(0.1, 0.2, 0.3)
check(proche(s2, 0.6, tol=1e-9) and inf2 is True, "somme (0.1,0.2,0.3) = 0.6 < π")

# ── 4) TRIANGLE IDÉAL : aire -> π·R² (supremum, approché PAR EN DESSOUS) ──
check(proche(H.aire_maximale(1.0), PI, tol=1e-9), "aire maximale (R=1) = π (triangle idéal)")
check(proche(H.aire_maximale(2.0), 4.0 * PI, tol=1e-8), "aire maximale (R=2) = 4π")
aire_quasi_ideale = H.aire_triangle_hyperbolique((1e-9, 1e-9, 1e-9), 1.0)
check(proche(aire_quasi_ideale, PI, tol=1e-7), "angles -> 0 : aire -> π·R² (R=1)")
check(aire_quasi_ideale < PI, "aire d'un vrai triangle STRICTEMENT < π·R² (supremum non atteint)")
check(H.aire_triangle_hyperbolique((0.5, 0.5, 0.5), 1.0) < H.aire_maximale(1.0),
      "toute aire < aire maximale")

# ── 5) EUCLIDIEN ET SPHÉRIQUE REFUSÉS (signature de la courbure négative) ──
check(leve(H.somme_angles_triangle_hyperbolique, PI / 3, PI / 3, PI / 3),
      "Σ = π (euclidien π/3×3) -> ValueError")
check(leve(H.somme_angles_triangle_hyperbolique, PI / 2, PI / 2, PI / 2),
      "Σ > π (sphérique π/2×3) -> ValueError")
check(leve(H.defaut_angulaire, PI / 3, PI / 3, PI / 3), "défaut : Σ = π -> ValueError")
check(leve(H.defaut_angulaire, PI / 2, PI / 2, PI / 2), "défaut : Σ > π -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (PI / 3, PI / 3, PI / 3), 1.0), "aire : Σ = π -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (PI / 2, PI / 2, PI / 2), 1.0), "aire : Σ > π -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (1.2, 1.2, 1.2), 1.0), "aire : Σ = 3.6 > π -> ValueError")

# ── 6) DISQUE DE POINCARÉ : ancre exacte arcosh(5/3) = ln(3) ──
# À la main : |u−v|² = 0.25 ; (1−|u|²)(1−|v|²) = 1·0.75 ; argument = 1 + 0.5/0.75 = 5/3 ;
# arcosh(5/3) = ln(5/3 + 4/3) = ln 3. Vérifié contre math.log(3) — SECOND chemin, pas math.acosh.
check(proche(H.distance_poincare((0.0, 0.0), (0.5, 0.0)), math.log(3.0), tol=1e-9),
      "d((0,0),(0.5,0)) = ln(3) ≈ 1.0986122887")
check(proche(H.distance_poincare((0.0, 0.0), (0.5, 0.0)), 1.0986122887, tol=1e-9),
      "d((0,0),(0.5,0)) ≈ 1.0986122887 (valeur en dur)")
check(H.distance_poincare((0.0, 0.0), (0.0, 0.0)) == 0.0, "d(0,0) = 0")
check(H.distance_poincare((0.3, 0.1), (0.3, 0.1)) == 0.0, "d(u,u) = 0")
check(H.distance_poincare((0.2, 0.3), (-0.4, 0.1))
      == H.distance_poincare((-0.4, 0.1), (0.2, 0.3)), "symétrie d(u,v) = d(v,u)")
# Rotation de l'ancre : d((0,0),(0,0.5)) = même distance (isotropie autour de l'origine)
check(proche(H.distance_poincare((0.0, 0.0), (0.0, 0.5)), math.log(3.0), tol=1e-9),
      "d((0,0),(0,0.5)) = ln(3) (isotropie)")
check(H.distance_poincare((0.0, 0.0), (0.9, 0.0))
      > H.distance_poincare((0.0, 0.0), (0.5, 0.0)),
      "la distance explose vers le bord (0.9 plus loin que 0.5)")
check(H.distance_poincare((0.1, 0.2), (0.3, -0.1)) > 0.0, "d(u,v) > 0 pour u ≠ v")

# ── 6bis) STABILITÉ AUX PETITES SÉPARATIONS (fix : identité arcosh(1+2t) = 2·arsinh(√t)) ──
# Ancres calculées INDÉPENDAMMENT en Decimal (60 chiffres) sur les mêmes flottants d'entrée,
# via 2·ln(√t + √(t+1)) hors du code testé. Le flottant 1e-9 vaut exactement
# 1.0000000000000000622…e-9, d'où l'attendu 2.0000000000000001e-9 (et non 2e-9 pile).
d_1e9 = H.distance_poincare((0.0, 0.0), (1e-9, 0.0))
check(d_1e9 > 0.0, "d((0,0),(1e-9,0)) > 0 : le zéro faux (cancellation) est mort")
check(proche(d_1e9, 2.0000000000000001e-9, tol=1e-18),
      "d((0,0),(1e-9,0)) = 2.0000000000000001e-9 (Decimal 60 chiffres, en dur)")
check(proche(H.distance_poincare((0.0, 0.0), (1e-8, 0.0)), 2.0000000000000001e-8, tol=1e-17),
      "d((0,0),(1e-8,0)) = 2.0000000000000001e-8 (Decimal 60 chiffres, en dur)")
# 10 chiffres significatifs TENUS sur points proches non triviaux (l'audit mesurait 2.043…e-7, faux) :
check(proche(H.distance_poincare((0.1, 0.1), (0.1, 0.1000001)), 2.0408163471e-7, tol=1e-16),
      "d((0.1,0.1),(0.1,0.1000001)) = 2.0408163471e-7 (Decimal : 2.0408163471307407e-7)")
# Séparation subnormale-adjacente : le carré 1e-400 sous-passerait ; hypot + arsinh x = x le tiennent.
check(H.distance_poincare((0.0, 0.0), (1e-200, 0.0)) == 2e-200,
      "d((0,0),(1e-200,0)) = 2e-200 (le carré n'est jamais formé)")
# SECOND chemin radial : d((0,0),(r,0)) = 2·artanh(r) — math.atanh, fonction distincte de asinh.
check(proche(H.distance_poincare((0.0, 0.0), (0.5, 0.0)), 2.0 * math.atanh(0.5), tol=1e-9),
      "d((0,0),(0.5,0)) = 2·artanh(0.5) (second chemin radial)")
check(proche(H.distance_poincare((0.0, 0.0), (0.999, 0.0)), 2.0 * math.atanh(0.999), tol=1e-8),
      "d((0,0),(0.999,0)) = 2·artanh(0.999) ≈ 7.600402335")
check(proche(H.distance_poincare((0.0, 0.0), (0.999, 0.0)), 7.600402335, tol=1e-8),
      "d((0,0),(0.999,0)) = 7.600402335 (Decimal : 7.60040233450039917…, en dur)")
# Près du bord (1−|v|² = 2e-8 : la cancellation du dénominateur est tuée par Fraction) :
check(proche(H.distance_poincare((0.0, 0.0), (0.99999999, 0.0)), 2.0 * math.atanh(0.99999999), tol=1e-7),
      "d((0,0),(0.99999999,0)) = 2·artanh(0.99999999) (près du bord)")
check(proche(H.distance_poincare((0.0, 0.0), (0.99999999, 0.0)), 19.11382791, tol=1e-7),
      "d((0,0),(0.99999999,0)) = 19.11382791 (Decimal : 19.113827914487551…, en dur)")
# Symétrie et déterminisme tiennent aussi dans le régime des petites séparations :
check(H.distance_poincare((0.1, 0.1), (0.1, 0.1000001))
      == H.distance_poincare((0.1, 0.1000001), (0.1, 0.1)), "symétrie aux petites séparations")
check(d_1e9 == H.distance_poincare((0.0, 0.0), (1e-9, 0.0)), "déterminisme aux petites séparations")

# ── 7) SOUNDNESS — Poincaré : hors du disque OUVERT ──
check(leve(H.distance_poincare, (1.0, 0.0), (0.0, 0.0)), "bord |u| = 1 -> ValueError")
check(leve(H.distance_poincare, (0.0, 0.0), (0.0, 1.0)), "bord |v| = 1 -> ValueError")
check(leve(H.distance_poincare, (1.5, 0.0), (0.0, 0.0)), "|u| > 1 -> ValueError")
check(leve(H.distance_poincare, (0.8, 0.8), (0.0, 0.0)), "x²+y² = 1.28 > 1 -> ValueError")
check(leve(H.distance_poincare, (0.0,), (0.0, 0.0)), "point à 1 coordonnée -> ValueError")
check(leve(H.distance_poincare, (0.0, 0.0, 0.0), (0.0, 0.0)), "point à 3 coordonnées -> ValueError")
check(leve(H.distance_poincare, 0.5, (0.0, 0.0)), "point non-couple -> ValueError")
check(leve(H.distance_poincare, (float("nan"), 0.0), (0.0, 0.0)), "coordonnée NaN -> ValueError")
check(leve(H.distance_poincare, (float("inf"), 0.0), (0.0, 0.0)), "coordonnée inf -> ValueError")
check(leve(H.distance_poincare, (True, 0.0), (0.0, 0.0)), "coordonnée bool -> ValueError")
check(leve(H.distance_poincare, ("0.5", 0.0), (0.0, 0.0)), "coordonnée str -> ValueError")

# ── 8) SOUNDNESS — rayon ──
check(leve(H.courbure_gauss_hyperbolique, 0.0), "K : R = 0 -> ValueError")
check(leve(H.courbure_gauss_hyperbolique, -1.0), "K : R < 0 -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (PI / 4, PI / 4, PI / 4), 0.0), "aire : R = 0 -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (PI / 4, PI / 4, PI / 4), -2.0), "aire : R < 0 -> ValueError")
check(leve(H.aire_maximale, 0.0), "aire max : R = 0 -> ValueError")
check(leve(H.aire_maximale, -1.0), "aire max : R < 0 -> ValueError")

# ── 9) SOUNDNESS — angles hors ]0, π[ ──
check(leve(H.somme_angles_triangle_hyperbolique, 0.0, 0.5, 0.5), "angle = 0 -> ValueError")
check(leve(H.somme_angles_triangle_hyperbolique, -0.1, 0.5, 0.5), "angle < 0 -> ValueError")
check(leve(H.somme_angles_triangle_hyperbolique, PI, 0.1, 0.1), "angle = π -> ValueError")
check(leve(H.defaut_angulaire, 4.0, 0.1, 0.1), "défaut : angle > π -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (0.0, 0.5, 0.5), 1.0), "aire : angle = 0 -> ValueError")

# ── 10) SOUNDNESS — arité / structure des angles ──
check(leve(H.aire_triangle_hyperbolique, (0.5, 0.5), 1.0), "2 angles -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (0.5, 0.5, 0.5, 0.5), 1.0), "4 angles -> ValueError")
check(leve(H.aire_triangle_hyperbolique, 0.5, 1.0), "angles non-séquence -> ValueError")

# ── 11) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(H.courbure_gauss_hyperbolique, True), "K : bool -> ValueError")
check(leve(H.courbure_gauss_hyperbolique, "1"), "K : str -> ValueError")
check(leve(H.courbure_gauss_hyperbolique, float("nan")), "K : NaN -> ValueError")
check(leve(H.courbure_gauss_hyperbolique, float("inf")), "K : inf -> ValueError")
check(leve(H.defaut_angulaire, True, 0.5, 0.5), "défaut : bool -> ValueError")
check(leve(H.defaut_angulaire, float("nan"), 0.5, 0.5), "défaut : NaN -> ValueError")
check(leve(H.somme_angles_triangle_hyperbolique, "0.5", 0.5, 0.5), "somme : str -> ValueError")
check(leve(H.aire_triangle_hyperbolique, (0.5, 0.5, float("inf")), 1.0), "aire : angle inf -> ValueError")
check(leve(H.aire_maximale, True), "aire max : bool -> ValueError")

# ── 12) COHÉRENCE RELATIVE : FAIT sourcé (Beltrami 1868, Klein, Poincaré) ──
enonce = H.coherence_relative()
check(isinstance(enonce, str) and len(enonce) > 100, "coherence_relative() renvoie un énoncé substantiel")
check("Beltrami" in enonce and "1868" in enonce, "énoncé sourcé : Beltrami 1868")
check("Klein" in enonce and "Poincaré" in enonce, "énoncé sourcé : Klein + Poincaré")
check("cohérente si et seulement si" in enonce, "équivalence de cohérence énoncée (ssi)")
check("MODÈLE" in enonce, "le disque de Poincaré est un MODÈLE (mécanisme de la preuve)")
check("INDÉPENDANT" in enonce and "parallèles" in enonce,
      "corollaire : indépendance du postulat des parallèles")

# ── 13) DÉTERMINISME ──
check(H.aire_triangle_hyperbolique((PI / 4, PI / 4, PI / 4), 1.0)
      == H.aire_triangle_hyperbolique((PI / 4, PI / 4, PI / 4), 1.0), "déterminisme aire")
check(H.distance_poincare((0.2, 0.3), (-0.4, 0.1))
      == H.distance_poincare((0.2, 0.3), (-0.4, 0.1)), "déterminisme distance")
check(H.somme_angles_triangle_hyperbolique(0.1, 0.2, 0.3)
      == H.somme_angles_triangle_hyperbolique(0.1, 0.2, 0.3), "déterminisme somme")
check(H.coherence_relative() == H.coherence_relative(), "déterminisme énoncé")

print(f"\n=== valide_geometrie_hyperbolique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
