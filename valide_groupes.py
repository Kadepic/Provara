"""VALIDE groupes.py — ADVERSE, FAUX=0. Ordres connus (ℤ/nℤ, permutations), signatures, théorème de Lagrange,
validation de tables de Cayley (groupes connus acceptés, tables cassées rejetées) + SOUNDNESS (entrée invalide
-> ValueError)."""
from math import gcd

import groupes as G

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


# ORDRE dans ℤ/nℤ = n/pgcd(g,n) — vérifié indépendamment
for n in (6, 7, 12):
    for g in range(n):
        attendu = n // gcd(g % n, n) if g % n else 1
        check(G.ordre_element_zn(g, n) == attendu, f"ordre {g} dans Z{n} = {attendu}")
check(G.ordre_element_zn(1, 7) == 7, "Z7 : 1 d'ordre 7 (générateur)")

# ORDRE de permutation = ppcm des cycles
check(G.ordre_permutation((1, 2, 0)) == 3, "3-cycle -> ordre 3")
check(G.ordre_permutation((1, 0, 3, 2)) == 2, "deux 2-cycles -> ordre 2")
check(G.ordre_permutation((1, 2, 3, 4, 0)) == 5, "5-cycle -> ordre 5")
check(G.ordre_permutation((1, 0, 3, 4, 2)) == 6, "2-cycle + 3-cycle -> ppcm = 6")
check(G.ordre_permutation((0, 1, 2)) == 1, "identité -> ordre 1")

# SIGNATURE
check(G.signature_permutation((1, 0, 2)) == -1, "transposition -> -1")
check(G.signature_permutation((1, 2, 0)) == 1, "3-cycle -> +1 (paire)")
check(G.signature_permutation((0, 1, 2, 3)) == 1, "identité -> +1")
check(G.signature_permutation((1, 0, 3, 2)) == 1, "deux transpositions -> +1")
# signature multiplicative : ε(p∘q) = ε(p)·ε(q)
p, q = (1, 2, 0), (1, 0, 2)
check(G.signature_permutation(G.compose_permutations(p, q))
      == G.signature_permutation(p) * G.signature_permutation(q), "ε multiplicative")
check(G.compose_permutations((1, 2, 0), (0, 2, 1)) == (1, 0, 2), "composition correcte")

# TABLE DE CAYLEY — groupes connus vs cassés
Z3 = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
Z4 = [[0, 1, 2, 3], [1, 2, 3, 0], [2, 3, 0, 1], [3, 0, 1, 2]]
KLEIN = [[0, 1, 2, 3], [1, 0, 3, 2], [2, 3, 0, 1], [3, 2, 1, 0]]
check(G.est_groupe(Z3) and G.est_groupe(Z4) and G.est_groupe(KLEIN), "Z3, Z4, Klein sont des groupes")
check(G.est_groupe([[0]]), "groupe trivial")
check(not G.est_groupe([[0, 1, 2], [1, 0, 2], [2, 2, 0]]), "table sans inverse cohérent -> non-groupe")
check(not G.est_groupe([[1, 0], [1, 0]]), "pas d'élément neutre -> non-groupe")
# non-associative : table latine mais (a·b)·c ≠ a·(b·c)
NONASSOC = [[0, 1, 2, 3, 4], [1, 0, 3, 4, 2], [2, 4, 0, 1, 3], [3, 2, 4, 0, 1], [4, 3, 1, 2, 0]]
check(not G.est_groupe(NONASSOC), "carré latin non associatif -> non-groupe")

# LAGRANGE
check(G.lagrange_divise(3, 6) and G.lagrange_divise(2, 6) and not G.lagrange_divise(4, 6), "Lagrange : 3|6,2|6, 4∤6")
check(all(G.lagrange_divise(G.ordre_element_zn(g, 12), 12) for g in range(12)), "ordres de Z12 divisent 12")

# SOUNDNESS
check(leve(G.ordre_element_zn, 1, 0), "n=0 -> ValueError")
check(leve(G.ordre_permutation, (0, 0, 1)), "permutation invalide -> ValueError")
check(leve(G.compose_permutations, (0, 1), (0, 1, 2)), "tailles différentes -> ValueError")
check(leve(G.est_groupe, [[0, 1], [1, 0], [0, 1]]), "table non carrée -> ValueError")
check(leve(G.est_groupe, [[0, 5], [1, 0]]), "entrée hors 0..n-1 (clôture) -> ValueError")

print(f"\n=== valide_groupes : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
