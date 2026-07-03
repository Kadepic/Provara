"""
VALIDATION de l'E-PROCESS / TEST PAR PARI (e_process.py). Vérifie : martingale sous H0 (E[Eₜ]=1), inégalité de
VILLE (P(∃t Eₜ≥1/α) ≤ α = erreur de type I contrôlée SOUS arrêt optionnel), le DÉMASQUE d'un p-value classique
RÉPÉTÉ (type I explose = sur-confiance), la PUISSANCE sous H1, la MULTIPLICATIVITÉ des e-values, et la validité du
p-value anytime. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import e_process as E
from e_process import ABSTENTION, TEST

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


rng = random.Random(69)
p0 = 0.5
GRILLE = [0.5 + 0.5 * k / 10 for k in range(1, 10)]


def bernoulli(rng, p, n):
    return [1 if rng.random() < p else 0 for _ in range(n)]


# ─── 1. Martingale sous H0 : multiplicateur d'un pas = 1 (EXACT) + path-wise mélange = moyenne ───
# (NB : E[E_T] empirique sous-estime 1 — martingale à QUEUE LOURDE, moyenne dominée par des valeurs énormes rares ;
#  on vérifie donc l'identité martingale EXACTEMENT, pas par moyenne bruitée. La validité opérationnelle = Ville (§2).)
print("=== Martingale sous H0 : multiplicateur attendu d'un pas = 1 (exact) ===")
exact_ok = True
for p1 in GRILLE:
    pas = p0 * (p1 / p0) + (1 - p0) * ((1 - p1) / (1 - p0))   # E_{H0}[multiplicateur]
    if abs(pas - 1.0) > 1e-12:
        exact_ok = False
check("E_{H0}[multiplicateur d'un pas] = 1 ∀p1 (e-process = martingale, exact)", exact_ok)
# mélange = moyenne path-wise des e-process simples
xs_t = bernoulli(rng, p0, 40)
mix = E.e_process_melange(xs_t, p0, GRILLE)
moy = [sum(E.e_process_simple(xs_t, p0, p1)[t] for p1 in GRILLE) / len(GRILLE) for t in range(len(xs_t))]
check("e-process de mélange = moyenne des e-process simples (martingale par convexité)",
      all(abs(mix[t] - moy[t]) < 1e-9 for t in range(len(xs_t))))
# numérique TAME (faible variance) : E[E_T] ≈ 1
m_tame = sum(E.e_process_simple(bernoulli(rng, p0, 20), p0, 0.55)[-1] for _ in range(20000)) / 20000
print(f"   E[E_T] (p1=0.55, T=20, faible variance) = {m_tame:.3f} (≈ 1)")
check("E[E_T] ≈ 1 numériquement sur un cas à faible variance", abs(m_tame - 1) < 0.05)

# ─── 2. VILLE : P(∃t Eₜ ≥ 1/α) ≤ α (type I sous arrêt optionnel) ───
print("=== Ville : erreur de type I ≤ α SOUS peeking ===")
alpha = 0.10
s = E.seuil(alpha)
H = 300; TR = 4000
rejette_H0 = 0
for _ in range(TR):
    es = E.e_process_melange(bernoulli(rng, p0, H), p0, GRILLE)
    if max(es) >= s:
        rejette_H0 += 1
t1 = rejette_H0 / TR
print(f"   type I (e-process, arrêt au 1er franchissement) = {t1:.3f} (≤ α={alpha})")
check("erreur de type I de l'e-process ≤ α (Ville)", t1 <= alpha + 0.01)

# ─── 3. DÉMASQUE : p-value classique RÉPÉTÉ explose ───
print("=== Mode d'échec : p-value classique répété (peeking) ===")
def _Phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))
rejette_naif = 0
for _ in range(TR):
    xs = bernoulli(rng, p0, H)
    s_cum = 0
    rejete = False
    for t in range(1, H + 1):
        s_cum += xs[t - 1]
        if t >= 10:
            phat = s_cum / t
            z = (phat - p0) / math.sqrt(p0 * (1 - p0) / t)
            if (1 - _Phi(z)) < alpha:     # p-value unilatéral
                rejete = True; break
    if rejete:
        rejette_naif += 1
tn = rejette_naif / TR
print(f"   type I (p-value répété, peeking) = {tn:.3f} (≫ α={alpha})")
check("le p-value classique répété EXPLOSE l'erreur de type I (sur-confiant)", tn > 2 * alpha)
check("l'e-process contrôle bien mieux que le p-value répété", t1 < tn / 2)

# ─── 4. Puissance sous H1 ───
print("=== Puissance : sous H1, l'e-process rejette ===")
det = 0
for _ in range(1500):
    es = E.e_process_melange(bernoulli(rng, 0.65, H), p0, GRILLE)
    if max(es) >= s:
        det += 1
puis = det / 1500
print(f"   puissance (p_vrai=0.65) = {puis:.3f}")
check("puissance élevée sous H1 (> 0.9)", puis > 0.9)

# ─── 5. Multiplicativité des e-values ───
print("=== Les e-values se MULTIPLIENT : E[E₁·E₂] ≤ 1 sous H0 ===")
prod = sum(E.e_process_simple(bernoulli(rng, p0, 20), p0, 0.7)[-1]
           * E.e_process_simple(bernoulli(rng, p0, 20), p0, 0.7)[-1] for _ in range(8000)) / 8000
print(f"   E[E₁·E₂] = {prod:.3f} (≤ 1, à la précision MC)")
check("le produit de deux e-values indépendantes reste une e-value (E[·] ≤ 1)", prod <= 1.1)

# ─── 6. p-value anytime valide ───
print("=== p-value anytime : P(min_t pₜ ≤ α) ≤ α + monotonie ===")
viol = 0
mono_ok = True
for _ in range(TR):
    es = E.e_process_melange(bernoulli(rng, p0, H), p0, GRILLE)
    ps = E.p_anytime(es)
    if min(ps) <= alpha:
        viol += 1
    if any(ps[i + 1] > ps[i] + 1e-12 for i in range(len(ps) - 1)):
        mono_ok = False
check("P(min_t pₜ ≤ α) ≤ α (p-value anytime valide)", viol / TR <= alpha + 0.01)
check("pₜ non-croissant (running max de E)", mono_ok)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = E.test_sequentiel([], p0, alpha)
st2, _ = E.test_sequentiel([1, 0, 1], 1.5, alpha)
st3, _ = E.test_sequentiel([1, 0, 1], p0, 2.0)
check("données vides → ABSTENTION", st1 == ABSTENTION)
check("p0 hors (0,1) → ABSTENTION", st2 == ABSTENTION)
check("α hors (0,1) → ABSTENTION", st3 == ABSTENTION)
st4, _ = E.test_sequentiel(bernoulli(rng, 0.7, 50), p0, alpha)
check("cas valide → TEST", st4 == TEST)

print(f"\nRÉSULTAT e_process : {ok}/{total}")
assert ok == total
