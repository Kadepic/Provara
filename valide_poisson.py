"""
VALIDATION de l'ESTIMATION POISSON (poisson.py) — jugée par calibration.py. L'IC exact couvre le vrai taux ≥ confiance
(conservateur, jamais sur-confiant) ; les probabilités de comptage sont correctes.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import poisson as P
from poisson import ESTIMATION, ABSTENTION
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


def poisson_tirage(rng, mu):
    """Tirage Poisson (Knuth) pour mu modéré."""
    L = math.exp(-mu)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


print("=== COUVERTURE de l'IC exact (couvre le vrai λ ≥ confiance, conservateur) ===")
for conf in (0.90, 0.95):
    for lam in (2.0, 8.0):
        rng = random.Random(int(conf * 100) + int(lam))
        inter, ver = [], []
        for _ in range(4000):
            k = poisson_tirage(rng, lam)        # exposition = 1
            st, res, _ = P.estime_taux(k, 1.0, conf)
            if st == ESTIMATION:
                inter.append(res[1]); ver.append(lam)
        v, i = CAL.verdict_couverture(inter, ver, conf)
        print(f"   conf={conf}, λ={lam} : couverture {i['couverture']:.3f}")
        check(f"λ={lam} conf={conf} : couverture {i['couverture']:.3f} >= {conf}−0.02 et NON surconfiant",
              i["couverture"] >= conf - 0.02 and v != SURCONFIANT)

print("=== λ̂ ≈ λ (estimation ponctuelle) ===")
rng = random.Random(5)
ks = [poisson_tirage(rng, 4.0) for _ in range(20000)]
check(f"moyenne des comptages ≈ 4 ({sum(ks)/len(ks):.3f})", abs(sum(ks) / len(ks) - 4.0) < 0.1)

print("=== proba_compte : somme ≈ 1 et ≈ fréquence empirique ===")
s = sum(P.proba_compte(4.0, 1.0, k) for k in range(40))
check(f"Σ P(N=k) ≈ 1 ({s:.4f})", abs(s - 1.0) < 1e-4)
freq3 = sum(1 for k in ks if k == 3) / len(ks)
check(f"P(N=3) ≈ fréquence empirique ({P.proba_compte(4.0,1.0,3):.3f} vs {freq3:.3f})",
      abs(P.proba_compte(4.0, 1.0, 3) - freq3) < 0.02)

print("=== proba_au_moins : cohérence ===")
check("P(N≥0) = 1", P.proba_au_moins(3.0, 1.0, 0) == 1.0)
check("P(N≥k) décroît en k", P.proba_au_moins(3.0, 1.0, 5) < P.proba_au_moins(3.0, 1.0, 2))
freq_ge5 = sum(1 for k in ks if k >= 5) / len(ks)
check(f"P(N≥5 | λ=4) ≈ empirique ({P.proba_au_moins(4.0,1.0,5):.3f} vs {freq_ge5:.3f})",
      abs(P.proba_au_moins(4.0, 1.0, 5) - freq_ge5) < 0.02)

print("=== cas k=0 + χ² quantile + ABSTENTION ===")
st, res, _ = P.estime_taux(0, 100.0, 0.95)
check("k=0 : borne basse = 0", res[1][0] == 0.0)
check("k=0 : borne haute > 0", res[1][1] > 0.0)
check("χ²_quantile(0.95, 1) ≈ 3.841", abs(P._chi2_quantile(0.95, 1) - 3.841) < 0.02)
check("χ²_quantile(0.5, 4) ≈ 3.357 (médiane)", abs(P._chi2_quantile(0.5, 4) - 3.357) < 0.05)
check("exposition ≤ 0 -> ABSTENTION", P.estime_taux(3, 0.0)[0] == ABSTENTION)

print(f"\nPOISSON VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
