"""
VALIDATION des RÉGIONS MULTIVARIÉES CONFORMES (region_multivariee.py) — jugée par calibration.py. Sur des lois
connues (gaussiennes corrélées, 2D et 3D), la région conforme de Mahalanobis couvre ~1−α (couverture JOINTE garantie),
là où la boîte marginale par coordonnée SOUS-couvre (sur-confiance). Astuce de jugement : « y ∈ région » ⟺
0 ≤ D²(y) ≤ seuil, donc intervalle=(0,seuil) + vérité=D²(y) se juge par calibration.verdict_couverture.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import region_multivariee as RM
from region_multivariee import ESTIMATION, ABSTENTION
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


def gauss2(rng, n):
    out = []
    for _ in range(n):
        z1 = rng.gauss(0, 1)
        z2 = 0.8 * z1 + 0.6 * rng.gauss(0, 1)        # corrélées
        out.append((10 + 2 * z1, 5 + 1.5 * z2))
    return out


def gauss3(rng, n):
    out = []
    for _ in range(n):
        z1 = rng.gauss(0, 1)
        z2 = 0.7 * z1 + rng.gauss(0, 1)
        z3 = 0.5 * z1 + 0.5 * z2 + rng.gauss(0, 1)
        out.append((z1, 1 + z2, 2 + z3))
    return out


def experience(gen, alpha, reps, seed):
    """reps splits indépendants ; 1 point test frais par split. Renvoie (inter_conf, ver_conf, cov_box)."""
    rng = random.Random(seed)
    inter, ver = [], []
    in_box = 0
    n_box = 0
    for k in range(reps):
        train = gen(rng, 120)
        calib = gen(rng, 120)
        st, reg, _ = RM.region_conforme(train, calib, alpha)
        box = RM.boite_marginale(train + calib, alpha)
        y = gen(rng, 1)[0]
        if st == ESTIMATION:
            d2 = RM._mahal(y, reg["mu"], reg["Sinv"])
            inter.append((0.0, reg["seuil"])); ver.append(d2)
        n_box += 1
        in_box += RM.dans_boite(box, y)
    return inter, ver, in_box / n_box


print("=== 2D corrélé : région conforme CALIBRÉE, boîte marginale SOUS-couvre ===")
inter, ver, cov_box = experience(gauss2, 0.10, 500, 1)
vC, iC = CAL.verdict_couverture(inter, ver, 0.90)
print(f"   région conforme couverture={iC['couverture']:.3f} ({vC}) ; boîte marginale={cov_box:.3f} (cible 0.90)")
check("région conforme couvre ~0.90 (>=0.86) et NON surconfiante", iC["couverture"] >= 0.86 and vC != SURCONFIANT)
check("boîte marginale SOUS-couvre nettement (< 0.87)", cov_box < 0.87)

print("=== 3D corrélé : la boîte sous-couvre encore plus, le conforme tient ===")
inter3, ver3, cov_box3 = experience(gauss3, 0.10, 500, 2)
vC3, iC3 = CAL.verdict_couverture(inter3, ver3, 0.90)
print(f"   région conforme couverture={iC3['couverture']:.3f} ({vC3}) ; boîte 3D={cov_box3:.3f}")
check("région conforme 3D couvre ~0.90 (>=0.86) et NON surconfiante", iC3["couverture"] >= 0.86 and vC3 != SURCONFIANT)
check("boîte marginale 3D sous-couvre encore plus qu'en 2D", cov_box3 < cov_box)

print("=== Région conforme valide AUSSI à 1−α=0.80 (le seuil suit le niveau) ===")
inter8, ver8, _ = experience(gauss2, 0.20, 500, 3)
v8, i8 = CAL.verdict_couverture(inter8, ver8, 0.80)
print(f"   couverture={i8['couverture']:.3f} ({v8})")
check("couverture ~0.80 et non surconfiante", i8["couverture"] >= 0.76 and v8 != SURCONFIANT)

print("=== ABSTENTION : calibration trop petite ===")
rng = random.Random(9)
st, _, raison = RM.region_conforme(gauss2(rng, 120), gauss2(rng, 10), 0.10)
print(f"   {st} : {raison}")
check("ABSTENTION si calib < N_MIN_CAL", st == ABSTENTION)

print("=== ABSTENTION : covariance singulière (coordonnées colinéaires) ===")
rng = random.Random(8)
deg = [(v := rng.gauss(0, 1), 2 * v) for _ in range(120)]   # y2 = 2*y1 exactement
st, _, raison = RM.region_conforme(deg, deg, 0.10)
print(f"   {st} : {raison}")
check("ABSTENTION si covariance singulière", st == ABSTENTION)

print(f"\nRÉSULTAT region_multivariee : {ok}/{total}")
assert ok == total
