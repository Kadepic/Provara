"""
VALIDATION des DONNÉES MANQUANTES (donnees_manquantes.py) — jugée par calibration.py. Sous MAR (manque lié à une
covariable), l'imputation MULTIPLE de Rubin couvre la vraie moyenne ~confiance, l'imputation SIMPLE sous-couvre
(surconfiante) et le CAS COMPLET est biaisé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import donnees_manquantes as D
from donnees_manquantes import ESTIMATION, ABSTENTION
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


A, B, SIG = 1.0, 2.0, 0.5     # y = 1 + 2x + N(0,0.5) ; x ~ U(0,1) ; vraie moyenne(y) = 2.0
VRAI = A + B * 0.5
N = 300


def echantillon(rng):
    x, y = [], []
    for _ in range(N):
        xi = rng.random()
        x.append(xi); y.append(A + B * xi + rng.gauss(0, SIG))
    y_obs = [yi if rng.random() > 0.2 + 0.5 * xi else None for xi, yi in zip(x, y)]   # MAR sur x
    return x, y_obs


print("=== Cas dégénéré SANS manquant -> ABSTENTION (imputation multiple sans objet) ===")
rng = random.Random(3)
x = [rng.random() for _ in range(N)]
y_obs = [A + B * xi + rng.gauss(0, SIG) for xi in x]
st, _, raison = D.imputation_multiple(x, y_obs, m=20, seed=0)
print(f"   {st} : {raison}")
check("ABSTENTION quand aucune valeur ne manque", st == ABSTENTION)

print("=== ABSTENTION honnête si trop peu d'observés ===")
st, _, raison = D.imputation_multiple(list(range(10)), [1.0, None, None, 2.0, None, None, 3.0, None, None, None], m=20)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN_OBS observés", st == ABSTENTION)

print("=== COUVERTURE : imputation MULTIPLE (Rubin) couvre la vraie moyenne ~confiance ===")
rng = random.Random(1)
im, vm, iss, vss = [], [], [], []
cov_cc, n_cc = 0, 0
for k in range(350):
    x, y_obs = echantillon(rng)
    st, res, _ = D.imputation_multiple(x, y_obs, m=20, seed=k)
    if st == ESTIMATION:
        im.append(res[1]); vm.append(VRAI)
    si = D.imputation_simple(x, y_obs)
    if si:
        iss.append(si[1]); vss.append(VRAI)
    cc = D.cas_complet(x, y_obs)
    if cc:
        n_cc += 1; cov_cc += (cc[1][0] <= VRAI <= cc[1][1])
vMI, iMI = CAL.verdict_couverture(im, vm, 0.95)
vSI, iSI = CAL.verdict_couverture(iss, vss, 0.95)
cov_cc /= n_cc
print(f"   MI couverture={iMI['couverture']:.3f} ({vMI}) ; SIMPLE={iSI['couverture']:.3f} ({vSI}) ; CAS-COMPLET={cov_cc:.3f}")
check("MI couvre ~nominal (>=0.92) et N'EST PAS surconfiant", iMI["couverture"] >= 0.92 and vMI != SURCONFIANT)
check("IMPUTATION SIMPLE est SUR-CONFIANTE (sous-couvre)", vSI == SURCONFIANT)
check("CAS COMPLET fortement BIAISÉ sous MAR (couverture < 0.55)", cov_cc < 0.55)

print("=== L'IC de Rubin est PLUS LARGE que l'imputation simple (incertitude d'imputation ajoutée) ===")
rng = random.Random(2)
larg_mi, larg_si = [], []
for k in range(120):
    x, y_obs = echantillon(rng)
    st, res, _ = D.imputation_multiple(x, y_obs, m=20, seed=1000 + k)
    si = D.imputation_simple(x, y_obs)
    if st == ESTIMATION and si:
        larg_mi.append(res[1][1] - res[1][0]); larg_si.append(si[1][1] - si[1][0])
rmi, rsi = sum(larg_mi) / len(larg_mi), sum(larg_si) / len(larg_si)
print(f"   largeur IC : MI={rmi:.4f}  simple={rsi:.4f}")
check("MI strictement plus large que l'imputation simple", rmi > rsi * 1.05)

print(f"\nRÉSULTAT donnees_manquantes : {ok}/{total}")
assert ok == total
