"""
VALIDE teledetection.py — held-out ADVERSE.

Ancres CONNUES (valeurs de télédétection de référence, PAS recalculées par la même
expression triviale au moment du check — calculées à la main ci-dessous) :
  • GSD : fauchée 60 000 m / 6 000 px = 10 m/px  (cas canonique du module).
  • GSD : fauchée 11 540 m / 5 770 px = 2 m/px.
  • NDVI(0.5, 0.1) = 0.4/0.6 ≈ 0.666667 (végétation dense).
  • NDVI sol nu (NIR ≈ R) ≈ 0 ; eau/nuage (NIR < R) < 0 ; NDVI ∈ [−1, 1].
  • Revisite Sentinel-2 : 10 j (1 sat) / 2 sat = 5 j ; Landsat 16 j / 1 sat = 16 j.
SOUNDNESS : fauchée<=0, pixels<=0, NIR+R==0, NIR<0, R<0, période<=0, nb_sat<=0,
            entrée non numérique/non finie -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import teledetection as T

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — résolution spatiale (GSD = fauchée / pixels) ──
check(approx(T.resolution_spatiale(60000, 6000), 10.0), "GSD 60000/6000 = 10 m/px")
check(approx(T.resolution_spatiale(11540, 5770), 2.0), "GSD 11540/5770 = 2 m/px")
check(approx(T.resolution_spatiale(30000, 3000), 10.0), "GSD 30000/3000 = 10 m/px")
# Monotonie : plus de pixels -> pixel plus fin (GSD plus petit).
check(T.resolution_spatiale(60000, 12000) < T.resolution_spatiale(60000, 6000),
      "doubler les pixels divise le GSD par 2")
check(approx(T.resolution_spatiale(60000, 12000), 5.0), "GSD 60000/12000 = 5 m/px")
# Échelle : doubler la fauchée double le GSD à pixels constants.
check(approx(T.resolution_spatiale(120000, 6000), 20.0), "GSD 120000/6000 = 20 m/px")

# ── 2) ANCRES — NDVI ──
check(approx(T.ndvi(0.5, 0.1), 0.666667), "NDVI(0.5,0.1) ≈ 0.666667 (végét. dense)")
check(approx(T.ndvi(0.2, 0.2), 0.0), "NDVI sol nu (NIR≈R) ≈ 0")
check(approx(T.ndvi(0.1, 0.4), -0.6), "NDVI eau/nuage (NIR<R) = -0.6")
check(approx(T.ndvi(1.0, 0.0), 1.0), "NDVI(1,0) = +1 (borne haute)")
check(approx(T.ndvi(0.0, 1.0), -1.0), "NDVI(0,1) = -1 (borne basse)")
# Antisymétrie : NDVI(a,b) = -NDVI(b,a).
check(approx(T.ndvi(0.5, 0.1), -T.ndvi(0.1, 0.5)), "NDVI antisymétrique")
# Invariant de borne sur de nombreux couples non-négatifs.
borne_ok = True
for nir in (0.0, 0.05, 0.2, 0.7, 1.0, 3.5):
    for r in (0.0, 0.05, 0.2, 0.7, 1.0, 3.5):
        if nir + r == 0.0:
            continue
        v = T.ndvi(nir, r)
        if v < -1.0 - 1e-12 or v > 1.0 + 1e-12:
            borne_ok = False
check(borne_ok, "NDVI ∈ [-1, 1] pour toutes réflectances >= 0")
# Croissance : à rouge fixé, NIR plus fort -> NDVI plus grand.
check(T.ndvi(0.6, 0.1) > T.ndvi(0.3, 0.1), "NDVI croît avec NIR (rouge fixé)")

# ── 3) ANCRES — résolution temporelle (revisite / nb satellites) ──
check(approx(T.resolution_temporelle(10, 2), 5.0), "Sentinel-2 : 10 j / 2 sat = 5 j")
check(approx(T.resolution_temporelle(16, 1), 16.0), "Landsat : 16 j / 1 sat = 16 j")
check(approx(T.resolution_temporelle(16, 4), 4.0), "16 j / 4 sat = 4 j")
check(T.resolution_temporelle(16, 4) < T.resolution_temporelle(16, 2),
      "plus de satellites -> revisite plus courte")

# ── 4) SOUNDNESS — abstention (ValueError) plutôt qu'un faux ──
check(_leve_v(T.resolution_spatiale, 60000, 0), "pixels=0 -> ValueError")
check(_leve_v(T.resolution_spatiale, 60000, -10), "pixels<0 -> ValueError")
check(_leve_v(T.resolution_spatiale, 0, 6000), "fauchée=0 -> ValueError")
check(_leve_v(T.resolution_spatiale, -5, 6000), "fauchée<0 -> ValueError")
check(_leve_v(T.resolution_spatiale, "abc", 6000), "fauchée non num -> ValueError")
check(_leve_v(T.resolution_spatiale, float("inf"), 6000), "fauchée inf -> ValueError")
check(_leve_v(T.ndvi, 0.0, 0.0), "NIR+R==0 -> ValueError")
check(_leve_v(T.ndvi, -0.1, 0.2), "NIR<0 -> ValueError")
check(_leve_v(T.ndvi, 0.2, -0.1), "R<0 -> ValueError")
check(_leve_v(T.ndvi, float("nan"), 0.2), "NIR nan -> ValueError")
check(_leve_v(T.resolution_temporelle, 10, 0), "nb_sat=0 -> ValueError")
check(_leve_v(T.resolution_temporelle, 10, -2), "nb_sat<0 -> ValueError")
check(_leve_v(T.resolution_temporelle, 0, 2), "période=0 -> ValueError")
check(_leve_v(T.resolution_temporelle, -3, 2), "période<0 -> ValueError")

# ── 5) DÉTERMINISME ──
check(T.resolution_spatiale(60000, 6000) == T.resolution_spatiale(60000, 6000),
      "resolution_spatiale déterministe")
check(T.ndvi(0.5, 0.1) == T.ndvi(0.5, 0.1), "ndvi déterministe")
check(T.resolution_temporelle(10, 2) == T.resolution_temporelle(10, 2),
      "resolution_temporelle déterministe")

print(f"\n=== valide_teledetection : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
