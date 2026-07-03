"""VALIDE series_calcul.py — ADVERSE, FAUX=0. Sommes CONNUES (Gauss n(n+1)/2, Σk², géométriques Σ1/2ⁿ=1),
critères de convergence (géométrique, Riemann) + SOUNDNESS (série divergente -> ValueError, jamais une fausse limite)."""
from fractions import Fraction as F

import series_calcul as S

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


# ARITHMÉTIQUE (Gauss)
check(S.somme_arithmetique(1, 1, 100) == F(5050), "Gauss Σ1..100 = 5050")
check(S.somme_arithmetique(2, 2, 50) == F(2550), "Σ pairs 2..100 = 2550")
check(S.somme_arithmetique(5, 0, 10) == F(50), "raison 0 -> 10×5 = 50")
check(S.somme_arithmetique(1, 1, 0) == F(0), "0 terme -> 0")
check(S.somme_carres(10) == F(385), "Σk² (1..10) = 385")
check(S.somme_carres(1) == F(1) and S.somme_carres(0) == F(0), "Σk² bords")

# GÉOMÉTRIQUE finie
check(S.somme_geometrique(1, F(1, 2), 5) == F(31, 16), "Σ(1/2)^k k=0..4 = 31/16")
check(S.somme_geometrique(1, 2, 10) == F(1023), "Σ 2^k k=0..9 = 1023")
check(S.somme_geometrique(3, 1, 7) == F(21), "raison 1 -> n·a = 21")
check(S.somme_geometrique(1, F(1, 3), 0) == F(0), "0 terme -> 0")

# GÉOMÉTRIQUE infinie (exacte)
check(S.somme_geometrique_infinie(1, F(1, 2)) == F(2), "Σ(1/2)^k k≥0 = 2")
check(S.somme_geometrique_infinie(F(1, 2), F(1, 2)) == F(1), "Σ(1/2)^k k≥1 = 1")
check(S.somme_geometrique_infinie(1, F(-1, 2)) == F(2, 3), "Σ(-1/2)^k = 2/3 (alternée)")
check(S.somme_geometrique_infinie(1, F(1, 10)) == F(10, 9), "Σ(1/10)^k = 10/9 (0.111... = 1/9 décalé)")

# CRITÈRES DE CONVERGENCE
check(S.converge_geometrique(F(1, 2)) and not S.converge_geometrique(1) and not S.converge_geometrique(2),
      "convergence géométrique ssi |r|<1")
check(not S.converge_riemann(1) and S.converge_riemann(2) and not S.converge_riemann(F(1, 2)),
      "Riemann converge ssi s>1 (harmonique s=1 diverge)")

# SOUNDNESS — divergence -> ValueError
check(leve(S.somme_geometrique_infinie, 1, 1), "|r|=1 -> ValueError")
check(leve(S.somme_geometrique_infinie, 1, 2), "|r|=2 -> ValueError")
check(leve(S.somme_geometrique_infinie, 1, F(-3, 2)), "|r|=3/2 -> ValueError")
check(leve(S.somme_arithmetique, 1, 1, -1), "n négatif -> ValueError")
check(leve(S.somme_geometrique, 1, 2, -1), "n négatif (géom) -> ValueError")

# DÉTERMINISME
check(S.somme_geometrique_infinie(1, F(1, 2)) == S.somme_geometrique_infinie(1, F(1, 2)), "déterminisme")

print(f"\n=== valide_series_calcul : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
