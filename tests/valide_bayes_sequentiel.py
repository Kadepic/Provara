"""
VALIDATION du BAYÉSIEN SÉQUENTIEL (bayes_sequentiel.py) — jugé par calibration.py. Sous a priori cohérent, l'intervalle
crédible couvre le vrai θ ~confiance ; il se resserre avec n ; la moyenne postérieure converge ; séquentiel == lot.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import bayes_sequentiel as BS
import calibration as CAL
from calibration import SURCONFIANT

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


print("=== COUVERTURE BAYÉSIENNE : l'intervalle crédible couvre le vrai θ ~confiance (a priori Uniforme) ===")
for conf in (0.80, 0.90):
    rng = random.Random(int(conf * 100))
    inter, ver = [], []
    for _ in range(3000):
        theta = rng.random()                       # θ ~ Beta(1,1) = Uniforme (a priori cohérent)
        bb = BS.BetaBernoulli(1.0, 1.0)
        for _ in range(40):
            bb.observe(1 if rng.random() < theta else 0)
        inter.append(bb.intervalle_credible(conf))
        ver.append(theta)
    v, i = CAL.verdict_couverture(inter, ver, conf)
    print(f"   confiance={conf} : couverture {i['couverture']:.3f}")
    check(f"couverture {i['couverture']:.3f} ≈ {conf} (±0.03) et NON surconfiant",
          abs(i["couverture"] - conf) < 0.03 and v != SURCONFIANT)

print("=== L'intervalle SE RESSERRE avec n ===")
rng = random.Random(7)
def largeur(n):
    bb = BS.BetaBernoulli()
    for _ in range(n):
        bb.observe(1 if rng.random() < 0.4 else 0)
    bas, haut = bb.intervalle_credible(0.90)
    return haut - bas
l50, l1000 = largeur(50), largeur(1000)
print(f"   largeur n=50 -> {l50:.3f} ; n=1000 -> {l1000:.3f}")
check(f"largeur décroît avec n ({l1000:.3f} < {l50:.3f})", l1000 < l50)
check("largeur ~ 1/√n (ratio cohérent)", l50 / l1000 > 2.5)

print("=== CONVERGENCE de la moyenne postérieure vers le vrai θ ===")
rng = random.Random(3)
bb = BS.BetaBernoulli()
vrai = 0.65
for _ in range(5000):
    bb.observe(1 if rng.random() < vrai else 0)
check(f"moyenne postérieure ≈ vrai θ ({bb.moyenne():.3f} ≈ {vrai})", abs(bb.moyenne() - vrai) < 0.02)

print("=== SÉQUENTIEL == LOT (cohérence de la mise à jour) ===")
seq = BS.BetaBernoulli()
obs = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
for o in obs:
    seq.observe(o)
lot = BS.BetaBernoulli()
lot.observe_lot(sum(obs), len(obs))
check("a,b identiques séquentiel vs lot", seq.a == lot.a and seq.b == lot.b)

print("=== Beta incomplète + quantile : propriétés ===")
check("betai(a,b,0)=0 et betai(a,b,1)=1", BS.betai(2, 3, 0.0) == 0.0 and BS.betai(2, 3, 1.0) == 1.0)
check("betai croissante en x", BS.betai(2, 3, 0.3) < BS.betai(2, 3, 0.7))
check("quantile médian d'une Beta symétrique = 0.5", abs(BS.quantile_beta(0.5, 5, 5) - 0.5) < 1e-3)
check("betai(quantile)=p (inverse cohérent)", abs(BS.betai(3, 4, BS.quantile_beta(0.7, 3, 4)) - 0.7) < 1e-3)
# Beta(1,1) uniforme -> quantile 0.9 = 0.9
check("Beta(1,1) quantile 0.9 = 0.9", abs(BS.quantile_beta(0.9, 1, 1) - 0.9) < 1e-3)

print(f"\nBAYES SÉQUENTIEL VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
