"""
VALIDATION de la RÉGRESSION QUANTILE (quantile_regression.py) — jugée par calibration.py. Sous hétéroscédasticité
connue (σ croît avec x) : la bande quantile [q0.05, q0.95] couvre ~0.90 MARGINALEMENT et CONDITIONNELLEMENT (même
dans la zone à forte variance), les niveaux pinball sont calibrés (P(y≤q_τ)≈τ), là où la bande HOMOSCÉDASTIQUE
(OLS±zσ) SOUS-couvre dans la zone à forte variance (sur-confiance conditionnelle).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import quantile_regression as Q
from quantile_regression import ESTIMATION, ABSTENTION
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


A, B = 1.0, 2.0


def echantillon(rng, n):
    xs, ys = [], []
    for _ in range(n):
        x = rng.uniform(0, 5)
        sigma = 0.3 + 0.6 * x                 # dispersion CROÎT avec x
        xs.append(x); ys.append(A + B * x + rng.gauss(0, sigma))
    return xs, ys


rng = random.Random(1)
xtr, ytr = echantillon(rng, 500)
xte, yte = echantillon(rng, 5000)

print("=== Ajustement des quantiles (une fois) ===")
coef = {}
for tau in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95):
    coef[tau] = Q.quantile_fit(xtr, ytr, tau)
print(f"   médiane pente={coef[0.5][1]:.2f} (vraie {B})")
check("médiane ~ vraie pente (|pente−2|<0.3)", abs(coef[0.5][1] - B) < 0.3)

print("=== Couverture MARGINALE de la bande [q0.05, q0.95] ~ 0.90 ===")
inter, ver = [], []
for i in range(len(xte)):
    inter.append((Q.predit(coef[0.05], xte[i]), Q.predit(coef[0.95], xte[i]))); ver.append(yte[i])
vM, iM = CAL.verdict_couverture(inter, ver, 0.90)
print(f"   couverture marginale={iM['couverture']:.3f} ({vM})")
check("bande quantile : couverture marginale ~0.90 (>=0.86) et NON surconfiante", iM["couverture"] >= 0.86 and vM != SURCONFIANT)

print("=== Couverture CONDITIONNELLE (zone à FORTE variance x>3.5) : quantile tient, homoscédastique SOUS-couvre ===")
hom = Q.bande_homoscedastique(xtr, ytr, 0.90)        # (a, b, demi)
iq, vq, ih, vh = [], [], [], []
for i in range(len(xte)):
    if xte[i] > 3.5:
        iq.append((Q.predit(coef[0.05], xte[i]), Q.predit(coef[0.95], xte[i]))); vq.append(yte[i])
        c = hom[0] + hom[1] * xte[i]
        ih.append((c - hom[2], c + hom[2])); vh.append(yte[i])
vQc, iQc = CAL.verdict_couverture(iq, vq, 0.90)
vHc, iHc = CAL.verdict_couverture(ih, vh, 0.90)
print(f"   quantile (cond.)={iQc['couverture']:.3f} ({vQc}) ; homoscédastique (cond.)={iHc['couverture']:.3f} ({vHc})")
check("quantile : couverture conditionnelle ~0.90 (>=0.85) et NON surconfiante", iQc["couverture"] >= 0.85 and vQc != SURCONFIANT)
check("homoscédastique : SUR-CONFIANT dans la zone à forte variance", vHc == SURCONFIANT and iHc["couverture"] < 0.85)

print("=== Calibration des NIVEAUX pinball : P(y ≤ q_τ(x)) ≈ τ ===")
conf, just = [], []
for tau in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95):
    for i in range(len(xte)):
        conf.append(tau)
        just.append(1.0 if yte[i] <= Q.predit(coef[tau], xte[i]) else 0.0)
vL, iL = CAL.est_calibre(conf, just, n_bins=7)
print(f"   niveaux pinball : verdict={vL}, ECE={iL['ece']:.3f}")
check("niveaux quantiles calibrés (non surconfiant, ECE<0.05)", vL != SURCONFIANT and iL["ece"] < 0.05)

print("=== ABSTENTION si trop peu de points ===")
st, _, raison = Q.bande_quantile([0, 1, 2, 3, 4], [0, 1, 2, 3, 4], 0.05, 0.95)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN points", st == ABSTENTION)

print(f"\nRÉSULTAT quantile_regression : {ok}/{total}")
assert ok == total
