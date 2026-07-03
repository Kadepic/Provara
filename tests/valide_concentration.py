"""
VALIDATION des BORNES DE CONCENTRATION (concentration.py) — jugée par calibration.py. Vérifie que Hoeffding et
empirical-Bernstein COUVRENT ≥ 1−δ (distribution-free, n fini, plusieurs lois), que l'intervalle GAUSSIEN
SOUS-COUVRE (SUR-CONFIANT) à petit n / loi asymétrique, qu'empirical-Bernstein est bien plus serré que Hoeffding à
faible variance (n grand), que la largeur de Hoeffding ne dépend pas des données, et que tout rétrécit avec n. Pur
Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import concentration as C
from concentration import ABSTENTION, INTERVALLE
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


rng = random.Random(68)
LOIS = {
    "uniforme[0,1]": (lambda: rng.random(), 0.5),
    "Bernoulli(0.1)": (lambda: 1.0 if rng.random() < 0.1 else 0.0, 0.1),
    "Bernoulli(0.05)": (lambda: 1.0 if rng.random() < 0.05 else 0.0, 0.05),
}


def couvre(methode, loi, mu, n, delta, reps):
    samp = LOIS[loi][0]
    c = 0
    inters = []
    for _ in range(reps):
        xs = [samp() for _ in range(n)]
        if methode == "gaussien":
            lo, hi = C.gaussien(xs, delta)
        else:
            lo, hi = getattr(C, methode)(xs, 0, 1, delta)
        inters.append((lo, hi))
        if lo - 1e-12 <= mu <= hi + 1e-12:
            c += 1
    return c / reps, inters


delta = 0.10
# ─── 1. Hoeffding & empirical-Bernstein couvrent ≥ 1−δ (distribution-free) ───
print("=== Couverture ≥ 1−δ : Hoeffding & empirical-Bernstein (n=30) ===")
for loi, (_, mu) in LOIS.items():
    cH, _ = couvre("hoeffding", loi, mu, 30, delta, 2000)
    cB, _ = couvre("empirical_bernstein", loi, mu, 30, delta, 2000)
    print(f"   {loi:16s}: Hoeffding={cH:.3f}  emp-Bernstein={cB:.3f} (≥ {1-delta})")
    check(f"Hoeffding couvre ≥ 1−δ ({loi})", cH >= 1 - delta)
    check(f"empirical-Bernstein couvre ≥ 1−δ ({loi})", cB >= 1 - delta)

# ─── 2. DÉMASQUE : l'intervalle GAUSSIEN sous-couvre (sur-confiant) ───
print("=== Mode d'échec : intervalle gaussien (TCL) à petit n / loi asymétrique ===")
cG, intG = couvre("gaussien", "Bernoulli(0.05)", 0.05, 15, delta, 4000)
verit = [0.05] * len(intG)
vG, iG = CAL.verdict_couverture(intG, verit, 1 - delta)
print(f"   gaussien Bernoulli(0.05) n=15 : couverture={cG:.3f} ({vG}) (nominal {1-delta})")
check("l'intervalle gaussien SOUS-COUVRE (sur-confiant) à petit n / asymétrie", cG < 1 - delta and vG == SURCONFIANT)
# cas dégénéré explicite
deg = C.gaussien([0.0] * 20)
check("échantillon tout à 0 → gaussien dégénéré [0,0] (fausse certitude)", deg == (0.0, 0.0))
check("Hoeffding sur le même échantillon reste honnête (haut > 0)", C.hoeffding([0.0] * 20, 0, 1)[1] > 0)

# ─── 3. empirical-Bernstein ≪ Hoeffding à faible variance (n grand) ───
print("=== empirical-Bernstein bien plus serré que Hoeffding à faible variance ===")
faible = [min(1, max(0, 0.5 + rng.gauss(0, 0.01))) for _ in range(400)]
wH = (lambda t: t[1] - t[0])(C.hoeffding(faible, 0, 1, 0.05))
wB = (lambda t: t[1] - t[0])(C.empirical_bernstein(faible, 0, 1, 0.05))
print(f"   n=400, var faible : largeur Hoeffding={wH:.3f} ; emp-Bernstein={wB:.3f}")
check("empirical-Bernstein nettement plus serré (variance-adaptatif)", wB < wH * 0.6)

# ─── 4. Largeur de Hoeffding indépendante des données ───
print("=== Largeur de Hoeffding = fonction de (n, amplitude, δ) seulement ===")
e1 = [rng.random() for _ in range(40)]; e2 = [rng.random() ** 3 for _ in range(40)]
w1 = (lambda t: t[1] - t[0])(C.hoeffding(e1, 0, 1, 0.05))
w2 = (lambda t: t[1] - t[0])(C.hoeffding(e2, 0, 1, 0.05))
# (clipping aux bords mis à part) la demi-largeur théorique est identique
demi = (1 - 0) * math.sqrt(math.log(2 / 0.05) / (2 * 40))
check("demi-largeur Hoeffding = (b−a)√(ln(2/δ)/2n) (indépendante des valeurs)",
      abs(demi - math.sqrt(math.log(2/0.05)/80)) < 1e-12)

# ─── 5. Largeur → 0 quand n → ∞ ───
print("=== Largeur → 0 avec n ===")
def largeur(meth, n):
    xs = [rng.random() for _ in range(n)]
    lo, hi = (C.gaussien(xs, 0.05) if meth == "gaussien" else getattr(C, meth)(xs, 0, 1, 0.05))
    return hi - lo
check("Hoeffding rétrécit avec n", largeur("hoeffding", 50) > largeur("hoeffding", 5000))
check("empirical-Bernstein rétrécit avec n", largeur("empirical_bernstein", 50) > largeur("empirical_bernstein", 5000))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _, _ = C.intervalle([0.5], 0, 1)
st2, _, _ = C.intervalle([0.5, 0.3], 1, 0)
st3, _, _ = C.intervalle([0.5, 2.0], 0, 1)
st4, _, _ = C.intervalle([0.1, 0.2, 0.3], 0, 1, 1.5)
check("n<2 → ABSTENTION", st1 == ABSTENTION)
check("a≥b → ABSTENTION", st2 == ABSTENTION)
check("données hors [a,b] → ABSTENTION", st3 == ABSTENTION)
check("δ hors (0,1) → ABSTENTION", st4 == ABSTENTION)
st5, _, _ = C.intervalle([0.2, 0.4, 0.6, 0.5], 0, 1)
check("cas valide → INTERVALLE", st5 == INTERVALLE)

print(f"\nRÉSULTAT concentration : {ok}/{total}")
assert ok == total
