"""
VALIDATION du TEST DE PERMUTATION (test_permutation.py). Vérifie que la p-value de permutation est valide et contrôle
l'erreur de type I ≈ α sous échangeabilité (loi normale ET asymétrique), que le t-test SUR-REJETTE (type I gonflé =
sur-confiance) sur données asymétriques à tailles inégales alors que la permutation reste calibrée, que la permutation
a de la PUISSANCE (détecte une vraie différence) et ne perd rien sous normalité, et l'ABSTENTION. Pur Python.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import test_permutation as TP
from test_permutation import ABSTENTION, TEST

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


rng = random.Random(82)


def type_I(gen, nA, nB, methode, N=600, alpha=0.05, n_perm=400):
    rej = 0
    for _ in range(N):
        A = [gen() for _ in range(nA)]; B = [gen() for _ in range(nB)]
        if methode == "perm":
            rej += TP.p_permutation(A, B, rng, n_perm) < alpha
        else:
            try:
                rej += TP.p_ttest_welch(A, B) < alpha
            except Exception:
                pass
    return rej / N


# ─── 1. p-value valide + type I ≈ α (normale) ───
print("=== p-value valide + type I ≈ α (normale) ===")
A = [rng.gauss(0, 1) for _ in range(10)]; B = [rng.gauss(0, 1) for _ in range(10)]
pp = TP.p_permutation(A, B, rng, 2000)
check("p-value ∈ ]0, 1]", 0 < pp <= 1)
ti_perm_norm = type_I(lambda: rng.gauss(0, 1), 8, 8, "perm")
print(f"   type I permutation (normale) = {ti_perm_norm:.3f}")
check("permutation : type I ≈ α sous normalité", abs(ti_perm_norm - 0.05) < 0.03)

# ─── 2. type I ≈ α aussi sous loi ASYMÉTRIQUE (distribution-free) ───
print("=== Permutation distribution-free : type I ≈ α sous asymétrie ===")
expo = lambda: rng.expovariate(1)                       # rng SEEDÉ (reproductible, pas le module global)
ti_perm_skew = type_I(expo, 4, 16, "perm", N=2000)
print(f"   type I permutation (expo, tailles 4/16) = {ti_perm_skew:.3f}")
check("permutation : type I ≈ α même sur données asymétriques/tailles inégales", ti_perm_skew < 0.09)

# ─── 3. DÉMASQUE : le t-test SUR-REJETTE (sur-confiance) sur ce cas ───
print("=== Mode d'échec : t-test gonflé sur asymétrie + tailles inégales ===")
ti_t_skew = type_I(expo, 4, 16, "ttest", N=4000)        # N grand → estimation stable de l'inflation
print(f"   type I t-test (expo, 4/16) = {ti_t_skew:.3f} (nominal 0.05)")
check("le t-test SUR-REJETTE (type I gonflé nettement > nominal 0.05)", ti_t_skew > 0.068)
check("la permutation contrôle bien mieux que le t-test sur ce cas", ti_perm_skew < ti_t_skew - 0.012)

# ─── 4. Puissance : détecte une vraie différence ───
print("=== Puissance : détecte une vraie différence ===")
det = 0
for _ in range(300):
    A = [rng.expovariate(1) for _ in range(15)]
    B = [rng.expovariate(1) + 1.5 for _ in range(15)]
    if TP.p_permutation(A, B, rng, 400) < 0.05:
        det += 1
print(f"   puissance (décalage +1.5) = {det/300:.3f}")
check("puissance élevée sous une vraie différence (> 0.7)", det / 300 > 0.7)

# ─── 5. Pas de perte sous normalité (perm ≈ t-test) ───
print("=== Sous normalité : permutation ≈ t-test (pas de perte) ===")
A = [rng.gauss(0, 1) for _ in range(20)]; B = [rng.gauss(0.6, 1) for _ in range(20)]
pp2 = TP.p_permutation(A, B, rng, 3000); pt2 = TP.p_ttest_welch(A, B)
print(f"   p permutation={pp2:.3f} ; t-test={pt2:.3f}")
check("permutation et t-test proches sous normalité (|Δp|<0.05)", abs(pp2 - pt2) < 0.05)
# statistique extrême → petite p
Aex = [10.0] * 10; Bex = [0.0] * 10
check("séparation extrême → p très petite", TP.p_permutation(Aex, Bex, rng, 2000) < 0.01)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = TP.teste([1.0], [2.0, 3.0], rng)
st2, _ = TP.teste([], [1.0, 2.0], rng)
check("groupe n<2 → ABSTENTION", st1 == ABSTENTION)
check("groupe vide → ABSTENTION", st2 == ABSTENTION)
st3, _ = TP.teste([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], rng, 500)
check("cas valide → TEST", st3 == TEST)

print(f"\nRÉSULTAT test_permutation : {ok}/{total}")
assert ok == total
