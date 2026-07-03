"""
VALIDATION de l'ÉCHANTILLONNAGE PRÉFÉRENTIEL & ESS (importance_sampling.py). Vérifie la formule/bornes de l'ESS
(=n si poids uniformes, ≈1 si un poids domine), l'absence de biais, le DÉMASQUE (une proposition à queue LÉGÈRE rend
l'écart-type NAÏF SOUS-ESTIMÉ vs la vraie variabilité run-to-run = sur-confiance), que q=p / q large donnent un SE
honnête, que l'ESS DIAGNOSTIQUE au niveau du run (faible ESS ⇒ erreur plus grande), le verdict NON_FIABLE et
l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import math
import random
import statistics

from garde_ressources import borne
import importance_sampling as IS
from importance_sampling import ABSTENTION, FIABLE, NON_FIABLE

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


rng = random.Random(78)
p = lambda x: IS.normal_pdf(x, 0, 1)
f = lambda x: x * x                     # E_p[x²] = 1


# ─── 1. ESS : formule, bornes, cas extrêmes ───
print("=== ESS : =n si uniforme, ≈1 si un poids domine, ∈[1,n] ===")
check("poids uniformes → ESS = n", abs(IS.ess([1.0] * 50) - 50) < 1e-9)
check("un poids domine → ESS ≈ 1", IS.ess([1e6] + [1.0] * 49) < 1.1)
borne_ok = True
for _ in range(2000):
    w = [rng.random() + 1e-3 for _ in range(rng.randint(2, 30))]
    if not (1 - 1e-9 <= IS.ess(w) <= len(w) + 1e-9):
        borne_ok = False
check("ESS ∈ [1, n]", borne_ok)

# ─── 2. ESS = n ⟺ q = p ───
print("=== ESS = n quand q = p (poids tous égaux) ===")
xs = [rng.gauss(0, 1) for _ in range(100)]
check("q=p → poids égaux → ESS = n", abs(IS.ess(IS.poids(xs, p, p)) - 100) < 1e-9)

# ─── 3. Sans biais (même quand peu fiable) ───
print("=== Estimateur sans biais ===")
def moyenne_estimes(sig_q, reps=800, n=200):
    q = lambda x, s=sig_q: IS.normal_pdf(x, 0, s)
    es = []
    for _ in range(reps):
        xs = [rng.gauss(0, sig_q) for _ in range(n)]
        es.append(IS.estimateur(xs, f, IS.poids(xs, p, q)))
    return statistics.mean(es), statistics.pstdev(es)
m_pp, _ = moyenne_estimes(1.0)
m_lt, _ = moyenne_estimes(0.7)
print(f"   E[μ̂] : q=p → {m_pp:.3f} ; q queue-légère → {m_lt:.3f} (vrai 1.0)")
check("sans biais avec q=p", abs(m_pp - 1.0) < 0.03)
check("sans biais même avec q à queue légère (juste imprécis)", abs(m_lt - 1.0) < 0.1)

# ─── 4. DÉMASQUE : queue légère → SE naïf SOUS-ESTIMÉ vs vraie variabilité ───
print("=== Mode d'échec : SE naïf sous-estime sous une proposition à queue légère ===")
def vrai_vs_naif(sig_q, reps=800, n=200):
    q = lambda x, s=sig_q: IS.normal_pdf(x, 0, s)
    ests, ses = [], []
    for _ in range(reps):
        xs = [rng.gauss(0, sig_q) for _ in range(n)]
        w = IS.poids(xs, p, q)
        ests.append(IS.estimateur(xs, f, w)); ses.append(IS.erreur_naive(xs, f, w))
    return statistics.pstdev(ests), statistics.median(ses)
vrai_lt, naif_lt = vrai_vs_naif(0.7)
vrai_pp, naif_pp = vrai_vs_naif(1.0)
print(f"   q queue-légère : vrai SE={vrai_lt:.3f} vs naïf={naif_lt:.3f} ; q=p : vrai={vrai_pp:.3f} vs naïf={naif_pp:.3f}")
check("queue légère : SE naïf SOUS-ESTIME la vraie variabilité (sur-confiance)", naif_lt < 0.6 * vrai_lt)
check("q=p : SE naïf ≈ vraie variabilité (honnête)", abs(naif_pp - vrai_pp) < 0.25 * vrai_pp)

# ─── 5. L'ESS diagnostique au niveau du run (faible ESS ⇒ erreur plus grande) ───
print("=== ESS comme diagnostic : faible ESS ⇒ plus grande erreur ===")
q = lambda x: IS.normal_pdf(x, 0, 0.7)
runs = []
for _ in range(1500):
    xs = [rng.gauss(0, 0.7) for _ in range(150)]
    w = IS.poids(xs, p, q)
    runs.append((IS.ess(w), abs(IS.estimateur(xs, f, w) - 1.0)))
runs.sort()
q1 = runs[:len(runs) // 4]; q4 = runs[3 * len(runs) // 4:]
err_bas_ess = statistics.mean(e for _, e in q1); err_haut_ess = statistics.mean(e for _, e in q4)
print(f"   erreur moyenne : quartile ESS BAS={err_bas_ess:.3f} ; ESS HAUT={err_haut_ess:.3f}")
check("les runs à faible ESS ont une erreur plus grande (ESS diagnostique)", err_bas_ess > err_haut_ess)

# ─── 6. Verdict NON_FIABLE / FIABLE (mécanisme de seuil) ───
print("=== Verdict : seuil sur l'ESS ===")
xs = [rng.gauss(0, 1) for _ in range(200)]
st_pp = IS.analyse(xs, f, p, p, seuil_ess=0.9)               # ESS=n → fiable
st_large = IS.analyse([rng.gauss(0, 2) for _ in range(200)], f, p, lambda x: IS.normal_pdf(x, 0, 2), seuil_ess=0.9)  # ESS~0.66n < 0.9
check("q=p (ESS=n) → FIABLE", st_pp[0] == FIABLE)
check("seuil élevé attrape une ESS modérée → NON_FIABLE", st_large[0] == NON_FIABLE)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1 = IS.analyse([0.5], f, p, p)
st2 = IS.analyse([0.1, 0.2], f, p, lambda x: -1.0)
check("n<2 → ABSTENTION", st1[0] == ABSTENTION)
check("poids négatifs → ABSTENTION", st2[0] == ABSTENTION)
st3 = IS.analyse(xs, f, p, p)
check("cas valide → FIABLE", st3[0] == FIABLE)

print(f"\nRÉSULTAT importance_sampling : {ok}/{total}")
assert ok == total
