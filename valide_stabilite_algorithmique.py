"""
VALIDATION de la STABILITÉ ALGORITHMIQUE (stabilite_algorithmique.py). Vérifie que la stabilité β̂ décroît avec k
(et avec n), que l'algorithme INSTABLE (1-NN) MÉMORISE (R_emp≈0) et SOUS-ESTIME le risque vrai (sur-confiance),
que la borne de Bousquet-Elisseeff COUVRE le risque vrai et reste large pour l'instable (le signale) / serrée pour
le stable, et l'ABSTENTION. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import stabilite_algorithmique as ST
from stabilite_algorithmique import ABSTENTION, ANALYSE

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


def population(rng, M=150, sigma=0.25):
    f = lambda x: 0.5 + 0.35 * math.sin(3 * x)
    return [(x, min(1, max(0, f(x) + rng.gauss(0, sigma)))) for x in [i / M for i in range(M)]]


def tire_train(rng, pop, n):
    return [pop[rng.randrange(len(pop))] for _ in range(n)]


rng = random.Random(74)
pop = population(rng)
n = 30
REP = 40


def moyennes(k, n=30, reps=REP):
    """β̂, R_emp, R_vrai, borne moyens sur `reps` jeux d'entraînement."""
    bs = res = rvs = bns = 0.0
    for _ in range(reps):
        tr = tire_train(rng, pop, n)
        info = ST.analyse(tr, pop, k, rng)[1]
        bs += info["beta"]; res += info["r_emp"]; rvs += info["r_vrai"]; bns += info["borne"]
    return bs / reps, res / reps, rvs / reps, bns / reps


# ─── 1. β̂ décroît avec k ───
print("=== Stabilité : β̂ décroît avec k ===")
betas = [moyennes(k)[0] for k in (1, 3, 9, 20)]
print(f"   β̂ pour k=1,3,9,20 : {[round(b,3) for b in betas]}")
check("β̂ décroît avec k (grand k = plus stable)", all(betas[i] >= betas[i+1] - 1e-9 for i in range(len(betas)-1)))

# ─── 2. β̂ décroît avec n ───
print("=== β̂ décroît avec n ===")
b_petit = moyennes(9, n=15)[0]
b_grand = moyennes(9, n=60)[0]
print(f"   β̂ k=9 : n=15 → {b_petit:.3f} ; n=60 → {b_grand:.3f}")
check("β̂ décroît avec n", b_grand < b_petit)

# ─── 3. DÉMASQUE : 1-NN mémorise (R_emp≈0) et sous-estime R_vrai ───
print("=== Mode d'échec : 1-NN mémorise et sur-estime sa performance ===")
b1, re1, rv1, bn1 = moyennes(1)
b9, re9, rv9, bn9 = moyennes(9)
print(f"   k=1 : R_emp={re1:.3f} R_vrai={rv1:.3f} (écart={rv1-re1:+.3f}) ; k=9 : R_emp={re9:.3f} R_vrai={rv9:.3f} (écart={rv9-re9:+.3f})")
check("1-NN MÉMORISE : R_emp ≈ 0", re1 < 0.01)
check("1-NN SOUS-ESTIME le vrai risque (sur-confiance)", rv1 - re1 > 0.05)
check("l'écart (sur-confiance) est plus grand pour l'instable que pour le stable", (rv1 - re1) > (rv9 - re9))

# ─── 4. La borne couvre le risque vrai ; large pour instable, serrée pour stable ───
print("=== Borne de Bousquet-Elisseeff : couvre + reflète la stabilité ===")
couvre = 0
for _ in range(200):
    tr = tire_train(rng, pop, n)
    info = ST.analyse(tr, pop, 9, rng)[1]
    if info["r_vrai"] <= info["borne"] + 1e-9:
        couvre += 1
print(f"   couverture (k=9) = {couvre/200:.3f} ; borne k=1={bn1:.2f} (large) vs k=9={bn9:.2f} (serrée)")
check("la borne couvre le risque vrai ≥ 1−δ", couvre / 200 >= 0.95)
check("borne(instable k=1) ≫ borne(stable k=9) (la borne SIGNALE l'instabilité)", bn1 > bn9 + 0.5)

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = ST.analyse([], pop, 1, rng)
st2, _ = ST.analyse(tire_train(rng, pop, 5), pop, 10, rng)   # k > n
st3, _ = ST.analyse(tire_train(rng, pop, 5), [], 2, rng)
check("train vide → ABSTENTION", st1 == ABSTENTION)
check("k > n → ABSTENTION", st2 == ABSTENTION)
check("population vide → ABSTENTION", st3 == ABSTENTION)
st4, _ = ST.analyse(tire_train(rng, pop, 20), pop, 5, rng)
check("cas valide → ANALYSE", st4 == ANALYSE)

print(f"\nRÉSULTAT stabilite_algorithmique : {ok}/{total}")
assert ok == total
