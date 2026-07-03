"""
VALIDATION de la DÉTECTION DE NOUVEAUTÉ (nouveaute.py). On prouve l'invariant : le TAUX DE FAUSSE ALARME (déclarer
NOUVEAU un point pourtant in-distribution) est ≤ alpha — GARANTI, distribution-free — tout en DÉTECTANT le vrai
hors-distribution (puissance). Plus : uniformité des p-valeurs, monotonie, cas limites.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import nouveaute as N
from nouveaute import NOUVEAU, CONNU

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


rng = random.Random(1)
ref = [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(400)]
sc = N.scoreur_knn(ref, k=5)
cal = [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(400)]
scores_cal = [sc(p) for p in cal]

print("=== TAUX DE FAUSSE ALARME ≤ alpha (in-distribution flaggé NOUVEAU à tort) ===")
for alpha in (0.05, 0.10, 0.20):
    test_in = [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(4000)]
    fa = sum(1 for p in test_in if N.est_nouveau(scores_cal, sc(p), alpha)[0] == NOUVEAU) / len(test_in)
    print(f"   alpha={alpha} : fausses alarmes = {fa:.3f}")
    check(f"fausse alarme ({fa:.3f}) <= alpha+tol ({alpha}+0.03)", fa <= alpha + 0.03)

print("=== PUISSANCE : hors-distribution détecté (décalage de moyenne et changement d'échelle) ===")
ood_decale = [(rng.gauss(5, 1), rng.gauss(5, 1)) for _ in range(2000)]
det1 = sum(1 for p in ood_decale if N.est_nouveau(scores_cal, sc(p), 0.05)[0] == NOUVEAU) / len(ood_decale)
check(f"OOD décalé (+5) détecté à {det1:.3f} >= 0.9", det1 >= 0.9)
ood_echelle = [(rng.gauss(0, 5), rng.gauss(0, 5)) for _ in range(2000)]
det2 = sum(1 for p in ood_echelle if N.est_nouveau(scores_cal, sc(p), 0.05)[0] == NOUVEAU) / len(ood_echelle)
check(f"OOD étalé (σ=5) détecté à {det2:.3f} >= 0.5", det2 >= 0.5)

print("=== UNIFORMITÉ des p-valeurs in-distribution (p ~ U[0,1]) ===")
ps = [N.pvaleur_conforme(scores_cal, sc((rng.gauss(0, 1), rng.gauss(0, 1)))) for _ in range(5000)]
moy = sum(ps) / len(ps)
check(f"p-valeurs in-dist : moyenne {moy:.3f} ≈ 0.5", 0.45 <= moy <= 0.55)
frac01 = sum(1 for p in ps if p <= 0.1) / len(ps)
check(f"fraction p<=0.1 ≈ 0.1 (uniformité fine) : {frac01:.3f} <= 0.13", frac01 <= 0.13)

print("=== MONOTONIE & cas limites de la p-valeur ===")
check("point plus loin -> p plus petite", N.pvaleur_conforme(scores_cal, sc((8, 8))) < N.pvaleur_conforme(scores_cal, sc((0, 0))))
check("score = max -> p minimale = 1/(n+1)", abs(N.pvaleur_conforme([1, 2, 3, 4], 100) - 1.0 / 5.0) < 1e-9)
check("score très bas -> p = 1 (tous les cal >= lui)", abs(N.pvaleur_conforme([1, 2, 3, 4], -100) - 1.0) < 1e-9)
check("verdict NOUVEAU si p<alpha", N.est_nouveau([1, 2, 3, 4, 5, 6, 7, 8, 9], 100, 0.2)[0] == NOUVEAU)
check("verdict CONNU si p>=alpha", N.est_nouveau([1, 2, 3, 4, 5, 6, 7, 8, 9], 1, 0.2)[0] == CONNU)

print(f"\nNOUVEAUTÉ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
