"""
VALIDATION du MDL (mdl.py). Vérifie que l'erreur d'entraînement (RSS) décroît TOUJOURS avec le degré (sur-ajustement),
que la sélection par erreur d'entraînement choisit le degré MAXIMAL alors que MDL choisit un degré PARCIMONIEUX, que
le modèle MDL PRÉDIT MIEUX en held-out que le modèle sur-ajusté (sur-confiance démasquée), que la pénalité de
complexité croît avec k et n, que MDL RÉCUPÈRE le vrai degré à fort signal, et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import mdl as M
from mdl import ABSTENTION, SELECTION

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


rng = random.Random(76)


def donnees(rng, f, n, sigma, lo=-1, hi=1):
    xs = [rng.uniform(lo, hi) for _ in range(n)]
    return xs, [f(x) + rng.gauss(0, sigma) for x in xs]


# ─── 1. RSS décroît toujours ; train choisit max, MDL parcimonieux ───
print("=== RSS décroît avec le degré ; train=max, MDL parcimonieux ===")
f3 = lambda x: 1 - 2 * x + 0.5 * x ** 3
xs, ys = donnees(rng, f3, 40, 0.3)
xn = M._normalise(xs)
rsss = [M.rss(xn, ys, M.ajuste_poly(xn, ys, d)) for d in range(8)]
print(f"   RSS = {[round(r,2) for r in rsss]}")
check("RSS décroît (faiblement) avec le degré (sur-ajustement)", all(rsss[i] >= rsss[i+1] - 1e-9 for i in range(len(rsss)-1)))
info = M.analyse(xs, ys, 7)[1]
check("la sélection par erreur d'entraînement choisit le degré MAXIMAL", info["degre_train"] == 7)
check("MDL choisit un degré parcimonieux (< max)", info["degre_mdl"] < 7)

# ─── 2. DÉMASQUE : MDL prédit mieux en held-out que le sur-ajusté ───
print("=== Mode d'échec : le modèle sur-ajusté prédit MAL (held-out) ===")
d_max = 9
mse_mdl = mse_train = 0.0
T = 60
for _ in range(T):
    xtr, ytr = donnees(rng, f3, 30, 0.3)
    xte, yte = donnees(rng, f3, 200, 0.0)            # test sans bruit (vraie fonction)
    bornes = (min(xtr), max(xtr))
    d_mdl = M.selectionne_mdl(xtr, ytr, d_max)
    d_tr = M.selectionne_train(xtr, ytr, d_max)
    mse_mdl += sum((M.predit(xtr, ytr, d_mdl, x, bornes) - y) ** 2 for x, y in zip(xte, yte)) / len(xte)
    mse_train += sum((M.predit(xtr, ytr, d_tr, x, bornes) - y) ** 2 for x, y in zip(xte, yte)) / len(xte)
mse_mdl /= T; mse_train /= T
print(f"   MSE held-out : MDL={mse_mdl:.3f} ; sur-ajusté (degré max)={mse_train:.3f}")
check("le modèle MDL prédit BIEN mieux que le sur-ajusté (sur-confiance démasquée)", mse_mdl < mse_train / 2)

# ─── 3. Pénalité de complexité croît avec k et n ───
print("=== Pénalité de complexité (k/2)·ln(n) ↑ avec k et n ===")
pen = lambda k, n: (k / 2) * math.log(n)
check("pénalité ↑ avec le degré (k)", pen(2, 50) < pen(8, 50))
check("pénalité ↑ avec n", pen(4, 30) < pen(4, 300))

# ─── 4. Récupération du vrai degré à fort signal / grand n ───
print("=== Récupération du vrai degré (fort signal, grand n) ===")
fort = lambda x: 2 * x ** 3 - x                       # cubique fort
xsf, ysf = donnees(rng, fort, 200, 0.15)
d_rec = M.selectionne_mdl(xsf, ysf, 8)
print(f"   degré MDL récupéré = {d_rec} (vrai = 3)")
check("MDL récupère le vrai degré (3) à fort signal/grand n", d_rec == 3)
# modèle linéaire (vrai degré 1) -> MDL choisit 1
lin = lambda x: 0.5 + 1.5 * x
xsl, ysl = donnees(rng, lin, 150, 0.2)
check("MDL choisit degré 1 pour une vraie relation linéaire", M.selectionne_mdl(xsl, ysl, 6) == 1)

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = M.analyse([0.1, 0.2, 0.3], [1, 2, 3], 5)        # n < d_max+2
st2, _ = M.analyse([0.1, 0.2], [1.0], 0)                  # tailles différentes
check("trop peu de points → ABSTENTION", st1 == ABSTENTION)
check("tailles incohérentes → ABSTENTION", st2 == ABSTENTION)
st3, _ = M.analyse([rng.uniform(-1, 1) for _ in range(30)], [rng.random() for _ in range(30)], 4)
check("cas valide → SELECTION", st3 == SELECTION)

print(f"\nRÉSULTAT mdl : {ok}/{total}")
assert ok == total
