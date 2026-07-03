"""
VALIDATION de la PRÉVISION MULTIVARIÉE VAR (serie_multivariee.py) — jugée par calibration.py. Sur un VAR(1) 3-D à
innovations CORRÉLÉES : (1) l'incertitude de prévision CROÎT avec l'horizon ; (2) la RÉGION CONJOINTE (ellipsoïde de
Mahalanobis, seuil conforme) couvre l'événement conjoint ≈ nominal ; (3) la BOÎTE d'intervalles INDÉPENDANTS (chaque
composante au niveau nominal) SOUS-couvre le conjoint (sur-confiante par multiplicité/corrélation). Le VAR recouvre A.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import serie_multivariee as S
from serie_multivariee import ESTIMATION, ABSTENTION
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


# --- Processus VRAI : VAR(1) 3-D stable, innovations corrélées via un facteur commun ---
A = [[0.4, 0.1, 0.0],
     [0.0, 0.3, 0.1],
     [0.1, 0.0, 0.2]]
c = [0.2, -0.1, 0.3]


def innov(rng):
    f = rng.gauss(0, 0.7)                              # facteur commun -> corrélation
    return [f + rng.gauss(0, 0.5), f + rng.gauss(0, 0.5), -0.5 * f + rng.gauss(0, 0.5)]


def avance(x, e):
    return [c[i] + sum(A[i][k] * x[k] for k in range(3)) + e[i] for i in range(3)]


def simule(rng, n, x0=None):
    x = x0 or [0.0, 0.0, 0.0]
    out = []
    for _ in range(n):
        x = avance(x, innov(rng))
        out.append(x)
    return out


rng = random.Random(5)
serie = simule(rng, 2500)
st, model, _ = S.ajuste(serie)
print("=== Ajustement VAR(1) ===")
err_A = max(abs(model["A"][i][j] - A[i][j]) for i in range(3) for j in range(3))
print(f"   |A_est − A_vrai|_max = {err_A:.3f}")
check("VAR recouvre A (erreur max < 0.1)", err_A < 0.1)

print("=== (1) L'incertitude CROÎT avec l'horizon ===")
tr = []
for h in (1, 2, 4, 8):
    _, cov = S.prevision(model, serie[-1], h)
    tr.append(cov[0][0] + cov[1][1] + cov[2][2])
print(f"   trace(Σ_h) pour h=1,2,4,8 : {[round(t,2) for t in tr]}")
check("trace(Σ_h) strictement croissante en h", all(tr[i] < tr[i + 1] for i in range(len(tr) - 1)))

# --- Erreurs de prévision 1-pas (modèle ESTIMÉ), séparées calib / test ---
def erreurs_un_pas(rng2, n):
    errs = []
    x = serie[-1]
    for _ in range(n):
        e = innov(rng2)
        y = avance(x, e)
        mu, _cov = S.prevision(model, x, 1)
        errs.append([y[i] - mu[i] for i in range(3)])
        x = y
    return errs


rng2 = random.Random(9)
_, Sig1 = S.prevision(model, serie[-1], 1)
Sinv = S._inv(Sig1)
calib = erreurs_un_pas(rng2, 4000)
test = erreurs_un_pas(rng2, 6000)

NOM = 0.90
print("=== (2) RÉGION CONJOINTE (ellipsoïde Mahalanobis, seuil conforme) : couverture conjointe ~ nominal ===")
d2_cal = [S.mahalanobis2(e, [0, 0, 0], Sinv) for e in calib]
seuil = S.seuil_conforme(d2_cal, NOM)
d2_te = [S.mahalanobis2(e, [0, 0, 0], Sinv) for e in test]
inter_e = [(0.0, seuil)] * len(d2_te)
vE, iE = CAL.verdict_couverture(inter_e, d2_te, NOM)
print(f"   couverture ellipsoïde={iE['couverture']:.3f} ({vE})")
check("région conjointe : couverture ~nominal (>=0.87) et NON sur-confiante", iE["couverture"] >= 0.87 and vE != SURCONFIANT)

print("=== (3) BOÎTE indépendante (chaque composante au niveau nominal) : SOUS-couvre le conjoint ===")
demi = S.demi_largeurs_boite(Sig1, NOM)
score_box = [max(abs(e[i]) / demi[i] for i in range(3)) for e in test]    # <=1 ssi dans la boîte
inter_b = [(0.0, 1.0)] * len(score_box)
vB, iB = CAL.verdict_couverture(inter_b, score_box, NOM)
print(f"   couverture boîte indépendante={iB['couverture']:.3f} ({vB})")
check("boîte indépendante : SUR-CONFIANTE sur le conjoint (couverture < nominal)", vB == SURCONFIANT and iB["couverture"] < 0.87)

print("=== Marginale de la boîte OK (le défaut est CONJOINT, pas marginal) ===")
cov_marg = sum(1 for e in test if abs(e[0]) <= demi[0]) / len(test)
print(f"   couverture marginale composante 0 ={cov_marg:.3f}")
check("la boîte couvre bien chaque composante MARGINALEMENT (~0.90)", cov_marg >= 0.87)

print("=== ABSTENTION si série trop courte ===")
st2, _, raison = S.ajuste([[0, 0, 0]] * 10)
print(f"   {st2} : {raison}")
check("ABSTENTION sous N_MIN", st2 == ABSTENTION)

print(f"\nRÉSULTAT serie_multivariee : {ok}/{total}")
assert ok == total
