"""
VALIDATION du JACKKNIFE+ (conformal_jackknife.py) — jugé par calibration.py. Couverture ≥ 1−α (et ≥ 1−2α garantie)
SANS split de calibration, y compris en petit échantillon ; jamais sur-confiant.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import conformal_jackknife as J
from conformal_jackknife import ESTIMATION, ABSTENTION
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


def _erreur(f):
    try:
        f()
        return False
    except Exception:
        return True


def couverture(loi, n, alpha, M, graine):
    rng = random.Random(graine)
    inter, ver = [], []
    for _ in range(M):
        ys = [loi(rng) for _ in range(n)]
        st, it, _ = J.jackknife_plus_moyenne(ys, alpha)
        if st == ESTIMATION:
            inter.append(it)
            ver.append(loi(rng))
    return inter, ver


print("=== COUVERTURE @90% (n=40) : ≈ nominal, NON surconfiant ===")
inter, ver = couverture(lambda r: r.gauss(10, 2), 40, 0.10, 4000, graine=1)
v, i = CAL.verdict_couverture(inter, ver, 0.90)
print("   ", CAL.formule((v, i), "couverture"))
check(f"jackknife+ @90% : couverture {i['couverture']:.3f} >= 0.88 et NON surconfiant",
      i["couverture"] >= 0.88 and v != SURCONFIANT)

print("=== COUVERTURE @80% : suit le niveau ===")
inter8, ver8 = couverture(lambda r: r.gauss(0, 1), 40, 0.20, 4000, graine=2)
v8, i8 = CAL.verdict_couverture(inter8, ver8, 0.80)
check(f"jackknife+ @80% : couverture {i8['couverture']:.3f} >= 0.78 et NON surconfiant",
      i8["couverture"] >= 0.78 and v8 != SURCONFIANT)

print("=== PETIT ÉCHANTILLON (n=12) : garantie ≥ 1−2α tenue ===")
inter_pe, ver_pe = couverture(lambda r: r.gauss(5, 3), 12, 0.10, 4000, graine=3)
_, ipe = CAL.verdict_couverture(inter_pe, ver_pe, 0.90)
check(f"n=12 @90% : couverture {ipe['couverture']:.3f} >= 0.80 (≥ 1−2α garantie)", ipe["couverture"] >= 0.80)

print("=== loi asymétrique : couverture tient (distribution-free) ===")
inter_a, ver_a = couverture(lambda r: math.exp(r.gauss(0, 1)), 40, 0.10, 4000, graine=4)
va, ia = CAL.verdict_couverture(inter_a, ver_a, 0.90)
check(f"asymétrique @90% : couverture {ia['couverture']:.3f} >= 0.86 et NON surconfiant",
      ia["couverture"] >= 0.86 and va != SURCONFIANT)

print("=== fonction GÉNÉRIQUE + MONOTONIE + ABSTENTION ===")
mu = [10.0] * 30
res = [float(i % 5) for i in range(30)]
st, (b90, h90), _ = J.intervalle_jackknife_plus(mu, res, 0.10)
st2, (b99, h99), _ = J.intervalle_jackknife_plus(mu, res, 0.01)
check("générique : intervalle 99% plus large que 90%", (h99 - b99) >= (h90 - b90))
check("trop peu de points -> ABSTENTION", J.jackknife_plus_moyenne([1, 2, 3])[0] == ABSTENTION)
check("générique tailles incohérentes -> erreur", _erreur(lambda: J.intervalle_jackknife_plus([1, 2], [1])))

print(f"\nJACKKNIFE+ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
