"""
VALIDATION du CONFORME PONDÉRÉ (conformal_pondere.py) — jugé par calibration.py. Sous COVARIATE SHIFT, le conforme
NON pondéré SOUS-COUVRE (SURCONFIANT) ; le conforme PONDÉRÉ (poids = rapport de vraisemblance) RESTAURE la couverture
≥ 1−α. Sans décalage, les deux coïncident.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import conformal_pondere as CP
from conformal_pondere import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT

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
    return 0.5 + abs(x)                 # bruit hétéroscédastique : plus on s'éloigne de 0, plus c'est bruité


def couvertures(mu_test, alpha, M, n_cal, graine):
    """À chaque essai : calibration x~N(0,1), test x~N(mu_test,1). Renvoie (intervalles_pondérés, intervalles_non_pondérés,
    verites) pour juger la couverture marginale sous le décalage."""
    rng = random.Random(graine)
    ip, inp, ver = [], [], []
    for _ in range(M):
        xs = [rng.gauss(0, 1) for _ in range(n_cal)]
        residus = [rng.gauss(0, sigma(x)) for x in xs]
        poids = [CP.poids_ratio_gaussien(x, 0, 1, mu_test, 1) for x in xs]
        x_t = rng.gauss(mu_test, 1)
        w_t = CP.poids_ratio_gaussien(x_t, 0, 1, mu_test, 1)
        sp, interp, _ = CP.intervalle_pondere(residus, poids, w_t, 0.0, alpha)
        snp, internp, _ = CP.intervalle_pondere(residus, [1.0] * n_cal, 1.0, 0.0, alpha)
        if sp == ESTIMATION and snp == ESTIMATION:
            ip.append(interp)
            inp.append(internp)
            ver.append(rng.gauss(0, sigma(x_t)))      # vraie valeur test (résidu réel à x_t)
    return ip, inp, ver


print("=== COVARIATE SHIFT (test décalé +1.5) : non pondéré SOUS-COUVRE, pondéré TIENT ===")
ip, inp, ver = couvertures(1.5, 0.10, 4000, 200, graine=1)
vp, infp = CAL.verdict_couverture(ip, ver, 0.90)
vn, infn = CAL.verdict_couverture(inp, ver, 0.90)
print("   pondéré     :", CAL.formule((vp, infp), "couverture"))
print("   non pondéré :", CAL.formule((vn, infn), "couverture"))
check(f"non pondéré sous shift : SOUS-COUVRE {infn['couverture']:.3f} -> SURCONFIANT", vn == SURCONFIANT)
check(f"pondéré sous shift : couverture {infp['couverture']:.3f} >= 0.87 et NON surconfiant",
      infp["couverture"] >= 0.87 and vp != SURCONFIANT)

print("=== SANS DÉCALAGE (mu_test=0) : pondéré ≈ non pondéré ≈ nominal ===")
ip0, inp0, ver0 = couvertures(0.0, 0.10, 3000, 200, graine=2)
vp0, infp0 = CAL.verdict_couverture(ip0, ver0, 0.90)
vn0, infn0 = CAL.verdict_couverture(inp0, ver0, 0.90)
check(f"sans shift : non pondéré calibré ({infn0['couverture']:.3f})", vn0 != SURCONFIANT)
check(f"sans shift : pondéré calibré ({infp0['couverture']:.3f})", vp0 != SURCONFIANT)

print("=== DÉCALAGE PLUS FORT -> pondéré tient encore ===")
ip2, _, ver2 = couvertures(2.5, 0.10, 3000, 250, graine=3)
vp2, infp2 = CAL.verdict_couverture(ip2, ver2, 0.90)
check(f"pondéré sous shift +2.5 : couverture {infp2['couverture']:.3f} >= 0.86 et NON surconfiant",
      infp2["couverture"] >= 0.86 and vp2 != SURCONFIANT)

print("=== PROPRIÉTÉS du quantile pondéré + ABSTENTION ===")
# poids égaux -> identique au quantile conforme standard
import conformal as CF
res = [abs(x) for x in (3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8)]
qp = CP.quantile_pondere(res, [1.0] * len(res), 1.0, 0.10)
qc = CF.quantile_conforme(res, 0.10)
check(f"poids égaux -> quantile pondéré ({qp}) == quantile conforme ({qc})", abs(qp - qc) < 1e-9)
check("poids test énorme -> q = +inf (prudent)", CP.quantile_pondere(res, [1.0] * len(res), 1e6, 0.10) == float("inf"))
check("trop peu de points -> ABSTENTION", CP.intervalle_pondere([1, 2, 3], [1, 1, 1], 1.0, 0.0)[0] == ABSTENTION)
check("plus de confiance -> quantile plus grand",
      CP.quantile_pondere(res, [1.0] * len(res), 1.0, 0.01) >= CP.quantile_pondere(res, [1.0] * len(res), 1.0, 0.30))

print(f"\nCONFORME PONDÉRÉ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
