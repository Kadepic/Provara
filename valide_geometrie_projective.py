"""VALIDE geometrie_projective.py — ADVERSE, FAUX=0. Birapports connus, INVARIANCE par homographie (propriété
fondamentale, oracle non circulaire), division harmonique (−1) + SOUNDNESS (points confondus -> ValueError)."""
from fractions import Fraction as F

import geometrie_projective as G

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# BIRAPPORTS connus (calcul exact)
check(G.birapport(0, 1, 2, 3) == F(4, 3), "birapport(0,1,2,3) = 4/3")
check(G.birapport(0, 2, 1, 3) == F(-1, 3), "birapport(0,2,1,3) = -1/3")
check(G.birapport(1, 2, 3, 4) == F(4, 3), "birapport invariant par translation")

# INVARIANCE PAR HOMOGRAPHIE (la propriété DÉFINISSANTE de la géométrie projective) — oracle indépendant
for (p, q, r, s) in [(2, 1, 1, 3), (1, 0, 0, 2), (3, -1, 2, 5)]:
    pts = [0, 1, 3, 7]
    images = [G.homographie(x, p, q, r, s) for x in pts]
    check(G.birapport(*pts) == G.birapport(*images), f"birapport invariant sous homographie {(p, q, r, s)}")

# permutations du birapport : (a,b;c,d) et (b,a;d,c) sont égaux ; (a,b;d,c) est l'inverse
br = G.birapport(0, 1, 3, 7)
check(G.birapport(1, 0, 7, 3) == br, "symétrie (a,b;c,d)=(b,a;d,c)")
check(G.birapport(0, 1, 7, 3) == 1 / br, "(a,b;d,c) = 1/birapport")

# DIVISION HARMONIQUE
d = G.conjugue_harmonique(0, 6, 2)
check(d == -6, "conjugué harmonique de 2 / (0,6) = -6")
check(G.est_division_harmonique(0, 6, 2, d) is True, "(0,6;2,-6) est harmonique (birapport=-1)")
check(G.est_division_harmonique(0, 1, 2, 3) is False, "birapport 4/3 ≠ -1 -> non harmonique")
# le conjugué harmonique est involutif sur c<->d
d2 = G.conjugue_harmonique(0, 6, -6)
check(d2 == 2, "conjugué harmonique involutif (2 <-> -6)")

# SOUNDNESS
check(leve(G.birapport, 0, 1, 1, 2), "c=b (dénominateur nul) -> ValueError")
check(leve(G.birapport, 0, 1, 2, 0), "d=a (dénominateur nul) -> ValueError")
check(leve(G.conjugue_harmonique, 0, 6, 3), "c milieu de [a,b] -> conjugué à l'infini -> ValueError")
check(leve(G.homographie, 1, 2, 4, 1, 2), "homographie dégénérée (det=0) -> ValueError")

# DÉTERMINISME
check(G.birapport(0, 1, 2, 3) == G.birapport(0, 1, 2, 3), "déterminisme")

print(f"\n=== valide_geometrie_projective : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
