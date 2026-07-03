"""
VALIDATION des BANDITS (bandit.py). Invariant : REGRET SOUS-LINÉAIRE (regret/T -> 0), bat largement l'aléatoire,
converge vers le bon bras ; la borne UCB est un vrai majorant de confiance (jamais sur-confiant sur un bras).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import bandit as B
from bandit import UCB, THOMPSON

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


MOY = [0.2, 0.5, 0.55, 0.9]


def regret_moyen(strat, T, runs=5):
    """Regret/T moyenné sur plusieurs graines (réduit le bruit)."""
    return sum(B.simule(MOY, T, strat, seed=s)[0] for s in range(runs)) / (runs * T)


print("=== REGRET SOUS-LINÉAIRE : regret/T décroît quand T grandit ===")
for strat in (UCB, THOMPSON):
    r_court = regret_moyen(strat, 1000)
    r_long = regret_moyen(strat, 8000)
    print(f"   {strat} : regret/T  T=1000 -> {r_court:.4f} ; T=8000 -> {r_long:.4f}")
    check(f"{strat} : regret/T décroît (sous-linéaire)", r_long < r_court * 0.8)

print("=== BAT L'ALÉATOIRE (qui a un regret LINÉAIRE) ===")
opt = max(MOY)
regret_alea_T = opt - sum(MOY) / len(MOY)         # regret/T de la stratégie uniforme aléatoire
for strat in (UCB, THOMPSON):
    r = regret_moyen(strat, 8000)
    print(f"   {strat} regret/T={r:.4f} vs aléatoire {regret_alea_T:.4f}")
    check(f"{strat} bat largement l'aléatoire", r < regret_alea_T / 3)

print("=== CONVERGENCE vers le BON bras ===")
for strat in (UCB, THOMPSON):
    fopt = sum(B.simule(MOY, 8000, strat, seed=s)[1] for s in range(5)) / 5
    check(f"{strat} : fraction du bras optimal >= 0.9 ({fopt:.3f})", fopt >= 0.9)

print("=== BORNE UCB = vrai MAJORANT de confiance (optimisme honnête, pas sur-confiant) ===")
# au fil d'un run, la borne sup d'un bras doit MAJORER sa vraie moyenne dans la grande majorité des cas
rng = random.Random(3)
b = B.Bandit(len(MOY), UCB, seed=3)
couvre, tot = 0, 0
for _ in range(6000):
    a = b.choisis()
    r = 1.0 if rng.random() < MOY[a] else 0.0
    b.observe(a, r)
    for x in range(len(MOY)):
        if b.tirages[x] > 0:
            tot += 1
            if b.borne_sup(x) >= MOY[x]:
                couvre += 1
taux = couvre / tot
print(f"   borne_sup ≥ vraie moyenne : {taux:.3f} du temps")
check(f"borne UCB majore la vraie moyenne >= 0.9 du temps ({taux:.3f})", taux >= 0.9)

print("=== bras clairement meilleur finalement identifié ===")
b2 = B.Bandit(len(MOY), THOMPSON, seed=5)
rng2 = random.Random(5)
for _ in range(4000):
    a = b2.choisis(); b2.observe(a, 1.0 if rng2.random() < MOY[a] else 0.0)
check("meilleur bras estimé = vrai meilleur (indice 3)", b2.meilleur_estime() == 3)

print(f"\nBANDIT VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
