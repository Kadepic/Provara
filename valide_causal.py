"""
VALIDATION de l'INFÉRENCE CAUSALE (causal.py) — jugée par calibration.py. En essai randomisé, la diff de moyennes
couvre le vrai ATE ; sous CONFUSION, elle sous-couvre (SURCONFIANT) alors que l'IPW le corrige et couvre ~confiance.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import causal as C
from causal import ESTIMATION, ABSTENTION
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


def sig(x):
    return 1.0 / (1.0 + math.exp(-x))


ATE_VRAI = 2.0


def donnees_confondues(n, rng):
    """X confond : propension sig(0.8X), résultat 2X + 2·T + bruit (effet causal +2). Renvoie (y, t, e)."""
    y, t, e = [], [], []
    for _ in range(n):
        x = rng.gauss(0, 1)
        prop = sig(0.8 * x)
        ti = 1 if rng.random() < prop else 0
        yi = 2.0 * x + ATE_VRAI * ti + rng.gauss(0, 1)
        y.append(yi); t.append(ti); e.append(prop)
    return y, t, e


def donnees_randomisees(n, rng):
    """Randomisé : T tiré à pile ou face (indépendant de X) -> pas de confusion."""
    y, t, e = [], [], []
    for _ in range(n):
        x = rng.gauss(0, 1)
        ti = 1 if rng.random() < 0.5 else 0
        yi = 2.0 * x + ATE_VRAI * ti + rng.gauss(0, 1)
        y.append(yi); t.append(ti); e.append(0.5)
    return y, t, e


print("=== RANDOMISÉ : diff de moyennes couvre le vrai ATE ~90% ===")
inter, ver = [], []
rng = random.Random(1)
for t_ in range(700):
    y, tr, e = donnees_randomisees(400, rng)
    yt = [y[i] for i in range(len(y)) if tr[i]]
    yc = [y[i] for i in range(len(y)) if not tr[i]]
    st, res, _ = C.ate_diff_moyennes(yt, yc, 0.90, n_boot=200, seed=t_)
    if st == ESTIMATION:
        inter.append(res[1]); ver.append(ATE_VRAI)
v, i = CAL.verdict_couverture(inter, ver, 0.90)
check(f"randomisé : couverture {i['couverture']:.3f} >= 0.86 et NON surconfiant", i["couverture"] >= 0.86 and v != SURCONFIANT)

print("=== CONFUSION : diff NAÏVE biaisée (sous-couvre, SURCONFIANT) ; IPW corrige (couvre) ===")
inter_naif, inter_ipw, ver = [], [], []
rng = random.Random(2)
ates_ipw = []
for t_ in range(700):
    y, tr, e = donnees_confondues(400, rng)
    yt = [y[i] for i in range(len(y)) if tr[i]]
    yc = [y[i] for i in range(len(y)) if not tr[i]]
    st_n, res_n, _ = C.ate_diff_moyennes(yt, yc, 0.90, n_boot=200, seed=t_)
    st_i, res_i, _ = C.ate_ipw(y, tr, e, 0.90, n_boot=200, seed=t_)
    if st_n == ESTIMATION and st_i == ESTIMATION:
        inter_naif.append(res_n[1]); inter_ipw.append(res_i[1]); ver.append(ATE_VRAI)
        ates_ipw.append(res_i[0])
vn, in_ = CAL.verdict_couverture(inter_naif, ver, 0.90)
vi, ii = CAL.verdict_couverture(inter_ipw, ver, 0.90)
print(f"   naïf couverture={in_['couverture']:.3f} ({vn}) ; IPW couverture={ii['couverture']:.3f} ({vi})")
check(f"naïf sous confusion : SOUS-COUVRE {in_['couverture']:.3f} -> SURCONFIANT", vn == SURCONFIANT)
check(f"IPW sous confusion : couverture {ii['couverture']:.3f} >= 0.85 et NON surconfiant",
      ii["couverture"] >= 0.85 and vi != SURCONFIANT)
moy_ipw = sum(ates_ipw) / len(ates_ipw)
check(f"IPW ~sans biais (moyenne {moy_ipw:.2f} ≈ {ATE_VRAI})", abs(moy_ipw - ATE_VRAI) < 0.15)

print("=== ABSTENTION + parole ===")
check("propension dégénérée (≈0/1) -> ABSTENTION",
      C.ate_ipw([1.0] * 20, [1] * 10 + [0] * 10, [0.001] * 20)[0] == ABSTENTION)
check("trop peu -> ABSTENTION", C.ate_diff_moyennes([1, 2], [3, 4])[0] == ABSTENTION)
# IC excluant 0 -> affirme un effet ; incluant 0 -> prudence
ph = C.formule((ESTIMATION, (2.0, (1.0, 3.0)), 0.90))
check("parole effet net : 'POSITIF'", "POSITIF" in ph)
ph0 = C.formule((ESTIMATION, (0.1, (-0.5, 0.7)), 0.90))
check("parole IC inclut 0 : 'inclut 0'", "inclut 0" in ph0)

print(f"\nCAUSAL VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
