"""VALIDE robotique.py — ADVERSE, FAUX=0. Positions d'effecteur CONNUES (configurations géométriques simples),
portée min/max, atteignabilité + SOUNDNESS (longueur ≤ 0 -> ValueError)."""
import robotique as R

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def pos(a, b, t=1e-4):     # tolérance cohérente avec l'arrondi à 6 chiffres significatifs du module
    return abs(a[0] - b[0]) <= t and abs(a[1] - b[1]) <= t


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# CINÉMATIQUE DIRECTE — positions connues
check(pos(R.cinematique_directe_2r(1, 1, 0, 0), (2.0, 0.0)), "bras tendu horizontal -> (2,0)")
check(pos(R.cinematique_directe_2r(1, 1, 90, 0), (0.0, 2.0)), "bras tendu vertical -> (0,2)")
check(pos(R.cinematique_directe_2r(1, 1, 0, 90), (1.0, 1.0)), "coude à 90° -> (1,1)")
check(pos(R.cinematique_directe_2r(2, 1, 90, -90), (1.0, 2.0)), "config (2,1,90,-90) -> (1,2)")
check(pos(R.cinematique_directe_2r(1, 1, 0, 180), (0.0, 0.0)), "replié sur la base -> (0,0)")
check(pos(R.cinematique_directe_2r(3, 0.0001 if False else 1, 0, 0), (4.0, 0.0)), "tendu (3,1) -> (4,0)")
import math
check(pos(R.cinematique_directe_2r(1, 1, 45, 45),
          (math.cos(math.radians(45)), math.sin(math.radians(45)) + 1)), "config 45/45")

# PORTÉE / ATTEIGNABILITÉ
check(R.portee_max(3, 1) == 4.0 and R.portee_min(3, 1) == 2.0, "portée [2,4] pour (3,1)")
check(R.portee_min(2, 2) == 0.0, "bras égaux -> portée min 0")
check(R.atteignable(2, 1, 2.5, 0) is True, "(2.5,0) atteignable")
check(R.atteignable(2, 1, 0.5, 0) is False, "(0.5,0) sous la portée min -> non")
check(R.atteignable(2, 1, 3.5, 0) is False, "(3.5,0) au-delà de la portée -> non")
check(R.atteignable(2, 1, 3, 0) is True, "(3,0) = portée max -> atteignable")

# SOUNDNESS
check(leve(R.cinematique_directe_2r, 0, 1, 0, 0), "l1=0 -> ValueError")
check(leve(R.cinematique_directe_2r, 1, -1, 0, 0), "l2<0 -> ValueError")
check(leve(R.cinematique_directe_2r, 1, 1, "x", 0), "angle non numérique -> ValueError")
check(leve(R.portee_max, -3, 1), "longueur négative -> ValueError")

# DÉTERMINISME
check(R.cinematique_directe_2r(2, 1, 30, 60) == R.cinematique_directe_2r(2, 1, 30, 60), "déterminisme")

print(f"\n=== valide_robotique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
