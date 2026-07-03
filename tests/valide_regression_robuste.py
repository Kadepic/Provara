"""
VALIDATION de la RÉGRESSION ROBUSTE (regression_robuste.py) — jugée par calibration.py. Sous contamination à levier
connue, l'IC bootstrap de la pente de Huber COUVRE la vraie pente ~confiance et résiste au biais, là où OLS est
SUR-CONFIANT (sous-couvre) et sa pente est tordue. Sans contamination, Huber ≈ OLS (aucun prix payé).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import regression_robuste as R
from regression_robuste import ESTIMATION, ABSTENTION
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


A, B, SIG = 1.0, 2.0, 0.4
PS, OFF, N = 0.10, -5.0, 120     # outliers à LEVIER : proba 0..PS croît avec x, décalage négatif -> biaise OLS


def jeu(rng, contamine=True):
    xs, ys = [], []
    for _ in range(N):
        xv = rng.uniform(0, 5)
        xs.append(xv)
        if contamine and rng.random() < PS * (xv / 5.0):
            ys.append(A + B * xv + rng.gauss(0, SIG) + OFF)
        else:
            ys.append(A + B * xv + rng.gauss(0, SIG))
    return xs, ys


print("=== COUVERTURE sous contamination : Huber calibré, OLS SUR-CONFIANT ===")
rng = random.Random(7)
ih, vh, io, vo = [], [], [], []
bh, bo = [], []
for k in range(250):
    xs, ys = jeu(rng, True)
    sh, rh, _ = R.huber_slope_ic(xs, ys, 0.90, n_boot=200, seed=k)
    so, ro, _ = R.ols_slope_ic(xs, ys, 0.90)
    if sh == ESTIMATION:
        ih.append(rh[1]); vh.append(B); bh.append(abs(rh[0] - B))
    if so == ESTIMATION:
        io.append(ro[1]); vo.append(B); bo.append(abs(ro[0] - B))
vH, iH = CAL.verdict_couverture(ih, vh, 0.90)
vO, iO = CAL.verdict_couverture(io, vo, 0.90)
mbh, mbo = sum(bh) / len(bh), sum(bo) / len(bo)
print(f"   Huber couverture={iH['couverture']:.3f} ({vH}) biais={mbh:.3f} ; OLS couverture={iO['couverture']:.3f} ({vO}) biais={mbo:.3f}")
check("Huber CI calibré (couverture >= 0.84) et NON surconfiant", iH["couverture"] >= 0.84 and vH != SURCONFIANT)
check("OLS SUR-CONFIANT (sous-couvre nettement, < 0.75)", vO == SURCONFIANT and iO["couverture"] < 0.75)

print("=== Huber RÉSISTE au biais (point estimate) là où OLS est tordu ===")
check("biais de la pente Huber < moitié du biais OLS", mbh < mbo / 2)

print("=== Sans contamination : Huber ≈ OLS (aucun prix payé) ===")
rng = random.Random(3)
ecarts, cov_h = [], 0
n_h = 0
for k in range(120):
    xs, ys = jeu(rng, False)
    sh, rh, _ = R.huber_slope_ic(xs, ys, 0.90, n_boot=200, seed=k)
    bo_fit = R.ols(xs, ys)
    if sh == ESTIMATION and bo_fit is not None:
        ecarts.append(abs(rh[0] - bo_fit[1]))
        n_h += 1; cov_h += (rh[1][0] <= B <= rh[1][1])
ec = sum(ecarts) / len(ecarts)
cov_h /= n_h
print(f"   |pente_Huber − pente_OLS| moyen={ec:.4f} ; Huber couverture (propre)={cov_h:.3f}")
check("sans contamination Huber ≈ OLS (écart moyen < 0.05)", ec < 0.05)
check("Huber reste calibré sans contamination (couverture >= 0.85)", cov_h >= 0.85)

print("=== ABSTENTION honnête si trop peu de points ===")
st, _, raison = R.huber_slope_ic([0, 1, 2, 3, 4], [1, 3, 5, 7, 9], 0.90)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN points", st == ABSTENTION)

print(f"\nRÉSULTAT regression_robuste : {ok}/{total}")
assert ok == total
