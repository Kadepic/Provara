"""VALIDE electronique.py — ADVERSE, FAUX=0. Associations connues (série=Σ, parallèle, diviseur, RC, impédances)
+ propriétés (parallèle ≤ min, 2 R égales en // = R/2) + SOUNDNESS (R/f/C ≤ 0, liste vide -> ValueError)."""
import math

import electronique as E

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


# SÉRIE / PARALLÈLE
check(E.resistance_serie([10, 20, 30]) == 60.0, "série = 60 Ω")
check(E.resistance_serie([5]) == 5.0, "série singleton")
check(proche(E.resistance_parallele([2, 3, 6]), 1.0), "parallèle [2,3,6] = 1 Ω")
check(E.resistance_parallele([10, 10]) == 5.0, "2 R égales en // = R/2")
check(E.resistance_parallele([100]) == 100.0, "parallèle singleton = R")
check(E.resistance_parallele([4, 4, 4, 4]) == 1.0, "4 R égales en // = R/4")
# parallèle toujours ≤ la plus petite résistance
check(E.resistance_parallele([2, 8]) < 2, "parallèle < min(R)")

# DIVISEUR DE TENSION
check(E.diviseur_tension(12, 1000, 2000) == 8.0, "diviseur 12V -> 8V")
check(E.diviseur_tension(10, 1000, 1000) == 5.0, "R1=R2 -> Vin/2")
check(E.diviseur_tension(9, 0.5, 0.5) == 4.5, "diviseur symétrique")

# RC / IMPÉDANCES / RÉSONANCE
check(proche(E.constante_temps_rc(1000, 1e-6), 1e-3), "τ = RC = 1 ms")
check(proche(E.impedance_condensateur(50, 1e-6), 1 / (2 * math.pi * 50 * 1e-6)), "Xc = 1/2πfC")
check(proche(E.impedance_bobine(50, 0.1), 2 * math.pi * 50 * 0.1), "XL = 2πfL")
check(proche(E.frequence_resonance_lc(1e-3, 1e-6), 1 / (2 * math.pi * math.sqrt(1e-9))), "f résonance LC")
# à la résonance XL = XC
fr = E.frequence_resonance_lc(1e-3, 1e-6)
check(proche(E.impedance_bobine(fr, 1e-3), E.impedance_condensateur(fr, 1e-6)), "à résonance XL = XC")

# SOUNDNESS
check(leve(E.resistance_serie, []), "liste vide -> ValueError")
check(leve(E.resistance_parallele, [10, 0]), "R=0 -> ValueError")
check(leve(E.resistance_serie, [10, -5]), "R<0 -> ValueError")
check(leve(E.diviseur_tension, 12, 0, 100), "R1=0 -> ValueError")
check(leve(E.constante_temps_rc, 1000, 0), "C=0 -> ValueError")
check(leve(E.impedance_condensateur, 0, 1e-6), "f=0 -> ValueError")

# DÉTERMINISME
check(E.resistance_parallele([2, 3, 6]) == E.resistance_parallele([2, 3, 6]), "déterminisme")

print(f"\n=== valide_electronique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
