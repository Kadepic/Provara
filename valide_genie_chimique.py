"""VALIDE genie_chimique.py — ADVERSE, FAUX=0. Temps de séjour, conversion CSTR/PFR ordre 1 (PFR>CSTR pour même k·τ),
Fenske + SOUNDNESS (débit/volume ≤ 0, α ≤ 1, fractions invalides -> ValueError)."""
import math

import genie_chimique as G

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, rel=1e-4):
    return abs(a - b) <= rel * abs(b) + 1e-9


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# TEMPS DE SÉJOUR
check(G.temps_sejour(100, 5) == 20.0, "τ = V/Q = 20 s")
check(G.temps_sejour(50, 50) == 1.0, "τ = 1 s")

# CONVERSION ordre 1
check(proche(G.conversion_cstr_ordre1(0.5, 4), 2 / 3), "CSTR : kτ/(1+kτ) = 2/3")
check(proche(G.conversion_pfr_ordre1(0.5, 4), 1 - math.exp(-2)), "PFR : 1−e^(−kτ)")
check(proche(G.conversion_cstr_ordre1(1, 1), 0.5), "CSTR kτ=1 -> X=0.5")
# PFR plus efficace que CSTR à kτ égal (résultat classique du génie de la réaction)
for kt in [(0.5, 4), (1, 1), (2, 3)]:
    check(G.conversion_pfr_ordre1(*kt) > G.conversion_cstr_ordre1(*kt), f"PFR > CSTR pour kτ={kt}")
# conversion croît avec kτ et reste < 1
check(G.conversion_cstr_ordre1(10, 10) < 1 and G.conversion_pfr_ordre1(1, 3) < 1, "X < 1 (asymptote)")
check(G.conversion_cstr_ordre1(0.1, 1) < G.conversion_cstr_ordre1(1, 1), "X croît avec k")

# FENSKE (distillation)
n = G.etages_fenske(0.95, 0.05, 2)
check(proche(n, math.log((0.95 / 0.05) * (0.95 / 0.05)) / math.log(2)), "Fenske xD=0.95,xB=0.05,α=2")
check(proche(n, 8.49586, rel=1e-4), "Fenske ≈ 8.5 étages")
# plus α est grand, moins il faut d'étages
check(G.etages_fenske(0.95, 0.05, 4) < G.etages_fenske(0.95, 0.05, 2), "α↑ -> moins d'étages")

# SOUNDNESS
check(leve(G.temps_sejour, 100, 0), "Q=0 -> ValueError")
check(leve(G.conversion_cstr_ordre1, 0, 4), "k=0 -> ValueError")
check(leve(G.etages_fenske, 0.95, 0.05, 1), "α=1 -> ValueError")
check(leve(G.etages_fenske, 0.05, 0.95, 2), "xD<xB -> ValueError")
check(leve(G.etages_fenske, 1.0, 0.05, 2), "xD=1 -> ValueError")

# DÉTERMINISME
check(G.conversion_pfr_ordre1(0.5, 4) == G.conversion_pfr_ordre1(0.5, 4), "déterminisme")

print(f"\n=== valide_genie_chimique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
