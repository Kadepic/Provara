"""
VALIDATION du PARADOXE DE LINDLEY (lindley.py). Vérifie : le probit (Φ(probit(p))=p), z_pour_p(0.05)≈1.96 ; B01 croît
avec n à p fixe ; DIVERGENCE à grand n (fréquentiste rejette, bayésien soutient H0) vs ACCORD à petit n (honnêteté) ;
P(H0|donnée)→1 ; un même p=0.05 = preuves très différentes selon n ; un signal vraiment fort (p minuscule) ne déclenche
PAS le paradoxe ; calibration Type-I du test fréquentiste lui-même ≈ α (MC seedé) ; ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import lindley as L
from lindley import ABSTENTION, ANALYSE

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


# ─── 1. Probit & z_pour_p ───
print("=== Probit & z pour p ===")
check("Φ(probit(p)) = p (inversion correcte)", all(abs(L._Phi(L.probit(p)) - p) < 1e-6 for p in (0.01, 0.1, 0.5, 0.9, 0.975)))
check("z pour p=0.05 ≈ 1.96", abs(L.z_pour_p(0.05) - 1.95996) < 1e-3)
check("z pour p=0.01 ≈ 2.576", abs(L.z_pour_p(0.01) - 2.5758) < 1e-3)

# ─── 2. À p=0.05 fixe, B01 croît avec n ───
print("=== B01 croît avec n (p fixe) ===")
z = L.z_pour_p(0.05)
bs = [L.facteur_bayes_01(z, n) for n in (30, 1000, 100000, 10_000_000)]
print(f"   B01 : {[round(b,2) for b in bs]}")
check("B01 est strictement croissant en n", all(bs[i] < bs[i + 1] for i in range(len(bs) - 1)))

# ─── 3. DIVERGENCE à grand n ; ACCORD à petit n (honnêteté) ───
print("=== Divergence Lindley à grand n, accord à petit n ===")
st_grand, ig = L.analyse(0.05, 100000)
st_petit, ip = L.analyse(0.05, 30)
print(f"   n=100000 : rejette_freq={ig['rejette_freq']} B01={ig['B01']:.1f} soutient_H0={ig['soutient_h0_bayes']}")
print(f"   n=30     : rejette_freq={ip['rejette_freq']} B01={ip['B01']:.2f} soutient_H0={ip['soutient_h0_bayes']}")
check("grand n : fréquentiste rejette MAIS bayésien soutient H0 (DIVERGENCE)", ig["rejette_freq"] and ig["soutient_h0_bayes"])
check("petit n : pas de paradoxe (bayésien favorise aussi H1)", not ip["soutient_h0_bayes"])
check("formule signale la DIVERGENCE de Lindley à grand n", "DIVERGENCE" in L.formule((st_grand, ig)))
check("formule signale l'accord à petit n", "DIVERGENCE" not in L.formule((st_petit, ip)))

# ─── 4. P(H0|donnée) → 1 quand n → ∞ (à p=0.05) ───
print("=== P(H0|donnée) → 1 ===")
posts = [L.posterior_h0(z, n) for n in (1000, 100000, 10_000_000)]
print(f"   P(H0|donnée) : {[round(p,3) for p in posts]}")
check("P(H0|donnée) croît vers 1 avec n", posts[0] < posts[1] < posts[2] and posts[-1] > 0.99)

# ─── 5. Sur-confiance : un même p=0.05 = preuves opposées selon n ───
print("=== Même p, preuves opposées selon n ===")
b_petit = L.facteur_bayes_01(z, 30)
b_grand = L.facteur_bayes_01(z, 10_000_000)
print(f"   p=0.05 : B01(n=30)={b_petit:.2f} (pro-H1) vs B01(n=1e7)={b_grand:.1f} (pro-H0)")
check("le même p=0.05 traverse de pro-H1 à fortement pro-H0", b_petit < 1 < 100 < b_grand)

# ─── 6. Un signal VRAIMENT fort ne déclenche pas le paradoxe ───
print("=== Signal fort : pas de faux paradoxe ===")
st_fort, info_fort = L.analyse(1e-8, 1000)         # p minuscule à n modéré
print(f"   p=1e-8, n=1000 : B01={info_fort['B01']:.2e} soutient_H0={info_fort['soutient_h0_bayes']}")
check("un p minuscule donne B01 ≪ 1 (bayésien rejette aussi H0)", not info_fort["soutient_h0_bayes"] and info_fort["B01"] < 0.01)

# ─── 7. Calibration Type-I du test fréquentiste lui-même ≈ α (MC seedé) ───
print("=== Type-I du test fréquentiste ≈ α (sanité) ===")
rng = random.Random(100)
n_ech, alpha, REPS = 50, 0.05, 20000
sigma = 1.0
rejets = 0
for _ in range(REPS):
    xbar = rng.gauss(0.0, sigma / math.sqrt(n_ech))     # sous H0
    zz = abs(xbar) * math.sqrt(n_ech) / sigma
    p = 2 * (1 - L._Phi(zz))
    rejets += p <= alpha
t1 = rejets / REPS
print(f"   Type-I empirique={t1:.3f} (α={alpha})")
check("le test fréquentiste est bien calibré en Type-I (le paradoxe n'est pas un défaut de Type-I)", abs(t1 - alpha) < 0.01)

# ─── 8. ABSTENTION ───
print("=== ABSTENTION ===")
check("p hors ]0,1[ → ABSTENTION", L.analyse(1.5, 100)[0] == ABSTENTION)
check("n < 1 → ABSTENTION", L.analyse(0.05, 0)[0] == ABSTENTION)
check("cas valide → ANALYSE", st_grand == ANALYSE)

print(f"\nRÉSULTAT lindley : {ok}/{total}")
assert ok == total
