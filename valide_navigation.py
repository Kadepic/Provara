"""VALIDE navigation.py — ADVERSE, FAUX=0. Orthodromie (haversine, R=6371) + cap initial.
Ancres CONNUES non circulaires : Paris→Londres ≈ 344 km (tol 2%), points identiques -> 0,
quart d'équateur (0,0)→(0,90) ≈ 10007 km, caps cardinaux 0/90/180/270 + SOUNDNESS bornes lat/lon."""
import math

import navigation as N

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, abs_tol):
    return abs(a - b) <= abs_tol


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── DISTANCE : ancres externes non circulaires ──
# Paris (48.85, 2.35) -> Londres (51.51, -0.13) : ~344 km (tol 2%)
d_pl = N.distance_orthodromique(48.85, 2.35, 51.51, -0.13)
check(abs(d_pl - 344.0) <= 0.02 * 344.0, f"Paris->Londres ~344 km (tol 2%), obtenu {d_pl}")
# haversine est un alias strict
check(N.haversine(48.85, 2.35, 51.51, -0.13) == d_pl, "haversine == distance_orthodromique (alias)")

# Deux points identiques -> distance 0
check(N.distance_orthodromique(48.85, 2.35, 48.85, 2.35) == 0.0, "points identiques -> 0")
check(N.distance_orthodromique(-33.45, 70.66, -33.45, 70.66) == 0.0, "points identiques (autre) -> 0")

# Quart de circonférence : équateur (0,0) -> (0,90) = π·R/2 ≈ 10007 km
quart = N.distance_orthodromique(0, 0, 0, 90)
check(proche(quart, math.pi * 6371 / 2, 0.1), f"quart équateur = π·R/2 ≈ 10007.54, obtenu {quart}")
check(abs(quart - 10007.0) < 1.0, f"quart équateur ≈ 10007 km, obtenu {quart}")

# Demi-équateur (0,0)->(0,180) = π·R ≈ 20015 km
demi = N.distance_orthodromique(0, 0, 0, 180)
check(proche(demi, math.pi * 6371, 0.1), f"demi équateur = π·R ≈ 20015, obtenu {demi}")
# 1° de méridien à l'équateur = π·R/180 ≈ 111.19 km
deg = N.distance_orthodromique(0, 0, 1, 0)
check(proche(deg, math.pi * 6371 / 180, 1e-3), f"1° méridien ≈ 111.19 km, obtenu {deg}")

# Symétrie : d(A,B) == d(B,A)
check(N.distance_orthodromique(48.85, 2.35, 51.51, -0.13)
      == N.distance_orthodromique(51.51, -0.13, 48.85, 2.35), "symétrie distance")

# ── CAP INITIAL : ancres cardinales depuis l'équateur ──
check(proche(N.cap_initial(0, 0, 0, 10), 90.0, 1e-6), "plein est -> cap 90°")
check(proche(N.cap_initial(0, 0, 10, 0), 0.0, 1e-6), "plein nord -> cap 0°")
check(proche(N.cap_initial(0, 0, 0, -10), 270.0, 1e-6), "plein ouest -> cap 270°")
check(proche(N.cap_initial(10, 0, 0, 0), 180.0, 1e-6), "plein sud -> cap 180°")
# Paris -> Londres : nord-ouest, ~330°
cap_pl = N.cap_initial(48.85, 2.35, 51.51, -0.13)
check(330.0 <= cap_pl <= 331.0, f"Paris->Londres cap ~330° (NO), obtenu {cap_pl}")
# Borne du domaine : cap dans [0, 360[
check(0.0 <= cap_pl < 360.0, "cap dans [0,360)")
check(0.0 <= N.cap_initial(0, 0, -10, 5) < 360.0, "cap dans [0,360) (sud-est)")

# ── DÉTERMINISME ──
check(N.distance_orthodromique(12.3, -45.6, -7.8, 99.1)
      == N.distance_orthodromique(12.3, -45.6, -7.8, 99.1), "déterminisme distance")
check(N.cap_initial(12.3, -45.6, -7.8, 99.1)
      == N.cap_initial(12.3, -45.6, -7.8, 99.1), "déterminisme cap")

# ── SOUNDNESS : bornes lat/lon + types ──
check(leve(N.distance_orthodromique, 91, 0, 0, 0), "lat1 > 90 -> ValueError")
check(leve(N.distance_orthodromique, -90.1, 0, 0, 0), "lat1 < -90 -> ValueError")
check(leve(N.distance_orthodromique, 0, 181, 0, 0), "lon1 > 180 -> ValueError")
check(leve(N.distance_orthodromique, 0, -181, 0, 0), "lon1 < -180 -> ValueError")
check(leve(N.distance_orthodromique, 0, 0, 95, 0), "lat2 > 90 -> ValueError")
check(leve(N.distance_orthodromique, 0, 0, 0, 200), "lon2 > 180 -> ValueError")
check(leve(N.cap_initial, 100, 0, 0, 0), "cap lat hors borne -> ValueError")
check(leve(N.cap_initial, 0, 0, 0, 999), "cap lon hors borne -> ValueError")
check(leve(N.distance_orthodromique, "a", 0, 0, 0), "lat non numérique -> ValueError")
check(leve(N.haversine, 0, None, 0, 0), "lon None -> ValueError")
check(leve(N.distance_orthodromique, True, 0, 0, 0), "bool refusé -> ValueError")
# bornes EXACTES acceptées (pôles / antiméridien) ne lèvent pas
check(isinstance(N.distance_orthodromique(90, 180, -90, -180), float), "bornes exactes acceptées")

print(f"\n=== valide_navigation : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
