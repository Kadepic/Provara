"""VALIDE geotechnique.py — ADVERSE, FAUX=0. Contrainte verticale/effective (Terzaghi), Rankine (Ka·Kp=1, φ=30°→1/3)
+ SOUNDNESS (φ hors [0,90°[, valeurs négatives -> ValueError)."""
import geotechnique as G

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
    return abs(a - b) <= rel * abs(b) + 1e-6


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# CONTRAINTES
check(G.contrainte_verticale(18, 5) == 90.0, "σ = γz = 90 kPa")
check(G.contrainte_verticale(20, 0) == 0.0, "z=0 -> σ=0")
check(G.contrainte_effective(90, 20) == 70.0, "σ' = σ - u = 70 (Terzaghi)")
check(G.contrainte_effective(90, 0) == 90.0, "u=0 -> σ'=σ (sol sec)")

# RANKINE
check(proche(G.coefficient_poussee_active(30), 1 / 3), "Ka(30°) = 1/3")
check(proche(G.coefficient_poussee_passive(30), 3.0), "Kp(30°) = 3")
check(G.coefficient_poussee_active(0) == 1.0, "Ka(0°) = 1 (état au repos limite)")
check(proche(G.coefficient_poussee_active(45), G.coefficient_poussee_active(45)), "déterminisme Ka")
# Ka et Kp sont inverses
check(proche(G.coefficient_poussee_active(30) * G.coefficient_poussee_passive(30), 1.0), "Ka·Kp = 1")
check(proche(G.coefficient_poussee_active(20) * G.coefficient_poussee_passive(20), 1.0), "Ka·Kp = 1 (φ=20°)")
# Ka décroît avec φ
check(G.coefficient_poussee_active(40) < G.coefficient_poussee_active(20), "Ka décroît avec φ")

# POUSSÉE ACTIVE
check(proche(G.poussee_active(18, 5, 30), 75.0), "Pa = ½·(1/3)·18·25 = 75 kN/m")
check(G.poussee_active(18, 0, 30) == 0.0, "H=0 -> Pa=0")

# SOUNDNESS
check(leve(G.coefficient_poussee_active, 90), "φ=90° -> ValueError")
check(leve(G.coefficient_poussee_active, -5), "φ<0 -> ValueError")
check(leve(G.contrainte_verticale, -18, 5), "γ<0 -> ValueError")
check(leve(G.contrainte_effective, 90, -10), "u<0 -> ValueError")
check(leve(G.poussee_active, 18, -5, 30), "H<0 -> ValueError")

print(f"\n=== valide_geotechnique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
