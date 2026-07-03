"""
VALIDATION des bornes PAC-BAYES (pac_bayes.py). Vérifie l'inversion du kl (tight), la COUVERTURE (R_vrai(Q) ≤ borne
avec fréquence ≥ 1−δ sur des échantillons simulés), que le risque EMPIRIQUE n'est PAS un majorant valide (sur-confiant),
la borne de McAllester (valide, plus lâche que kl), le PRIX de complexité KL, la convergence borne→R_emp (n→∞), le
biais d'optimisme de l'hypothèse sélectionnée, et l'ABSTENTION. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne as _b
import pac_bayes as PB
from pac_bayes import ABSTENTION, BORNE

_b()
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


rng = random.Random(63)


def emp_echantillon(rng, true_risks, n):
    """Risque empirique de chaque hypothèse = #erreurs/n, erreurs ~ Bernoulli(t_h)."""
    return {h: sum(1 for _ in range(n) if rng.random() < t) / n for h, t in true_risks.items()}


# ─── 1. Inversion du kl : tight + majorant ───
print("=== kl⁻¹ : kl(q‖B) = budget (tight) et B ≥ q ===")
tight_ok = maj_ok = True
for _ in range(5000):
    q = rng.uniform(0, 0.8); budget = rng.uniform(0.005, 0.5)
    B = PB.kl_inverse(q, budget)
    if B < q - 1e-12:
        maj_ok = False
    if B < 1 - 1e-6 and abs(PB.kl_bernoulli(q, B) - budget) > 1e-6:
        tight_ok = False
check("kl⁻¹(q, budget) ≥ q (majorant)", maj_ok)
check("kl(q‖B) = budget quand B<1 (inversion exacte)", tight_ok)

# ─── 2. COUVERTURE : R_vrai(Q) ≤ borne avec fréquence ≥ 1−δ ───
print("=== Couverture PAC-Bayes ≥ 1−δ ===")
H = [f"h{i}" for i in range(8)]
true_risks = {h: rng.uniform(0.2, 0.55) for h in H}
P = {h: 1 / len(H) for h in H}
delta = 0.05
n = 150
couvre = 0
emp_valide = 0
TRIALS = 2500
for _ in range(TRIALS):
    emp = emp_echantillon(rng, true_risks, n)
    Q = PB.gibbs(P, emp, gamma=1.5, n=n)
    st, B = PB.borne(Q, P, emp, n, delta)
    r_vrai = PB.risque(Q, true_risks)
    if r_vrai <= B + 1e-12:
        couvre += 1
    if r_vrai <= PB.risque(Q, emp) + 1e-12:
        emp_valide += 1
cov = couvre / TRIALS
emp_cov = emp_valide / TRIALS
print(f"   couverture borne PAC-Bayes = {cov:.3f} (≥ {1-delta}) ; 'borne' = risque empirique = {emp_cov:.3f}")
check("couverture de la borne PAC-Bayes ≥ 1−δ", cov >= 1 - delta)
check("le risque EMPIRIQUE n'est PAS un majorant valide (sur-confiant, couvre < 1−δ)", emp_cov < 1 - delta)

# ─── 3. McAllester : valide (≥1−δ) et plus lâche que kl ───
print("=== Borne de McAllester : valide et ≥ borne kl ===")
couvre_m = 0
plus_lache = True
for _ in range(2000):
    emp = emp_echantillon(rng, true_risks, n)
    Q = PB.gibbs(P, emp, 1.5, n)
    bm = PB.borne_mcallester(Q, P, emp, n, delta)
    _, bk = PB.borne(Q, P, emp, n, delta)
    if PB.risque(Q, true_risks) <= bm + 1e-12:
        couvre_m += 1
    if bm < bk - 1e-9:
        plus_lache = False
check("couverture McAllester ≥ 1−δ", couvre_m / 2000 >= 1 - delta)
check("McAllester ≥ borne kl (kl plus serrée)", plus_lache)

# ─── 4. Prix de complexité KL + convergence n→∞ ───
print("=== Prix KL (budget↑ ⇒ borne↑) + borne → R_emp quand n→∞ ===")
mono_ok = True
for _ in range(3000):
    q = rng.uniform(0.05, 0.6)
    b1, b2 = rng.uniform(0.01, 0.1), rng.uniform(0.2, 0.5)
    if PB.kl_inverse(q, min(b1, b2)) > PB.kl_inverse(q, max(b1, b2)) + 1e-12:
        mono_ok = False
check("kl⁻¹ croissant en budget (plus de complexité KL ⇒ borne plus haute)", mono_ok)
emp = {h: 0.3 for h in H}
Q = PB.gibbs(P, emp, 1.0, 100)
_, b_petit = PB.borne(Q, P, emp, 100, delta)
_, b_grand = PB.borne(Q, P, emp, 100000, delta)
print(f"   borne(n=100)={b_petit:.3f} → borne(n=1e5)={b_grand:.3f} (R_emp={PB.risque(Q,emp):.3f})")
check("borne → R_emp quand n→∞ (l'évidence rachète l'optimisme)", abs(b_grand - PB.risque(Q, emp)) < 0.02 and b_petit > b_grand)

# ─── 5. Biais d'optimisme de l'hypothèse SÉLECTIONNÉE ───
print("=== Biais de sélection : argmin R_emp sous-estime son risque vrai ===")
biais = 0.0
T = 3000
for _ in range(T):
    emp = emp_echantillon(rng, true_risks, n)
    hstar = min(emp, key=emp.get)
    biais += emp[hstar] - true_risks[hstar]
biais /= T
print(f"   biais moyen R_emp(ĥ) − R_vrai(ĥ) = {biais:.4f} (< 0 = optimisme)")
check("l'hypothèse sélectionnée a un risque empirique biaisé BAS (optimisme)", biais < -0.005)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = PB.borne({"a": 1.0}, {"a": 1.0}, {"a": 0.3}, 0, delta)
st2, _ = PB.borne({"a": 1.0}, {"a": 1.0}, {"a": 0.3}, 100, 1.5)
st3, _ = PB.borne({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.4}, {"a": 0.3, "b": 0.3}, 100, delta)  # P somme 0.9
st3b, _ = PB.borne({"a": 0.5, "b": 0.5}, {"a": 1.0, "b": 0.0}, {"a": 0.3, "b": 0.3}, 100, delta)  # support Q hors P
check("n=0 → ABSTENTION", st1 == ABSTENTION)
check("δ hors (0,1) → ABSTENTION", st2 == ABSTENTION)
check("distribution non normalisée → ABSTENTION", st3 == ABSTENTION)
check("support de Q hors du prior → ABSTENTION", st3b == ABSTENTION)
st4, _ = PB.borne({"a": 1.0}, {"a": 1.0}, {"a": 0.3}, 100, delta)
check("cas valide → BORNE", st4 == BORNE)

print(f"\nRÉSULTAT pac_bayes : {ok}/{total}")
assert ok == total
