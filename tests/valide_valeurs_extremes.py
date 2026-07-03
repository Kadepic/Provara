"""
VALIDATION des VALEURS EXTRÊMES (valeurs_extremes.py) — jugée par calibration.py. Sur une loi de Pareto connue, le
VaR POT couvre la vraie valeur ~confiance et EXTRAPOLE dans la queue là où l'empirique échoue.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import valeurs_extremes as V
from valeurs_extremes import ESTIMATION, ABSTENTION
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


ALPHA = 3.0       # Pareto : P(X>x)=x^-alpha (x>=1)


def pareto(rng, n):
    return [(1.0 - rng.random()) ** (-1.0 / ALPHA) for _ in range(n)]


def vrai_var(p):
    return (1 - p) ** (-1 / ALPHA)


print("=== COUVERTURE du VaR @99% (CI couvre la vraie VaR) ===")
p = 0.99
vrai = vrai_var(p)
inter, ver = [], []
rng = random.Random(1)
for t in range(400):
    d = pareto(rng, 2500)
    st, res, _ = V.var_pot_ic(d, p, 0.90, 0.90, n_boot=300, seed=t)
    if st == ESTIMATION:
        inter.append(res[1]); ver.append(vrai)
v, i = CAL.verdict_couverture(inter, ver, 0.90)
print(f"   vrai VaR={vrai:.2f} ; couverture CI={i['couverture']:.3f}")
check(f"VaR @99% : couverture {i['couverture']:.3f} >= 0.80 et NON surconfiant", i["couverture"] >= 0.80 and v != SURCONFIANT)

print("=== POT EXTRAPOLE là où l'EMPIRIQUE est PLAFONNÉ (p=0.9999, AU-DELÀ des données : (1−p)·n<1) ===")
pe = 0.9999
rng = random.Random(2)
biais_emp, biais_pot = [], []
vrai_e = vrai_var(pe)
for t in range(200):
    d = sorted(pareto(rng, 2000))
    emp = d[min(len(d) - 1, int(pe * len(d)))]         # quantile empirique = MAX (ne peut pas extrapoler)
    pot = V.var_pot(d, pe, 0.90)
    if pot is not None:
        biais_emp.append(emp)
        biais_pot.append(pot)
moy_emp = sum(biais_emp) / len(biais_emp)
moy_pot = sum(biais_pot) / len(biais_pot)
print(f"   vrai VaR(0.9999)={vrai_e:.2f} ; empirique(=max) moyen={moy_emp:.2f} ; POT moyen={moy_pot:.2f}")
check(f"empirique plafonné SOUS la vraie VaR ({moy_emp:.2f} < {vrai_e:.2f}·0.85)", moy_emp < vrai_e * 0.85)
check(f"POT extrapole vers la vraie VaR ({moy_pot:.2f} dans [{vrai_e*0.6:.1f}, {vrai_e*1.6:.1f}])",
      vrai_e * 0.6 <= moy_pot <= vrai_e * 1.6)

print("=== PROBA DE DÉPASSEMENT ≈ vraie probabilité de queue ===")
rng = random.Random(3)
d = pareto(rng, 5000)
x = 5.0
vraie_p = x ** (-ALPHA)              # P(X>5) pour Pareto(3) = 5^-3 = 0.008
est_p = V.proba_depassement(d, x, 0.90)
print(f"   P(X>5) : vrai={vraie_p:.4f} ; estimé={est_p:.4f}")
check(f"proba dépassement proche ({est_p:.4f} ∈ [{vraie_p*0.5:.4f}, {vraie_p*2:.4f}])", vraie_p * 0.5 <= est_p <= vraie_p * 2)

print("=== ξ recouvré ≈ 1/alpha + ABSTENTION ===")
rng = random.Random(4)
d = pareto(rng, 8000)
u = V._seuil(d, 0.90)
dep = [v - u for v in d if v > u]
xi, sigma = V.ajuste_gpd(dep)
check(f"ξ estimé ≈ 1/alpha = {1/ALPHA:.2f} (estimé {xi:.2f})", abs(xi - 1 / ALPHA) < 0.15)
check("trop peu de dépassements -> ABSTENTION", V.var_pot_ic([1.0] * 30 + [2.0] * 5, 0.99)[0] == ABSTENTION)
check("ajuste_gpd trop peu -> None", V.ajuste_gpd([1, 2, 3]) is None)

print(f"\nVALEURS EXTRÊMES VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
