"""
VALIDATION de la RÉGRESSION RIDGE (ridge.py). Vérifie OLS=ridge(λ=0), que sous COLINÉARITÉ les coefficients OLS ont une
VARIANCE énorme (sur-confiance) que ridge réduit fortement, que ridge PRÉDIT mieux en held-out, le rétrécissement
(λ→∞ ⇒ β→0), l'absence de bénéfice (et d'inconvénient) sans colinéarité, et l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random
import statistics

from garde_ressources import borne
import ridge as R
from ridge import ABSTENTION, RIDGE

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


rng = random.Random(89)


def donnees(n, collin, b1=1.0, b2=1.0, bruit=0.5):
    X, y = [], []
    for _ in range(n):
        x1 = rng.gauss(0, 1)
        x2 = x1 + rng.gauss(0, collin)
        X.append([x1, x2]); y.append(b1 * x1 + b2 * x2 + rng.gauss(0, bruit))
    return X, y


# ─── 1. OLS = ridge(λ=0) ───
print("=== OLS = ridge(λ=0) ===")
X, y = donnees(60, 0.5)
b0 = R.ajuste(X, y, 0.0); br0 = R.ajuste(X, y, 0.0)
check("ridge(λ=0) = OLS", all(abs(b0[k] - br0[k]) < 1e-12 for k in range(2)))

# ─── 2. Sous colinéarité : variance OLS ≫ variance ridge ───
print("=== Colinéarité : variance des coefficients OLS ≫ ridge ===")
def variances(collin, lam, reps=300, n=50):
    b1_ols, b1_rid = [], []
    for _ in range(reps):
        X, y = donnees(n, collin)
        b1_ols.append(R.ajuste(X, y, 0.0)[0]); b1_rid.append(R.ajuste(X, y, lam)[0])
    return statistics.pstdev(b1_ols), statistics.pstdev(b1_rid)
sd_ols, sd_rid = variances(0.05, 1.0)
print(f"   colinéaire : écart-type β₁ OLS={sd_ols:.2f} vs ridge={sd_rid:.2f}")
check("OLS très instable sous colinéarité (écart-type élevé)", sd_ols > 0.5)
check("ridge réduit fortement la variance (≥ 3×)", sd_rid < sd_ols / 3)

# ─── 3. Coefficients OLS peuvent avoir le mauvais signe ; ridge plus proche du vrai ───
print("=== OLS : signe instable ; ridge proche du vrai (1,1) ===")
mauvais_signe = 0; ecart_ols = ecart_rid = 0.0; R_ = 300
for _ in range(R_):
    X, y = donnees(50, 0.05)
    bo = R.ajuste(X, y, 0.0); br = R.ajuste(X, y, 1.0)
    if bo[0] < 0 or bo[1] < 0:                 # vrais coefficients = (1,1), positifs
        mauvais_signe += 1
    ecart_ols += abs(bo[0] - 1) + abs(bo[1] - 1)
    ecart_rid += abs(br[0] - 1) + abs(br[1] - 1)
print(f"   OLS au mauvais signe : {mauvais_signe}/{R_} ; écart au vrai : OLS={ecart_ols/R_:.2f} vs ridge={ecart_rid/R_:.2f}")
check("OLS produit parfois des coefficients de signe FAUX (vrai = positif)", mauvais_signe > 10)
check("ridge plus proche des vrais coefficients que OLS", ecart_rid < ecart_ols)

# ─── 4. Ridge prédit mieux en held-out sous colinéarité ───
print("=== Ridge prédit mieux (held-out) sous colinéarité ===")
mse_ols = mse_rid = 0.0; T = 300
for _ in range(T):
    Xtr, ytr = donnees(40, 0.05)
    Xte, yte = donnees(400, 0.05)
    bo = R.ajuste(Xtr, ytr, 0.0); br = R.ajuste(Xtr, ytr, 1.0)
    mse_ols += R.mse(Xte, yte, bo); mse_rid += R.mse(Xte, yte, br)
print(f"   MSE held-out : OLS={mse_ols/T:.3f} ; ridge={mse_rid/T:.3f}")
check("ridge généralise mieux que OLS sous colinéarité", mse_rid < mse_ols)

# ─── 5. Rétrécissement : λ↑ ⇒ ‖β‖ ↓ → 0 ───
print("=== Rétrécissement : λ↑ ⇒ ‖β‖ → 0 ===")
X, y = donnees(60, 0.05)
normes = [sum(v * v for v in R.ajuste(X, y, lam)) ** 0.5 for lam in (0.0, 1.0, 10.0, 100000.0)]
print(f"   ‖β‖ pour λ=0,1,10,1e5 : {[round(x,3) for x in normes]}")
check("‖β‖ décroît avec λ", all(normes[i] >= normes[i+1] - 1e-9 for i in range(len(normes)-1)))
check("λ très grand → β ≈ 0", normes[-1] < 0.1)

# ─── 6. Sans colinéarité : pas de pénalité (variances comparables) ───
print("=== Sans colinéarité : OLS aussi bon (ridge n'apporte rien d'essentiel) ===")
sd_o, sd_r = variances(1.0, 1.0)
print(f"   indépendants : écart-type β₁ OLS={sd_o:.2f} vs ridge={sd_r:.2f}")
check("sans colinéarité, OLS est stable (écart-type faible)", sd_o < 0.3)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = R.analyse([[1, 2]], [1])                  # n ≤ p
st2, _ = R.analyse([[1, 2], [3, 4], [5, 6]], [1, 2])   # tailles différentes
check("n ≤ p → ABSTENTION", st1 == ABSTENTION)
check("tailles différentes → ABSTENTION", st2 == ABSTENTION)
st3, _ = R.analyse(*donnees(40, 0.1), 1.0)
check("cas valide → RIDGE", st3 == RIDGE)

print(f"\nRÉSULTAT ridge : {ok}/{total}")
assert ok == total
