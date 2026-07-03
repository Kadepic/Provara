"""
VALIDATION de la COVARIANCE EN GRANDE DIMENSION (covariance_grande_dim.py). Vérifie la méthode de Jacobi
(valeurs propres exactes), la loi de MARCHENKO-PASTUR (étalement des valeurs propres dans le support, alors que la
vraie covariance est I), la SUR-CONFIANCE (max≫1, conditionnement qui explose, corrélations fantômes), et la
CORRECTION par rétrécissement (conditionnement et erreur d'estimation réduits). Pur Python, léger.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import covariance_grande_dim as CG
from covariance_grande_dim import ABSTENTION, ANALYSE

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


rng = random.Random(77)


def gauss_iid(rng, n, p):
    return [[rng.gauss(0, 1) for _ in range(p)] for _ in range(n)]


# ─── 1. Jacobi : valeurs propres exactes ───
print("=== Méthode de Jacobi : valeurs propres ===")
ev = CG.valeurs_propres([[2, 1], [1, 2]])
check("eigs([[2,1],[1,2]]) = (1, 3)", abs(ev[0] - 1) < 1e-9 and abs(ev[1] - 3) < 1e-9)
A = [[4, 1, 0], [1, 3, 1], [0, 1, 2]]
ev3 = CG.valeurs_propres(A)
check("somme des valeurs propres = trace", abs(sum(ev3) - 9) < 1e-9)
prod = ev3[0] * ev3[1] * ev3[2]
check("produit des valeurs propres = déterminant (18)", abs(prod - 18) < 1e-6)

# ─── 2. Loi de Marchenko-Pastur : étalement dans le support (vraie Σ=I) ───
print("=== Marchenko-Pastur : valeurs propres dans le support [(1−√c)²,(1+√c)²] ===")
p, n = 20, 40
lo_mp, hi_mp = CG.bornes_marchenko_pastur(p, n)
viol = 0; tests = 0
for _ in range(60):
    eigs = CG.valeurs_propres(CG.covariance_echantillon(gauss_iid(rng, n, p)))
    for e in eigs:
        tests += 1
        if not (0.6 * lo_mp - 0.05 <= e <= 1.25 * hi_mp):   # marge de fluctuation à n fini
            viol += 1
print(f"   c={p/n}, support MP=[{lo_mp:.2f},{hi_mp:.2f}] ; {viol}/{tests} hors support élargi")
check("valeurs propres dans le support MP (à la marge de fluctuation près)", viol == 0)

# ─── 3. SUR-CONFIANCE : étalement ≫ vérité, conditionnement ↑ avec c ───
print("=== Sur-confiance : étalement et conditionnement croissent avec p/n ===")
def conds(p, n, reps=30):
    cmax = sp = 0.0
    for _ in range(reps):
        eigs = CG.valeurs_propres(CG.covariance_echantillon(gauss_iid(rng, n, p)))
        cmax += CG.conditionnement(eigs); sp += eigs[-1]
    return cmax / reps, sp / reps
cond_faible, max_faible = conds(20, 200)
cond_fort, max_fort = conds(20, 30)
print(f"   c=0.1 : cond≈{cond_faible:.1f}, λ_max≈{max_faible:.2f} ; c=0.67 : cond≈{cond_fort:.1f}, λ_max≈{max_fort:.2f}")
check("λ_max ≫ 1 alors que la vraie valeur propre = 1 (sur-confiance)", max_fort > 2.0)
check("conditionnement explose quand p/n augmente", cond_fort > cond_faible * 3)

# ─── 4. Corrélations fantômes (vraie corrélation = 0) ───
print("=== Corrélations fantômes en grande dimension ===")
def max_corr(p, n, reps=20):
    return sum(CG.max_correlation_hors_diag(CG.covariance_echantillon(gauss_iid(rng, n, p))) for _ in range(reps)) / reps
mc_petit = max_corr(5, 40); mc_grand = max_corr(40, 40)
print(f"   max |corr| hors-diag : p=5 → {mc_petit:.2f} ; p=40 → {mc_grand:.2f} (vraie = 0)")
check("corrélations fantômes croissent avec la dimension", mc_grand > mc_petit + 0.1)
check("corrélation fantôme notable malgré une vraie corrélation nulle", mc_grand > 0.4)

# ─── 5. CORRECTION : le rétrécissement réduit conditionnement et erreur ───
print("=== Rétrécissement : conditionnement et erreur d'estimation réduits ===")
p, n = 20, 30
I = [[1.0 if i == j else 0.0 for j in range(p)] for i in range(p)]
cond_brut = cond_retr = err_brut = err_retr = 0.0
REP = 40
for _ in range(REP):
    X = gauss_iid(rng, n, p)
    S = CG.covariance_echantillon(X)
    Sr = CG.retrecissement(S, 0.5)
    cond_brut += CG.conditionnement(CG.valeurs_propres(S))
    cond_retr += CG.conditionnement(CG.valeurs_propres(Sr))
    err_brut += CG.frobenius(S, I); err_retr += CG.frobenius(Sr, I)
print(f"   conditionnement : brut≈{cond_brut/REP:.1f} → rétréci≈{cond_retr/REP:.1f}")
print(f"   erreur ‖·−I‖_F : brut≈{err_brut/REP:.2f} → rétréci≈{err_retr/REP:.2f}")
check("le rétrécissement réduit le conditionnement", cond_retr < cond_brut)
check("le rétrécissement réduit l'erreur d'estimation (plus proche de la vérité)", err_retr < err_brut)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = CG.analyse([[1.0, 2.0]])
st2, _ = CG.analyse([[1.0, 2.0], [1.0]])
check("n<2 → ABSTENTION", st1 == ABSTENTION)
check("dimensions incohérentes → ABSTENTION", st2 == ABSTENTION)
st3, _ = CG.analyse(gauss_iid(rng, 20, 5))
check("cas valide → ANALYSE", st3 == ANALYSE)

print(f"\nRÉSULTAT covariance_grande_dim : {ok}/{total}")
assert ok == total
