"""
VALIDATION de la DÉTECTION DE CHANGEMENT (changepoint.py). Invariant : FAUX POSITIFS ≤ α sous H0 (pas de changement),
PUISSANCE sur un vrai changement, LOCALISATION correcte, p-valeur ~uniforme sous H0.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import changepoint as CP
from changepoint import CHANGEMENT, STABLE, ABSTENTION

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


print("=== FAUX POSITIFS ≤ α sous H0 (série i.i.d., pas de changement) ===")
for alpha in (0.05, 0.10):
    fp = 0
    M = 2000
    for s in range(M):
        rng = random.Random(s)
        serie = [rng.gauss(0, 1) for _ in range(80)]
        if CP.detecte_changement(serie, alpha)[0] == CHANGEMENT:
            fp += 1
    taux = fp / M
    print(f"   alpha={alpha} : faux positifs = {taux:.3f}")
    check(f"faux positifs ({taux:.3f}) <= alpha+tol ({alpha}+0.02)", taux <= alpha + 0.02)

print("=== PUISSANCE + LOCALISATION : changement de moyenne détecté près de la vraie position ===")
det, loc_ok = 0, 0
for s in range(500):
    rng = random.Random(1000 + s)
    pos_vraie = 50
    serie = [rng.gauss(0, 1) for _ in range(pos_vraie)] + [rng.gauss(2.5, 1) for _ in range(50)]
    r = CP.detecte_changement(serie, 0.05)
    if r[0] == CHANGEMENT:
        det += 1
        if abs(r[1] - pos_vraie) <= 8:
            loc_ok += 1
print(f"   puissance={det/500:.3f} ; localisation correcte (±8)={loc_ok/max(1,det):.3f}")
check(f"puissance >= 0.9 ({det/500:.3f})", det / 500 >= 0.9)
check(f"localisation correcte >= 0.85 ({loc_ok/det:.3f})", loc_ok / det >= 0.85)

print("=== p-VALEUR ~UNIFORME sous H0 ===")
ps = []
for s in range(2000):
    rng = random.Random(5000 + s)
    serie = [rng.gauss(0, 1) for _ in range(60)]
    ps.append(CP.detecte_changement(serie, 0.05)[2])
moy = sum(ps) / len(ps)
check(f"moyenne p-valeur ≈ 0.5 ({moy:.3f})", 0.42 <= moy <= 0.58)

print("=== changement PLUS FORT -> p PLUS PETITE (monotonie) ===")
rng = random.Random(7)
base = [rng.gauss(0, 1) for _ in range(40)]
faible = base + [rng.gauss(1, 1) for _ in range(40)]
fort = base + [rng.gauss(4, 1) for _ in range(40)]
check("p(fort) < p(faible)", CP.detecte_changement(fort)[2] < CP.detecte_changement(faible)[2])

print("=== Kolmogorov + ABSTENTION ===")
check("_kolmogorov_p décroît avec la statistique", CP._kolmogorov_p(2.0) < CP._kolmogorov_p(0.5))
check("_kolmogorov_p(0) = 1", CP._kolmogorov_p(0.0) == 1.0)
check("série trop courte -> ABSTENTION", CP.detecte_changement([1, 2, 3])[0] == ABSTENTION)
check("série constante -> ABSTENTION", CP.detecte_changement([5.0] * 20)[0] == ABSTENTION)

print(f"\nCHANGEPOINT VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
