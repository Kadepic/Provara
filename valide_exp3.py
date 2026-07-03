"""
VALIDATION du BANDIT ADVERSARIAL EXP3 (exp3.py). Vérifie le plancher d'exploration (p_i ≥ γ/K), la propriété
NO-REGRET (regret/T → 0), la borne de regret ~2√((e−1)TK ln K), le DÉMASQUE (un glouton est EXPLOITABLE = regret
linéaire, EXP3 reste sous-linéaire), la robustesse aussi en environnement STOCHASTIQUE, et l'ABSTENTION. Pur Python.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import exp3 as X
from exp3 import ABSTENTION, JOUE

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


def piege(T, K):
    """Adversaire piège : bras 0 payé pendant l'amorce (K tours), puis bras 1 domine."""
    R = []
    for t in range(T):
        row = [0.0] * K
        row[0 if t < K else 1] = 1.0
        R.append(row)
    return R


def regret_exp3_moyen(R, seeds=15):
    T, K = len(R), len(R[0])
    g = X.gamma_optimal(T, K)
    return sum(X.regret(R, X.exp3(R, g, random.Random(s))[0]) for s in range(seeds)) / seeds


# ─── 1. Plancher d'exploration p_i ≥ γ/K ───
print("=== Plancher d'exploration : p_i ≥ γ/K ===")
R = piege(2000, 4); g = X.gamma_optimal(2000, 4)
_, _, pmin = X.exp3(R, g, random.Random(1))
print(f"   γ={g:.4f}, p_min observé={pmin:.4f} (≥ γ/K={g/4:.4f})")
check("p_i ≥ γ/K (exploration forcée)", pmin >= g / 4 - 1e-9)

# ─── 2. No-regret : regret/T → 0 ───
print("=== No-regret : regret/T décroît avec T ===")
r_petit = regret_exp3_moyen(piege(500, 4)) / 500
r_grand = regret_exp3_moyen(piege(8000, 4)) / 8000
print(f"   regret/T : T=500 → {r_petit:.3f} ; T=8000 → {r_grand:.3f}")
check("regret/T décroît avec T (no-regret)", r_grand < r_petit)
check("regret/T petit à grand T (< 0.1)", r_grand < 0.1)

# ─── 3. Borne de regret ───
print("=== Borne de regret ~2√((e−1)TK ln K) ===")
T, K = 3000, 4
R = piege(T, K)
reg_moy = regret_exp3_moyen(R, 20)
b = 2 * math.sqrt((math.e - 1) * T * K * math.log(K))
print(f"   regret moyen EXP3={reg_moy:.1f} ; borne={b:.0f}")
check("regret moyen EXP3 ≤ borne théorique", reg_moy <= b)

# ─── 4. DÉMASQUE : glouton exploité (regret linéaire) vs EXP3 sous-linéaire ───
print("=== Mode d'échec : glouton piégé (regret linéaire) ===")
reg_g = X.regret(R, X.glouton(R, random.Random(0)))
print(f"   regret glouton={reg_g} (≈ T, linéaire) ; regret EXP3≈{reg_moy:.0f} (sous-linéaire)")
check("le glouton subit un regret ~linéaire (≈ T)", reg_g > 0.8 * T)
check("EXP3 fait BIEN mieux que le glouton (regret ≪)", reg_moy < reg_g / 5)

# ─── 5. Robustesse en environnement STOCHASTIQUE ───
print("=== Robustesse : EXP3 sous-linéaire aussi en stochastique ===")
rng = random.Random(5)
means = [0.2, 0.8, 0.5, 0.3]
Rs = [[1.0 if rng.random() < means[i] else 0.0 for i in range(4)] for _ in range(3000)]
reg_s = regret_exp3_moyen(Rs, 10)
print(f"   regret/T stochastique = {reg_s/3000:.3f}")
check("EXP3 sous-linéaire aussi en stochastique (regret/T < 0.2)", reg_s / 3000 < 0.2)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = X.joue([], random.Random(0))
st2, _ = X.joue([[0.5, 0.5], [0.5]], random.Random(0))
st3, _ = X.joue([[0.5, 2.0]], random.Random(0))
check("matrice vide → ABSTENTION", st1 == ABSTENTION)
check("matrice mal formée → ABSTENTION", st2 == ABSTENTION)
check("récompenses hors [0,1] → ABSTENTION", st3 == ABSTENTION)
st4, _ = X.joue(piege(200, 3), random.Random(0))
check("cas valide → JOUE", st4 == JOUE)

print(f"\nRÉSULTAT exp3 : {ok}/{total}")
assert ok == total
