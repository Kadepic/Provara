"""
VALIDE geometries_non_euclidiennes.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par la formule testée) :
  • Triangle TRIRECTANGLE (3 angles droits) sur la sphère unité = un OCTANT de sphère. La sphère a une aire
    totale 4πR² ; un octant en vaut 1/8, soit 4π/8 = π/2 pour R=1. On confronte aire_triangle_spherique à
    cette aire-octant calculée INDÉPENDAMMENT (théorie de la sphère, pas Girard) -> validation non circulaire.
  • Courbure de Gauss de la sphère unité = 1 (valeur de référence) ; d'une sphère R=2 -> 1/4 ; Terre R≈6371 km
    -> 1/R² (ordre de grandeur connu).
  • Somme des angles du trirectangle = 3·(π/2) = 3π/2 (> π : signature de la courbure positive).

SOUNDNESS : R≤0, aire≤0, angle hors ]0,π[, somme ≤ π, mauvaise arité, types (bool/str/NaN/inf) -> ValueError.
"""
import math

import geometries_non_euclidiennes as G

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


PI = math.pi

# ── 1) ANCRE EXTERNE : trirectangle = octant de sphère, aire = (1/8)·4πR² ──
for R in (1.0, 2.0, 6.371e6):
    aire_octant = (4.0 * PI * R * R) / 8.0          # aire d'1/8 de sphère — INDÉPENDANT de Girard
    aire_girard = G.aire_triangle_spherique((PI / 2, PI / 2, PI / 2), R)
    check(proche(aire_girard, aire_octant, tol=1e-3 * aire_octant + 1e-9),
          f"trirectangle = octant : Girard {aire_girard} ≈ octant {aire_octant} (R={R})")

# Cas exact R=1 : aire = π/2
check(proche(G.aire_triangle_spherique((PI / 2, PI / 2, PI / 2), 1.0), PI / 2),
      "aire trirectangle (R=1) = π/2")

# ── 2) EXCÈS SPHÉRIQUE = aire/R² = Σangles − π ──
check(proche(G.exces_spherique(PI / 2, 1.0), PI / 2), "excès octant (R=1) = π/2")
check(proche(G.exces_spherique(PI, 1.0), PI), "excès aire=π,R=1 = π")
# excès = aire/R² : aire=π/2, R=2 -> (π/2)/4 = π/8
check(proche(G.exces_spherique(PI / 2, 2.0), PI / 8), "excès aire=π/2,R=2 = π/8")
# cohérence excès <-> somme angles : excès du trirectangle = somme − π
somme_tri, sup = G.somme_angles_triangle_spherique(PI / 2, PI / 2, PI / 2)
check(proche(somme_tri, 3.0 * PI / 2), "somme angles trirectangle = 3π/2")
check(sup is True, "somme > π signalée (vrai)")
check(proche(G.exces_spherique(PI / 2, 1.0), somme_tri - PI),
      "excès (octant) = somme angles − π (cohérence Girard)")

# ── 3) COURBURE DE GAUSS K = 1/R² ──
check(proche(G.courbure_gauss_sphere(1.0), 1.0), "K sphère unité = 1")
check(proche(G.courbure_gauss_sphere(2.0), 0.25), "K sphère R=2 = 1/4")
check(proche(G.courbure_gauss_sphere(0.5), 4.0), "K sphère R=0.5 = 4")
check(proche(G.courbure_gauss_sphere(6.371e6), 1.0 / (6.371e6 ** 2), tol=1e-20),
      "K Terre ≈ 1/R² (R≈6371 km)")

# ── 4) ÉCART À L'EUCLIDE : somme > π pour tout triangle sphérique valide ──
s2, sup2 = G.somme_angles_triangle_spherique(1.2, 1.2, 1.2)   # 3.6 rad > π
check(s2 > PI and sup2 is True, "triangle sphérique générique : somme > π")

# ── 5) SOUNDNESS — rayon ──
check(leve(G.courbure_gauss_sphere, 0.0), "R=0 -> ValueError")
check(leve(G.courbure_gauss_sphere, -1.0), "R<0 -> ValueError")
check(leve(G.exces_spherique, 1.0, 0.0), "exces R=0 -> ValueError")
check(leve(G.aire_triangle_spherique, (PI / 2, PI / 2, PI / 2), -1.0), "aire R<0 -> ValueError")

# ── 6) SOUNDNESS — aire / triangle dégénéré (somme ≤ π) ──
check(leve(G.exces_spherique, 0.0, 1.0), "aire=0 -> ValueError")
check(leve(G.exces_spherique, -2.0, 1.0), "aire<0 -> ValueError")
check(leve(G.somme_angles_triangle_spherique, PI / 3, PI / 3, PI / 3), "somme=π (euclidien) -> ValueError")
check(leve(G.somme_angles_triangle_spherique, 0.5, 0.5, 0.5), "somme<π -> ValueError")
check(leve(G.aire_triangle_spherique, (0.5, 0.5, 0.5), 1.0), "aire somme<π -> ValueError")

# ── 7) SOUNDNESS — angles hors ]0, π[ ──
check(leve(G.somme_angles_triangle_spherique, PI, PI / 2, PI / 2), "angle=π -> ValueError")
check(leve(G.somme_angles_triangle_spherique, 0.0, PI / 2, PI / 2), "angle=0 -> ValueError")
check(leve(G.somme_angles_triangle_spherique, -0.1, PI / 2, PI / 2), "angle<0 -> ValueError")
check(leve(G.aire_triangle_spherique, (4.0, PI / 2, PI / 2), 1.0), "angle>π -> ValueError")

# ── 8) SOUNDNESS — excès trop grand (≥ 2π, Σ ≥ 3π impossible pour un triangle) ──
check(leve(G.exces_spherique, 7.0, 1.0), "excès ≥ 2π (aire=7,R=1) -> ValueError")

# ── 9) SOUNDNESS — arité / structure des angles ──
check(leve(G.aire_triangle_spherique, (PI / 2, PI / 2), 1.0), "2 angles -> ValueError")
check(leve(G.aire_triangle_spherique, (PI / 2, PI / 2, PI / 2, PI / 2), 1.0), "4 angles -> ValueError")
check(leve(G.aire_triangle_spherique, PI / 2, 1.0), "angles non-séquence -> ValueError")

# ── 10) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(G.courbure_gauss_sphere, True), "bool -> ValueError")
check(leve(G.courbure_gauss_sphere, "1"), "str -> ValueError")
check(leve(G.courbure_gauss_sphere, float("nan")), "NaN -> ValueError")
check(leve(G.courbure_gauss_sphere, float("inf")), "inf -> ValueError")
check(leve(G.exces_spherique, float("inf"), 1.0), "aire=inf -> ValueError")
check(leve(G.somme_angles_triangle_spherique, True, PI / 2, PI / 2), "angle bool -> ValueError")

# ── 11) DÉTERMINISME ──
check(G.aire_triangle_spherique((PI / 2, PI / 2, PI / 2), 1.0)
      == G.aire_triangle_spherique((PI / 2, PI / 2, PI / 2), 1.0), "déterminisme aire")
check(G.somme_angles_triangle_spherique(PI / 2, PI / 2, PI / 2)
      == G.somme_angles_triangle_spherique(PI / 2, PI / 2, PI / 2), "déterminisme somme")

print(f"\n=== valide_geometries_non_euclidiennes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
