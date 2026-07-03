"""
VALIDATION du CQR (conformal_quantile.py) — jugé par calibration.py. Bande de quantiles TROP ÉTROITE (sous-couvre) :
le CQR RESTAURE la couverture ≥ 1−α tout en gardant l'ADAPTIVITÉ (largeur qui suit la difficulté), là où la bande
brute est SURCONFIANTE.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import conformal_quantile as CQ
from conformal_quantile import ESTIMATION, ABSTENTION
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


def sigma(x):
    return 0.3 + abs(x)


def bande(x):
    """Bande de quantiles prédite TROP ÉTROITE (facteur 0.8 sur ±1σ) -> sous-couvre sans correction."""
    return (-0.8 * sigma(x), 0.8 * sigma(x))


def calibre(n, alpha, graine):
    rng = random.Random(graine)
    xs = [rng.gauss(0, 1.2) for _ in range(n)]
    ys = [rng.gauss(0, sigma(x)) for x in xs]
    qb = [bande(x)[0] for x in xs]
    qh = [bande(x)[1] for x in xs]
    return CQ.ajuste_cqr(qb, qh, ys, alpha), rng


print("=== BANDE BRUTE (sans CQR) -> SOUS-COUVRE (SURCONFIANT) ; CQR -> couverture restaurée ===")
Q, rng = calibre(2000, 0.10, graine=1)
print(f"   correction Q = {Q:.3f}")
inter_cqr, inter_brut, ver = [], [], []
for _ in range(5000):
    x = rng.gauss(0, 1.2)
    qb, qh = bande(x)
    inter_brut.append((qb, qh))                       # bande brute (Q=0)
    inter_cqr.append((qb - Q, qh + Q))
    ver.append(rng.gauss(0, sigma(x)))
vb, ib = CAL.verdict_couverture(inter_brut, ver, 0.90)
vc, ic = CAL.verdict_couverture(inter_cqr, ver, 0.90)
print("   brute :", CAL.formule((vb, ib), "couverture"))
print("   CQR   :", CAL.formule((vc, ic), "couverture"))
check(f"bande brute -> SOUS-COUVRE {ib['couverture']:.3f} -> SURCONFIANT", vb == SURCONFIANT)
check(f"CQR -> couverture {ic['couverture']:.3f} >= 0.88 et NON surconfiant", ic["couverture"] >= 0.88 and vc != SURCONFIANT)

print("=== ADAPTIVITÉ : largeur(zone dure) > largeur(zone facile) ===")
st_f, (bf, hf), _ = CQ.intervalle_cqr(*bande(0.1), Q)
st_d, (bd, hd), _ = CQ.intervalle_cqr(*bande(3.0), Q)
check(f"largeur dur ({hd-bd:.2f}) > facile ({hf-bf:.2f})", (hd - bd) > 1.5 * (hf - bf))

print("=== ADAPTIVITÉ : la couverture conditionnelle du CQR est PLUS UNIFORME que la largeur constante ===")
# CQR ne GARANTIT que le marginal (≥1−α) ; son adaptivité rend la couverture conditionnelle plus ÉQUILIBRÉE entre
# régimes qu'un conforme à largeur CONSTANTE (qui sur-couvre le facile et sous-couvre le dur). On le mesure.
import conformal as CF
rng3 = random.Random(99)
# largeur constante : quantile conforme des |y| marginaux sur la même calibration
xs_c = [rng3.gauss(0, 1.2) for _ in range(2000)]
abs_res = [abs(rng3.gauss(0, sigma(x))) for x in xs_c]
q_const = CF.quantile_conforme(abs_res, 0.10)
regions = [0.0, 0.5, 1.0, 2.0]
cov_cqr, cov_const = [], []
for xfix in regions:
    rng2 = random.Random(200 + int(xfix * 10))
    qb, qh = bande(xfix)
    ver2 = [rng2.gauss(0, sigma(xfix)) for _ in range(4000)]
    cov_cqr.append(sum(1 for y in ver2 if qb - Q <= y <= qh + Q) / len(ver2))
    cov_const.append(sum(1 for y in ver2 if -q_const <= y <= q_const) / len(ver2))
spread_cqr = max(cov_cqr) - min(cov_cqr)
spread_const = max(cov_const) - min(cov_const)
print(f"   couverture par région  CQR={[round(c,2) for c in cov_cqr]} (spread {spread_cqr:.2f})")
print(f"                       const={[round(c,2) for c in cov_const]} (spread {spread_const:.2f})")
check(f"CQR plus uniforme entre régimes (spread {spread_cqr:.2f} < largeur constante {spread_const:.2f})",
      spread_cqr < spread_const)

print("=== MONOTONIE + cas limites ===")
Q90, _ = calibre(2000, 0.10, graine=7)
Q99, _ = calibre(2000, 0.01, graine=7)
check("correction 99% >= correction 90%", Q99 >= Q90)
check("trop peu -> correction None -> ABSTENTION", CQ.intervalle_cqr(-1, 1, CQ.ajuste_cqr([0], [1], [0.5]))[0] == ABSTENTION)
check("scores_cqr : y hors bande -> E>0 ; y dans bande -> E<0",
      CQ.scores_cqr([0], [2], [3])[0] > 0 and CQ.scores_cqr([0], [2], [1])[0] < 0)

print(f"\nCQR VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
