"""
VALIDATION des ERREURS-EN-VARIABLES (erreurs_variables.py) — jugée par calibration.py. Quand x est mesuré avec une
erreur de variance connue, l'IC de la pente CORRIGÉE (dé-atténuée) couvre la vraie pente ~confiance, là où l'IC OLS
naïf SOUS-couvre (centré sur la pente atténuée vers zéro).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import erreurs_variables as E
from erreurs_variables import ESTIMATION, ABSTENTION
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


A, B, SU, SE = 1.0, 2.0, 1.0, 0.5      # y = 1 + 2x + N(0,0.5) ; x mesuré avec erreur d'écart-type 1


def echantillon(rng, n=400):
    xs_obs, ys = [], []
    for _ in range(n):
        xt = rng.uniform(0, 5)
        ys.append(A + B * xt + rng.gauss(0, SE))
        xs_obs.append(xt + rng.gauss(0, SU))
    return xs_obs, ys


print("=== Couverture de la vraie pente : CORRIGÉE calibrée, OLS naïf SUR-CONFIANT ===")
rng = random.Random(1)
ic, vc, io, vo = [], [], [], []
bc, bo = [], []
for k in range(300):
    xs, ys = echantillon(rng)
    cc = E.pente_corrigee_ic(xs, ys, SU * SU, 0.90, n_boot=300, seed=k)
    oo = E.pente_ols_ic(xs, ys, 0.90)
    if cc[0] == ESTIMATION:
        ic.append(cc[1][1]); vc.append(B); bc.append(abs(cc[1][0] - B))
    if oo[0] == ESTIMATION:
        io.append(oo[1][1]); vo.append(B); bo.append(abs(oo[1][0] - B))
vC, iC = CAL.verdict_couverture(ic, vc, 0.90)
vO, iO = CAL.verdict_couverture(io, vo, 0.90)
mbc, mbo = sum(bc) / len(bc), sum(bo) / len(bo)
print(f"   CORRIGÉE={iC['couverture']:.3f} ({vC}) biais={mbc:.3f} ; OLS={iO['couverture']:.3f} ({vO}) biais={mbo:.3f}")
check("pente corrigée : couverture ~0.90 (>=0.85) et NON surconfiante", iC["couverture"] >= 0.85 and vC != SURCONFIANT)
check("OLS naïf : SUR-CONFIANT (sous-couvre la vraie pente, <0.40)", vO == SURCONFIANT and iO["couverture"] < 0.40)

print("=== La correction réduit fortement le biais (atténuation) ===")
print(f"   biais OLS={mbo:.3f} ; biais corrigé={mbc:.3f}")
check("biais corrigé < quart du biais OLS", mbc < mbo / 4)

print("=== Sans erreur de mesure (σ_u=0) : corrigée ≈ OLS (aucun prix payé) ===")
rng = random.Random(2)
xs, ys = [], []
for _ in range(200):
    xt = rng.uniform(0, 5)
    ys.append(A + B * xt + rng.gauss(0, SE)); xs.append(xt)
b_ols = E.pente_ols(xs, ys)
b_cor = E.pente_corrigee(xs, ys, 0.0)
print(f"   OLS={b_ols:.3f} ; corrigée(σ_u=0)={b_cor:.3f}")
check("σ_u=0 -> corrigée = OLS", abs(b_cor - b_ols) < 1e-9)

print("=== ABSTENTION si l'erreur de mesure dépasse la variance observée (fiabilité ≤ 0) ===")
rng = random.Random(3)
xs, ys = echantillon(rng, 60)
st, _, raison = E.pente_corrigee_ic(xs, ys, 100.0, 0.90)   # σ_u² énorme
print(f"   {st} : {raison}")
check("ABSTENTION si fiabilité ≤ 0", st == ABSTENTION)

print(f"\nRÉSULTAT erreurs_variables : {ok}/{total}")
assert ok == total
