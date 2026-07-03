"""
VALIDATION de l'OPTIMISATION BAYÉSIENNE (optimisation_bayesienne.py) — jugée par calibration.py. (1) L'incertitude du
surrogate (processus gaussien) est CALIBRÉE : la couverture de ses intervalles ≈ nominal (non sur-confiante) — c'est ce
qui rend l'exploration honnête. (2) Sur des fonctions à optimum local TROMPEUR (départ groupé près de la bosse locale),
l'acquisition UCB/EI atteint le pic GLOBAL alors que la stratégie GLOUTONNE (qui agit comme si la moyenne postérieure
était la vérité = sur-confiance décisionnelle) reste PIÉGÉE. UCB bat le glouton sur la majorité des fonctions tirées.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import optimisation_bayesienne as OB
from optimisation_bayesienne import ESTIMATION, ABSTENTION
import processus_gaussien as GP
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


def f_trompeuse(lx, gx, lh=0.6):
    """Bosse LOCALE en lx (hauteur lh) + pic GLOBAL en gx (hauteur 1.0)."""
    return lambda x: lh * math.exp(-((x - lx) ** 2) / 0.5) + 1.0 * math.exp(-((x - gx) ** 2) / 0.5)


print("=== (1) Incertitude du surrogate CALIBRÉE (couverture ~ nominal, non sur-confiante) ===")
rng = random.Random(3)
f0 = f_trompeuse(2.0, 8.0)
inter, ver = [], []
for _ in range(60):
    xs = [rng.uniform(0, 10) for _ in range(10)]
    ys = [f0(x) + rng.gauss(0, 0.05) for x in xs]
    model = GP.gp_fit(xs, ys, 1.0, 1.0, 0.1)
    if model is None:
        continue
    for _ in range(8):
        xt = rng.uniform(0, 10)
        _, (lo, hi) = GP.gp_intervalle(model, xt, 0.90)
        inter.append((lo, hi)); ver.append(f0(xt))
vCov, iCov = CAL.verdict_couverture(inter, ver, 0.90)
print(f"   couverture surrogate={iCov['couverture']:.3f} ({vCov})")
check("surrogate GP : intervalles calibrés (couverture >=0.85) et NON sur-confiants", iCov["couverture"] >= 0.85 and vCov != SURCONFIANT)

print("=== (2) Cas trompeur, départ près de la bosse locale : UCB trouve le global, glouton piégé ===")
depart = [1.5, 2.0, 2.5]
_, (xu, yu), _ = OB.optimise(f0, 0, 10, n_iter=12, methode="ucb", kappa=2.5, xs_init=depart)
_, (xg, yg), _ = OB.optimise(f0, 0, 10, n_iter=12, methode="glouton", xs_init=depart)
_, (xe, ye), _ = OB.optimise(f0, 0, 10, n_iter=12, methode="ei", xs_init=depart)
print(f"   UCB f={yu:.3f} (x={xu:.2f}) ; EI f={ye:.3f} (x={xe:.2f}) ; Glouton f={yg:.3f} (x={xg:.2f})")
check("UCB atteint le global (f>=0.90)", yu >= 0.90)
check("EI atteint le global (f>=0.90)", ye >= 0.90)
check("Glouton PIÉGÉ près de la bosse locale (f<0.75)", yg < 0.75)
check("UCB et EI battent strictement le glouton", yu > yg and ye > yg)

print("=== (3) Sur 12 fonctions trompeuses tirées : UCB bat le glouton sur la majorité ===")
rng2 = random.Random(11)
ucb_wins = 0
ucb_vals, glo_vals = [], []
N = 12
for _ in range(N):
    lx = rng2.uniform(1.5, 3.5)
    gx = rng2.uniform(6.5, 9.0)
    lh = rng2.uniform(0.55, 0.7)
    f = f_trompeuse(lx, gx, lh)
    dep = [lx - 0.5, lx, lx + 0.5]                # départ groupé sur la bosse LOCALE
    _, (_, yu2), _ = OB.optimise(f, 0, 10, n_iter=12, methode="ucb", kappa=2.5, xs_init=dep)
    _, (_, yg2), _ = OB.optimise(f, 0, 10, n_iter=12, methode="glouton", xs_init=dep)
    ucb_vals.append(yu2); glo_vals.append(yg2)
    if yu2 >= yg2 - 1e-9:
        ucb_wins += 1
moy_u = sum(ucb_vals) / N
moy_g = sum(glo_vals) / N
print(f"   UCB gagne/égale {ucb_wins}/{N} ; moyenne UCB={moy_u:.3f} vs glouton={moy_g:.3f}")
check("UCB >= glouton sur la majorité (>=10/12)", ucb_wins >= 10)
check("UCB meilleur EN MOYENNE que le glouton", moy_u > moy_g + 0.1)

print("=== (4) ABSTENTION si trop peu de points initiaux ===")
st, _, raison = OB.optimise(f0, 0, 10, n_init=2)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_INIT_MIN", st == ABSTENTION)

print(f"\nRÉSULTAT optimisation_bayesienne : {ok}/{total}")
assert ok == total
