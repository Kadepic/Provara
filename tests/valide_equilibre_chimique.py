"""VALIDE equilibre_chimique.py — ADVERSE, FAUX=0. Quotient de réaction connu, sens d'évolution (loi d'action de
masse), Le Chatelier (température) + SOUNDNESS (concentration/K ≤ 0 -> ValueError)."""
import equilibre_chimique as E

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, rel=1e-6):
    return abs(a - b) <= rel * abs(b) + 1e-9


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# QUOTIENT DE RÉACTION
check(E.quotient_reaction([(2, 2)], [(1, 1), (1, 3)]) == 4.0, "Q(NH3) = 2²/(1·1³) = 4")
check(E.quotient_reaction([(4, 1)], [(2, 1)]) == 2.0, "Q = 4/2 = 2")
check(proche(E.quotient_reaction([(3, 2)], [(3, 2)]), 1.0), "produits = réactifs -> Q = 1")
check(E.quotient_reaction([(2, 3)], [(2, 1)]) == 4.0, "Q = 2³/2 = 4")

# SENS D'ÉVOLUTION (loi d'action de masse)
check(E.sens_evolution(4, 10) == "direct", "Q<K -> sens direct (→ produits)")
check(E.sens_evolution(4, 1) == "inverse", "Q>K -> sens inverse (← réactifs)")
check(E.sens_evolution(4, 4) == "equilibre", "Q=K -> équilibre")
check(E.sens_evolution(0.001, 1000) == "direct" and E.sens_evolution(1000, 0.001) == "inverse", "extrêmes")

# LE CHATELIER (température)
check(E.deplace_equilibre_temperature(True, True) == "inverse", "exo + ↑T -> sens inverse")
check(E.deplace_equilibre_temperature(True, False) == "direct", "exo + ↓T -> sens direct")
check(E.deplace_equilibre_temperature(False, True) == "direct", "endo + ↑T -> sens direct")
check(E.deplace_equilibre_temperature(False, False) == "inverse", "endo + ↓T -> sens inverse")

# SOUNDNESS
check(leve(E.quotient_reaction, [(0, 1)], [(1, 1)]), "concentration nulle -> ValueError")
check(leve(E.quotient_reaction, [(-2, 1)], [(1, 1)]), "concentration négative -> ValueError")
check(leve(E.quotient_reaction, [], [(1, 1)]), "produits vides -> ValueError")
check(leve(E.sens_evolution, 4, 0), "K=0 -> ValueError")
check(leve(E.sens_evolution, -1, 4), "Q<0 -> ValueError")
check(leve(E.deplace_equilibre_temperature, "oui", True), "non-booléen -> ValueError")

# DÉTERMINISME
check(E.sens_evolution(4, 10) == E.sens_evolution(4, 10), "déterminisme")

print(f"\n=== valide_equilibre_chimique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
