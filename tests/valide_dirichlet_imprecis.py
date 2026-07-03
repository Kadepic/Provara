"""
VALIDATION du DIRICHLET IMPRÉCIS (dirichlet_imprecis.py) — jugé par calibration.py. Vérifie les bornes algébriques,
l'encadrement du MLE, la cohérence (Σbas ≤ 1 ≤ Σhaut), l'honnêteté sur le zéro, l'INVARIANCE DE REPRÉSENTATION
(signature IDM, vs Laplace K-dépendant), la largeur s/(N+s) qui rétrécit avec N, et DÉMASQUE la sur-confiance du MLE :
log-loss prédictive INFINIE (assigne 0 à l'inobservé qui réapparaît) et couverture de la vraie proba qui s'effondre
(SUR-CONFIANT) là où l'intervalle IDM tient. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import dirichlet_imprecis as D
from dirichlet_imprecis import ABSTENTION, BORNES
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


rng = random.Random(54)


def multinomial(rng, p, n):
    counts = [0] * len(p)
    for _ in range(n):
        u = rng.random(); c = 0.0
        for k, pk in enumerate(p):
            c += pk
            if u <= c:
                counts[k] += 1; break
        else:
            counts[-1] += 1
    return counts


# ─── 1. Bornes algébriques + encadrement du MLE + cohérence ───
print("=== Bornes, encadrement du MLE, cohérence ===")
alg_ok = brak_ok = coher_ok = True
for _ in range(3000):
    K = rng.randint(2, 7)
    counts = [rng.randint(0, 20) for _ in range(K)]
    s = rng.choice([1.0, 2.0])
    N = sum(counts)
    b = D.bornes(counts, s)
    pmle = D.mle(counts)
    for k in range(K):
        lo, hi = b[k]
        if abs(lo - counts[k] / (N + s)) > 1e-12 or abs(hi - (counts[k] + s) / (N + s)) > 1e-12:
            alg_ok = False
        if not (lo - 1e-12 <= pmle[k] <= hi + 1e-12 and lo <= hi):
            brak_ok = False
    sl, sh = sum(l for l, _ in b), sum(h for _, h in b)
    if not (sl <= 1 + 1e-12 <= sh + 1e-12 and abs(sl - N / (N + s)) < 1e-9 and abs(sh - (N + K * s) / (N + s)) < 1e-9):
        coher_ok = False
check("bornes = (n/(N+s), (n+s)/(N+s)) exactes", alg_ok)
check("encadrent le MLE et bas ≤ haut", brak_ok)
check("cohérence : Σbas = N/(N+s) ≤ 1 ≤ Σhaut = (N+Ks)/(N+s)", coher_ok)

# ─── 2. Honnêteté sur le zéro ───
print("=== Honnêteté sur la catégorie jamais observée ===")
b0 = D.bornes([10, 0, 0], s=2.0)
print(f"   counts=[10,0,0], s=2 -> {[ (round(l,3),round(h,3)) for l,h in b0 ]}")
check("zéro-compte : MLE = 0 (fausse certitude)", D.mle([10, 0, 0])[1] == 0.0)
check("zéro-compte : IDM bas = 0 MAIS haut = s/(N+s) > 0 (honnête)", b0[1][0] == 0.0 and b0[1][1] > 0.0
      and abs(b0[1][1] - 2.0 / 12.0) < 1e-12)

# ─── 3. Invariance de représentation (signature IDM) vs Laplace K-dépendant ───
print("=== Invariance de représentation : IDM stable, Laplace bouge avec K ===")
nA, N = 5, 13
i4 = D.intervalle_evenement(nA, N, 1.0)
i9 = D.intervalle_evenement(nA, N, 1.0)
lap4 = (nA + 1) / (N + 4)
lap9 = (nA + 1) / (N + 9)
print(f"   IDM(A) K=4={tuple(round(x,4) for x in i4)} K=9={tuple(round(x,4) for x in i9)} ; Laplace K=4={lap4:.4f} K=9={lap9:.4f}")
check("IDM(A) ne dépend que de (n_A, N), pas de K", i4 == i9)
check("Laplace(A) CHANGE avec K (non invariant)", abs(lap4 - lap9) > 0.05)

# ─── 4. Largeur = s/(N+s), indépendante des comptes, rétrécit avec N ───
print("=== Largeur d'imprécision s/(N+s) : indépendante des comptes, → 0 avec N ===")
larg_ok = True
for counts in ([0, 20], [10, 10], [19, 1]):
    for (l, h) in D.bornes(counts, 1.0):
        if abs((h - l) - 1.0 / (sum(counts) + 1.0)) > 1e-12:
            larg_ok = False
check("largeur identique pour toutes catégories = s/(N+s)", larg_ok)
w_petit = D.bornes([2, 3], 1.0)[0]
w_grand = D.bornes([200, 300], 1.0)[0]
check("largeur rétrécit avec N (apprentissage)", (w_petit[1] - w_petit[0]) > (w_grand[1] - w_grand[0]))

# ─── 5. DÉMASQUE : log-loss prédictive du MLE = ∞ (assigne 0 à l'inobservé) ; IDM finie ───
print("=== Sur-confiance du MLE : log-loss prédictive infinie sur l'inobservé ===")
p_vrai = [0.5, 0.3, 0.15, 0.04, 0.01]   # 2 catégories rares
mle_inf = 0
ll_idm_total = 0.0
n_test_total = 0
for _ in range(400):
    counts = multinomial(rng, p_vrai, 15)   # peu de données -> catégories rares souvent à 0
    pm = D.mle(counts)
    pi = D.predictif_credal(counts, s=1.0)
    test = multinomial(rng, p_vrai, 8)
    for k, tk in enumerate(test):
        for _ in range(tk):
            if pm[k] <= 0.0:
                mle_inf += 1
            ll_idm_total += -math.log(pi[k])
            n_test_total += 1
print(f"   tirages test où le MLE assigne proba 0 (log-loss=∞) : {mle_inf} ; log-loss moyenne IDM = {ll_idm_total/n_test_total:.3f} (finie)")
check("le MLE assigne proba 0 à des catégories qui APPARAISSENT (sur-confiance ∞)", mle_inf > 0)
check("le prédictif IDM reste fini partout (log-loss bornée)", math.isfinite(ll_idm_total) and ll_idm_total > 0)

# ─── 6. Couverture : l'intervalle IDM tient, le point MLE s'effondre (SUR-CONFIANT) ───
print("=== Couverture de la vraie proba : IDM vs point MLE ===")
int_idm, int_mle, verites = [], [], []
for _ in range(1500):
    counts = multinomial(rng, p_vrai, 18)
    b = D.bornes(counts, 2.0)
    pm = D.mle(counts)
    for k in range(len(p_vrai)):
        int_idm.append(b[k]); int_mle.append((pm[k], pm[k])); verites.append(p_vrai[k])
covI = CAL.couverture(int_idm, verites)[0]
covM = CAL.couverture(int_mle, verites)[0]
vM, iM = CAL.verdict_couverture(int_mle, verites, 0.80)
print(f"   couverture IDM = {covI:.3f} ; couverture point MLE = {covM:.3f} ({vM})")
check("l'intervalle IDM couvre bien plus que le point MLE (+0.3)", covI - covM > 0.3)
check("le point MLE est SUR-CONFIANT (sous-couvre fortement)", vM == SURCONFIANT and covM < 0.6)

# ─── 7. ABSTENTION sur force a priori invalide ───
print("=== ABSTENTION si N+s ≤ 0 ===")
st, raison = D.estime([], indice=None, s=0.0)
print(f"   counts=[], s=0 -> {st} ({raison})")
check("N+s ≤ 0 → ABSTENTION", st == ABSTENTION)
st2, _ = D.estime([3, 1], indice=0, s=1.0)
check("cas valide → BORNES", st2 == BORNES)

print(f"\nRÉSULTAT dirichlet_imprecis : {ok}/{total}")
assert ok == total
