"""
VALIDATION du PROCESSUS GAUSSIEN (processus_gaussien.py) — jugée par calibration.py. Sur une fonction lisse connue
avec un TROU d'échantillonnage, l'intervalle GP couvre ~confiance PARTOUT (l'incertitude épistémique grandit dans le
trou), là où une bande de largeur CONSTANTE sous-couvre dans le trou (sur-confiance épistémique).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import processus_gaussien as G
from processus_gaussien import ESTIMATION, ABSTENTION
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


SIG = 0.2
ELL, SF, SN = 0.7, 1.0, 0.2


def f(x):
    return math.sin(1.5 * x)


def train(rng):
    xs, ys = [], []
    while len(xs) < 40:
        x = rng.uniform(0, 5)
        if 2.0 < x < 3.5:               # TROU d'échantillonnage
            continue
        xs.append(x); ys.append(f(x) + rng.gauss(0, SIG))
    return xs, ys


print("=== Couverture GP : marginale ET dans le TROU ; bande constante sous-couvre le trou ===")
rng = random.Random(1)
inter_m, ver_m = [], []              # marginal (partout)
inter_g, ver_g = [], []              # GP dans le trou
inter_c, ver_c = [], []              # bande CONSTANTE dans le trou
z = G._invnorm(0.95)
for rep in range(200):
    xs, ys = train(rng)
    st, model, _ = G.ajuste(xs, ys, ell=ELL, sigma_f=SF, sigma_n=SN)
    if st != ESTIMATION:
        continue
    # largeur constante = écart-type prédictif en zone dense (x=1), appliquée partout
    _, var_dense = G.gp_predict(model, 1.0)
    w_const = z * math.sqrt(var_dense)
    for _ in range(6):
        xt = rng.uniform(0, 5)
        yt = f(xt) + rng.gauss(0, SIG)
        lo, hi = G.gp_intervalle(model, xt, 0.90)[1]
        inter_m.append((lo, hi)); ver_m.append(yt)
        if 2.0 < xt < 3.5:
            inter_g.append((lo, hi)); ver_g.append(yt)
            mean, _ = G.gp_predict(model, xt)
            inter_c.append((mean - w_const, mean + w_const)); ver_c.append(yt)
vM, iM = CAL.verdict_couverture(inter_m, ver_m, 0.90)
vG, iG = CAL.verdict_couverture(inter_g, ver_g, 0.90)
vC, iC = CAL.verdict_couverture(inter_c, ver_c, 0.90)
print(f"   GP marginal={iM['couverture']:.3f} ({vM}) ; GP trou={iG['couverture']:.3f} ({vG}) ; bande constante trou={iC['couverture']:.3f} ({vC})")
check("GP : couverture marginale ~0.90 (>=0.86) et NON surconfiante", iM["couverture"] >= 0.86 and vM != SURCONFIANT)
check("GP : couverture dans le TROU ~0.90 (>=0.85) et NON surconfiante", iG["couverture"] >= 0.85 and vG != SURCONFIANT)
check("bande de largeur CONSTANTE : SUR-CONFIANTE dans le trou", vC == SURCONFIANT and iC["couverture"] < 0.85)

print("=== L'incertitude GP GRANDIT dans le trou (épistémique) ===")
rng = random.Random(2)
xs, ys = train(rng)
_, model, _ = G.ajuste(xs, ys, ell=ELL, sigma_f=SF, sigma_n=SN)
_, var_dense = G.gp_predict(model, 1.0)
_, var_trou = G.gp_predict(model, 2.75)
print(f"   écart-type dense={math.sqrt(var_dense):.3f} ; trou={math.sqrt(var_trou):.3f}")
check("écart-type GP plus grand dans le trou que dans la zone dense", var_trou > 2 * var_dense)

print("=== GP cohérent : prédiction proche de la vérité en zone DENSE ===")
errs = 0
ntot = 0
for xt in (0.5, 1.0, 4.0, 4.5):
    mean, _ = G.gp_predict(model, xt)
    ntot += 1
    if abs(mean - f(xt)) < 0.3:
        errs += 1
check("GP précis en zone dense (>=3/4 à moins de 0.3)", errs >= 3)

print("=== ABSTENTION si trop peu de points ===")
st, _, raison = G.ajuste([0.0, 1.0, 2.0], [0.0, 1.0, 0.0], ell=ELL, sigma_f=SF, sigma_n=SN)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN points", st == ABSTENTION)

print(f"\nRÉSULTAT processus_gaussien : {ok}/{total}")
assert ok == total
