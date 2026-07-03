"""VALIDE information_calcul.py — ADVERSE, FAUX=0. Ancres connues (pièce=1 bit, dé 4 faces=2 bits, H([.5,.25,.25])=1.5)
+ propriétés (I≥0, I=0 si indépendants, KL≥0, KL=0 ssi p=q) + SOUNDNESS (distribution invalide -> ValueError)."""
import math

import information_calcul as I

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, t=1e-9):
    return abs(a - b) <= t


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ENTROPIE — ancres exactes
check(proche(I.entropie([0.5, 0.5]), 1.0), "pièce équilibrée = 1 bit")
check(proche(I.entropie([0.25] * 4), 2.0), "dé 4 faces = 2 bits")
check(proche(I.entropie([0.125] * 8), 3.0), "8 issues = 3 bits")
check(proche(I.entropie([1.0, 0.0, 0.0]), 0.0), "certitude = 0 bit")
check(proche(I.entropie([0.5, 0.25, 0.25]), 1.5), "H([.5,.25,.25]) = 1.5 bits")
check(proche(I.entropie([0.7, 0.3]), -0.7 * math.log2(0.7) - 0.3 * math.log2(0.3)), "H Bernoulli(0.7)")
# l'uniforme MAXIMISE l'entropie sur n issues (= log2 n)
check(proche(I.entropie([1 / 3] * 3), math.log2(3)), "uniforme 3 = log2(3)")
check(I.entropie([0.6, 0.4]) < I.entropie([0.5, 0.5]) + 1e-12, "uniforme maximise l'entropie")

# INFORMATION MUTUELLE
check(proche(I.information_mutuelle([[0.25, 0.25], [0.25, 0.25]]), 0.0), "indépendants -> I = 0")
check(proche(I.information_mutuelle([[0.5, 0.0], [0.0, 0.5]]), 1.0), "corrélation parfaite -> I = H = 1")
check(I.information_mutuelle([[0.4, 0.1], [0.1, 0.4]]) > 0, "I ≥ 0 (dépendance partielle)")

# DIVERGENCE KL
check(proche(I.divergence_kl([0.5, 0.5], [0.5, 0.5]), 0.0), "KL(p‖p) = 0")
check(proche(I.divergence_kl([1.0, 0.0], [0.5, 0.5]), 1.0), "KL([1,0]‖[.5,.5]) = 1 bit")
check(I.divergence_kl([0.7, 0.3], [0.5, 0.5]) > 0, "KL ≥ 0 (Gibbs)")

# SOUNDNESS
check(leve(I.entropie, [0.5, 0.6]), "somme ≠ 1 -> ValueError")
check(leve(I.entropie, [-0.1, 1.1]), "proba négative -> ValueError")
check(leve(I.entropie, []), "distribution vide -> ValueError")
check(leve(I.entropie, [0.5, "x"]), "proba non numérique -> ValueError")
check(leve(I.divergence_kl, [1.0, 0.0], [0.0, 1.0]), "KL support incompatible (q=0,p>0) -> ValueError")

# DÉTERMINISME
check(I.entropie([0.3, 0.7]) == I.entropie([0.3, 0.7]), "déterminisme")

print(f"\n=== valide_information_calcul : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
