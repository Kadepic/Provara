"""
VALIDATION de la COMPLEXITÉ DE RADEMACHER (rademacher.py). Vérifie R̂_n ∈ [0,1] (classe non restreinte ≈ 1/2 →
borne vide), la monotonie (classe plus grande ⇒ R̂_n ≥), le majorant de Massart, la COUVERTURE de la borne de
généralisation (R_vrai ≤ borne ∀h, ≥ 1−δ), et le DÉMASQUE : le risque empirique de l'hypothèse sélectionnée
sous-estime le vrai (sur-confiance ↑ avec la richesse de la classe) alors que la borne le majore. Pur Python, léger.
"""
from __future__ import annotations

import itertools
import math
import random

from garde_ressources import borne as _gb
import rademacher as R
from rademacher import ABSTENTION, BORNE

_gb()
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


rng = random.Random(66)


def classe(rng, K, n, p=0.5):
    """K vecteurs de pertes ∈ {0,1}, iid Bernoulli(p) : risque vrai = p, risque empirique = moyenne."""
    return [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(K)]


# ─── 1. R̂_n ∈ [0,1] + classe non restreinte ≈ 1/2 ───
print("=== R̂_n ∈ [0,1] ; classe non restreinte ≈ 1/2 (borne vide) ===")
tous = [list(pat) for pat in itertools.product([0, 1], repeat=10)]
rad_full = R.rademacher_empirique(tous, rng, 300)
print(f"   R̂_n(non restreinte) = {rad_full:.3f}")
check("R̂_n non restreinte ≈ 0.5 (0.45–0.55)", 0.45 <= rad_full <= 0.55)
check("borne vide pour la classe non restreinte (≥ 1)", R.borne_generalisation(0.0, rad_full, 10) >= 1.0)

# ─── 2. Monotonie : superset ⇒ R̂_n ≥ (mêmes σ) ───
print("=== Monotonie : classe plus grande ⇒ R̂_n ≥ ===")
mono_ok = True
for _ in range(300):
    n = 30
    H = classe(rng, 4, n); extra = classe(rng, 4, n)
    s = rng.randint(0, 10**6)
    r1 = R.rademacher_empirique(H, random.Random(s), 150)
    r2 = R.rademacher_empirique(H + extra, random.Random(s), 150)   # mêmes σ
    if r2 < r1 - 1e-12:
        mono_ok = False; break
check("R̂_n(H ∪ extra) ≥ R̂_n(H) (sup sur superset)", mono_ok)

# ─── 3. Majorant de Massart ───
print("=== Majorant de Massart : R̂_n ≤ √(2 ln|H|/n) ===")
massart_ok = True
for _ in range(400):
    n = rng.randint(20, 60); K = rng.randint(2, 40)
    H = classe(rng, K, n)
    if R.rademacher_empirique(H, rng, 200) > R.borne_massart(K, n) + 0.02:
        massart_ok = False; break
check("R̂_n ≤ borne de Massart (à la précision MC)", massart_ok)

# ─── 4. COUVERTURE de la borne de généralisation ≥ 1−δ ───
print("=== Couverture : R_vrai(h) ≤ borne ∀h (≥ 1−δ) ===")
n = 400; K = 12; p = 0.5; delta = 0.1
TRIALS = 250
couvre = 0
emp_valide = 0
for _ in range(TRIALS):
    H = classe(rng, K, n, p)
    risques_emp = [sum(lv) / n for lv in H]
    st, info = R.borne(H, risques_emp, n, rng, delta, n_sigma=60)
    bornes = info["bornes"]
    if all(p <= b + 1e-12 for b in bornes):        # R_vrai = p pour tout h
        couvre += 1
    if all(p <= re + 1e-12 for re in risques_emp):  # risque empirique comme 'majorant'
        emp_valide += 1
cov = couvre / TRIALS; empc = emp_valide / TRIALS
print(f"   couverture borne Rademacher = {cov:.3f} (≥ {1-delta}) ; risque empirique comme majorant = {empc:.3f}")
check("la borne de Rademacher couvre le risque vrai ≥ 1−δ", cov >= 1 - delta)
check("le risque EMPIRIQUE n'est pas un majorant valide (sur-confiant)", empc < 1 - delta)

# ─── 5. DÉMASQUE : sur-confiance ↑ avec la richesse de la classe ───
print("=== Mode d'échec : sélection ⇒ R_emp(ĥ) sous-estime, écart ↑ avec |H| ===")
def biais_min_emp(K, n, p, reps=400):
    s = 0.0
    for _ in range(reps):
        H = classe(rng, K, n, p)
        s += p - min(sum(lv) / n for lv in H)        # vrai − meilleur empirique
    return s / reps
b_petit = biais_min_emp(2, 200, 0.5)
b_grand = biais_min_emp(40, 200, 0.5)
print(f"   écart vrai−min_emp : |H|=2 → {b_petit:.3f} ; |H|=40 → {b_grand:.3f}")
check("le min empirique sous-estime le risque vrai (sur-confiance)", b_petit > 0 and b_grand > 0)
check("l'écart (sur-confiance) CROÎT avec la richesse de la classe", b_grand > b_petit + 0.02)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = R.borne([[0, 1]], [0.5], 0, rng, 0.05)
st2, _ = R.borne([[0, 1]], [0.5], 2, rng, 1.5)
st3, _ = R.borne([], [], 10, rng, 0.05)
check("n=0 → ABSTENTION", st1 == ABSTENTION)
check("δ hors (0,1) → ABSTENTION", st2 == ABSTENTION)
check("classe vide → ABSTENTION", st3 == ABSTENTION)
st4, _ = R.borne([[0, 1, 0], [1, 1, 0]], [0.33, 0.67], 3, rng, 0.05, n_sigma=50)
check("cas valide → BORNE", st4 == BORNE)

print(f"\nRÉSULTAT rademacher : {ok}/{total}")
assert ok == total
