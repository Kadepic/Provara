"""
VALIDATION du TEST DE CALIBRATION (test_calibration.py). Invariant : ERREUR DE TYPE I CONTRÔLÉE (sous H0 calibré, on
rejette ~α du temps) + PUISSANCE (la vraie mal-calibration est rejetée). p-valeur ~uniforme sous H0.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import test_calibration as TC
from test_calibration import CALIBRE, NON_CALIBRE, ABSTENTION

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


def durcis(p, k):
    return p ** k / (p ** k + (1 - p) ** k)


def dataset(n, graine, k=1.0):
    """Forecaster : probas p ~ U(0,1) ; issue ~ Bernoulli(durcis(p,k)). k=1 -> calibré ; k≠1 -> mal calibré."""
    rng = random.Random(graine)
    p = [rng.random() for _ in range(n)]
    y = [1 if rng.random() < durcis(pi, k) else 0 for pi in p]
    return p, y


for methode in ("spiegelhalter", "hosmer"):
    print(f"=== {methode.upper()} : TYPE I sous H0 (calibré) ≈ α ===")
    M = 400
    rejets = 0
    for s in range(M):
        p, y = dataset(800, graine=s, k=1.0)
        if TC.est_calibre_test(p, y, 0.05, methode)[0] == NON_CALIBRE:
            rejets += 1
    taux = rejets / M
    print(f"   taux de rejet sous H0 = {taux:.3f} (cible ~0.05)")
    check(f"{methode} : type I contrôlé ({taux:.3f} <= 0.09)", taux <= 0.09)

    print(f"=== {methode.upper()} : PUISSANCE sur mal-calibration (sur-confiance) ===")
    det = 0
    for s in range(200):
        p, y = dataset(800, graine=1000 + s, k=2.5)
        if TC.est_calibre_test(p, y, 0.05, methode)[0] == NON_CALIBRE:
            det += 1
    pui = det / 200
    print(f"   puissance = {pui:.3f}")
    check(f"{methode} : puissance >= 0.9 ({pui:.3f})", pui >= 0.9)

print("=== p-VALEUR ~UNIFORME sous H0 (Spiegelhalter) ===")
ps = []
for s in range(600):
    p, y = dataset(600, graine=5000 + s, k=1.0)
    ps.append(TC.test_spiegelhalter(p, y)[1])
moy = sum(ps) / len(ps)
frac05 = sum(1 for v in ps if v < 0.05) / len(ps)
check(f"moyenne p-valeur ≈ 0.5 ({moy:.3f})", 0.45 <= moy <= 0.55)
check(f"fraction p<0.05 ≈ 0.05 ({frac05:.3f} <= 0.09)", frac05 <= 0.09)

print("=== fonctions internes + ABSTENTION ===")
check("_phi(0) = 0.5", abs(TC._phi(0.0) - 0.5) < 1e-9)
check("_phi(1.96) ≈ 0.975", abs(TC._phi(1.96) - 0.975) < 1e-3)
check("_chi2_sf(df, df) ∈ (0,1)", 0.0 < TC._chi2_sf(10, 10) < 1.0)
check("χ² sf décroît avec la statistique", TC._chi2_sf(30, 10) < TC._chi2_sf(5, 10))
check("n<30 -> ABSTENTION", TC.est_calibre_test([0.5] * 10, [0] * 10)[0] == ABSTENTION)
# direction : un sur-confiant net est rejeté
p, y = dataset(1500, graine=42, k=3.0)
check("sur-confiance nette -> NON_CALIBRE", TC.est_calibre_test(p, y)[0] == NON_CALIBRE)

print(f"\nTEST CALIBRATION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
