"""
VALIDATION de l'ESTIMATION DE FERMI (fermi.py) — jugée par calibration.py. Si chaque facteur est un intervalle
`confiance` honnête (log-normal), l'intervalle du PRODUIT couvre la vraie valeur ~`confiance`. + point = moyenne
géométrique, monotonie, variante Monte-Carlo, abstention.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import fermi as F
from fermi import ESTIMATION, ABSTENTION
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


# facteurs (bas, haut) = intervalles `confiance` ; on en déduit la log-normale vraie de chaque facteur.
FACTEURS = [(2.0, 8.0), (0.5, 2.0), (10.0, 100.0), (0.01, 0.05)]


def params_lognormal(b, h, conf):
    z = F._Z[round(conf, 2)]
    mu = (math.log(b) + math.log(h)) / 2.0
    sig = (math.log(h) - math.log(b)) / (2.0 * z)
    return mu, sig


def couverture(conf, M, graine):
    rng = random.Random(graine)
    st, res, _ = F.estime_fermi(FACTEURS, conf)
    assert st == ESTIMATION
    inter = res[1]
    params = [params_lognormal(b, h, conf) for (b, h) in FACTEURS]
    ver = []
    for _ in range(M):
        prod = 1.0
        for (mu, sig) in params:
            prod *= math.exp(rng.gauss(mu, sig))
        ver.append(prod)
    return [inter] * M, ver


print("=== COUVERTURE du PRODUIT @90% : l'intervalle Fermi couvre la vraie valeur ~90% ===")
inter, ver = couverture(0.90, 6000, graine=1)
v, i = CAL.verdict_couverture(inter, ver, 0.90)
print("   ", CAL.formule((v, i), "couverture"))
check(f"Fermi @90% : couverture {i['couverture']:.3f} ∈ [0.86, 0.94] (calibré)", 0.86 <= i["couverture"] <= 0.94)
check("Fermi @90% : NON surconfiant", v != SURCONFIANT)

print("=== COUVERTURE @80% : suit le niveau ===")
inter8, ver8 = couverture(0.80, 6000, graine=2)
v8, i8 = CAL.verdict_couverture(inter8, ver8, 0.80)
check(f"Fermi @80% : couverture {i8['couverture']:.3f} ∈ [0.75, 0.86]", 0.75 <= i8["couverture"] <= 0.86)

print("=== POINT = moyenne géométrique + MONOTONIE ===")
st, res, _ = F.estime_fermi([(1.0, 100.0)], 0.90)         # un facteur : point = √(1·100)=10
check("point d'un facteur = moyenne géométrique (≈10)", abs(res[0] - 10.0) < 1e-6)
# facteurs FIXÉS à 90%, sortie demandée à 90% puis 99% -> doit s'élargir
_, (_, (b90, h90)), _ = F.estime_fermi(FACTEURS, 0.90, conf_facteurs=0.90)
_, (_, (b99, h99)), _ = F.estime_fermi(FACTEURS, 0.99, conf_facteurs=0.90)
check("sortie 99% plus large que 90% (facteurs fixés)", (h99 / b99) > (h90 / b90))

print("=== VARIANTE MONTE-CARLO : couverture calibrée aussi ===")
params = [params_lognormal(b, h, 0.90) for (b, h) in FACTEURS]
tirages = [(lambda r, mu=mu, sig=sig: math.exp(r.gauss(mu, sig))) for (mu, sig) in params]
st, res_mc, _ = F.estime_fermi_mc(tirages, 0.90, n=20000, seed=5)
rng = random.Random(77)
ver_mc = []
for _ in range(5000):
    prod = 1.0
    for (mu, sig) in params:
        prod *= math.exp(rng.gauss(mu, sig))
    ver_mc.append(prod)
v_mc, i_mc = CAL.verdict_couverture([res_mc[1]] * len(ver_mc), ver_mc, 0.90)
check(f"Fermi MC @90% : couverture {i_mc['couverture']:.3f} >= 0.86 et NON surconfiant",
      i_mc["couverture"] >= 0.86 and v_mc != SURCONFIANT)

print("=== ABSTENTION : facteur invalide ===")
check("bas<=0 -> ABSTENTION", F.estime_fermi([(0.0, 1.0)])[0] == ABSTENTION)
check("bas>haut -> ABSTENTION", F.estime_fermi([(5.0, 1.0)])[0] == ABSTENTION)

print(f"\nFERMI VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
