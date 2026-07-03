"""VALIDE mecanique.py — ADVERSE, FAUX=0. Ancres physiques connues (T=2π√(m/k), pendule, Archimède = poids du fluide
déplacé, pression hydrostatique) + cohérence interne (f = 1/T, ω = 2π/T) + SOUNDNESS (domaine invalide -> ValueError).
"""
import math

import mecanique as M

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


# FROTTEMENT
check(M.force_frottement(0.5, 100) == 50.0, "F = μN = 50")
check(M.force_frottement(0, 100) == 0.0, "μ=0 -> 0")

# OSCILLATEUR : ancres + cohérence interne
check(proche(M.periode_ressort(1, 1), 2 * math.pi), "T(m=1,k=1) = 2π")
check(proche(M.periode_ressort(2, 8), math.pi), "T(m=2,k=8) = 2π/2 = π")
check(proche(M.periode_ressort(4, 1), 4 * math.pi), "T ∝ √m : T(4,1) = 4π")
check(proche(M.pulsation_ressort(2, 8), 2.0), "ω = √(k/m) = 2")
check(proche(M.frequence_ressort(1, 1), 1 / (2 * math.pi)), "f(1,1) = 1/2π")
check(proche(M.frequence_ressort(1, 4 * math.pi ** 2), 1.0), "f(m=1,k=4π²) = 1 Hz")
# cohérence f = 1/T et ω = 2π/T
check(proche(M.frequence_ressort(3, 7) * M.periode_ressort(3, 7), 1.0), "f·T = 1")
check(proche(M.pulsation_ressort(3, 7), 2 * math.pi / M.periode_ressort(3, 7)), "ω = 2π/T")
check(proche(M.periode_pendule(1), 2.00607, rel=1e-3), "pendule L=1 ≈ 2.006 s")
check(proche(M.periode_pendule(M.G_PESANTEUR), 2 * math.pi), "pendule L=g -> 2π")
check(proche(M.energie_ressort(200, 0.1), 1.0), "E = ½·200·0.1² = 1 J")
check(M.energie_ressort(0, 5) == 0.0, "k=0 -> énergie 0")

# FLUIDES
check(M.pression(100, 2) == 50.0, "P = F/A = 50 Pa")
check(proche(M.poussee_archimede(1000, 0.001), 9.80665), "Archimède 1 L d'eau = 9.807 N")
check(proche(M.poussee_archimede(1000, 1), 9806.65), "Archimède 1 m³ d'eau = poids 1000 kg")
check(proche(M.pression_hydrostatique(1000, 10), 98066.5), "P hydro 10 m d'eau ≈ 0.981 bar")
check(M.pression_hydrostatique(1000, 0) == 0.0, "h=0 -> P=0")

# SOUNDNESS
check(leve(M.periode_ressort, 0, 1), "m=0 -> ValueError")
check(leve(M.periode_ressort, 1, 0), "k=0 -> ValueError")
check(leve(M.force_frottement, -0.5, 100), "μ<0 -> ValueError")
check(leve(M.pression, 100, 0), "surface=0 -> ValueError")
check(leve(M.pression_hydrostatique, 1000, -5), "profondeur<0 -> ValueError")
check(leve(M.poussee_archimede, -1, 1), "ρ<0 -> ValueError")
check(leve(M.periode_ressort, "x", 1), "non-numérique -> ValueError")

# DÉTERMINISME
check(M.periode_ressort(2, 8) == M.periode_ressort(2, 8), "déterminisme")

print(f"\n=== valide_mecanique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
