"""
VALIDATION des JEUX À SOMME NULLE (jeux_zero_somme.py). Vérifie le théorème MINIMAX (encadrement L≤v≤U qui se
resserre, maximin = minimax), la GARANTIE de sécurité (la stratégie maximin garantit ≥ v contre tout adversaire,
mieux que toute autre), le DÉMASQUE (best-response à un adversaire présumé = EXPLOITABLE sous la valeur), la
convergence du jeu fictif, les jeux connus (matching pennies, dominance), et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import jeux_zero_somme as J
from jeux_zero_somme import ABSTENTION, JEU

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


rng = random.Random(70)


def jeu_alea(rng, m, n):
    return [[rng.uniform(-5, 5) for _ in range(n)] for _ in range(m)]


# ─── 1. Théorème minimax : L ≤ v ≤ U, encadrement serré ───
print("=== Théorème minimax : maximin = minimax (encadrement serré) ===")
gap_max = 0.0
ordre_ok = True
for _ in range(200):
    A = jeu_alea(rng, rng.randint(2, 4), rng.randint(2, 4))
    v, x, y, (L, U) = J.jeu_fictif(A, 8000)
    if not (L <= U + 1e-9):
        ordre_ok = False
    gap_max = max(gap_max, U - L)
print(f"   écart maximin/minimax max (U−L) sur 200 jeux = {gap_max:.3f}")
check("L (maximin) ≤ U (minimax) toujours", ordre_ok)
check("l'encadrement se resserre (U−L petit) = maximin ≈ minimax = valeur", gap_max < 0.15)

# ─── 2. GARANTIE de sécurité : maximin ≥ toute autre stratégie ───
print("=== Garantie : la stratégie maximin garantit le mieux contre tout adversaire ===")
garantie_ok = True
for _ in range(300):
    m, n = rng.randint(2, 4), rng.randint(2, 4)
    A = jeu_alea(rng, m, n)
    v, x, y, _ = J.jeu_fictif(A, 6000)
    sec_max = J.securite_ligne(A, x)
    # comparer à des stratégies pures et aléatoires : aucune ne doit garantir nettement plus
    for i in range(m):
        pure = [1.0 if k == i else 0.0 for k in range(m)]
        if J.securite_ligne(A, pure) > sec_max + 0.1:
            garantie_ok = False
check("aucune stratégie (pure) ne garantit nettement plus que la maximin", garantie_ok)

# ─── 3. DÉMASQUE : best-response à un adversaire présumé = exploitable ───
print("=== Mode d'échec : best-response à un adversaire présumé ===")
pennies = [[1, -1], [-1, 1]]
v, x, y, _ = J.jeu_fictif(pennies, 5000)
i0 = J.meilleure_reponse_ligne(pennies, [0.5, 0.5])     # BR à l'adversaire présumé uniforme
pire_BR = min(pennies[i0])                               # si l'adversaire dévie pour exploiter
pire_maximin = J.securite_ligne(pennies, x)
print(f"   matching pennies : valeur≈{v:.2f} ; pire-cas BR={pire_BR} ; pire-cas maximin={pire_maximin:.2f}")
check("le best-response (pur) est EXPLOITABLE sous la valeur", pire_BR < v - 0.5)
check("la stratégie maximin garantit ≥ valeur (non exploitable)", pire_maximin >= v - 0.05)
# général : la sécurité du BR-à-présumé ≤ sécurité maximin
expl = 0
for _ in range(300):
    m, n = rng.randint(2, 4), rng.randint(2, 4)
    A = jeu_alea(rng, m, n)
    v2, x2, _, _ = J.jeu_fictif(A, 4000)
    y0 = [1.0 / n] * n
    iBR = J.meilleure_reponse_ligne(A, y0)
    pureBR = [1.0 if k == iBR else 0.0 for k in range(m)]
    if J.securite_ligne(A, pureBR) < J.securite_ligne(A, x2) - 0.1:
        expl += 1
print(f"   jeux où le BR-à-présumé est strictement moins sûr que maximin : {expl}/300")
check("le BR à un adversaire présumé est souvent strictement exploitable vs maximin", expl > 100)

# ─── 4. Convergence du jeu fictif (plus d'itérations → plus serré) ───
print("=== Convergence du jeu fictif ===")
A = jeu_alea(rng, 3, 3)
_, _, _, (L1, U1) = J.jeu_fictif(A, 200)
_, _, _, (L2, U2) = J.jeu_fictif(A, 8000)
print(f"   gap iters=200 : {U1-L1:.3f} → iters=8000 : {U2-L2:.3f}")
check("plus d'itérations resserrent l'encadrement", (U2 - L2) <= (U1 - L1) + 1e-9)

# ─── 5. Jeux connus ───
print("=== Jeux connus ===")
check("matching pennies : valeur ≈ 0", abs(v) < 0.05)
check("matching pennies : stratégie optimale ≈ (0.5, 0.5)", abs(x[0] - 0.5) < 0.05)
# jeu à dominance : ligne 0 domine -> valeur = max-min de la ligne dominante
dom = [[4, 5, 6], [1, 0, 2]]
vd, xd, _, _ = J.jeu_fictif(dom, 3000)
check("jeu à dominance : valeur = min de la ligne dominante (4)", abs(vd - 4) < 0.05 and xd[0] > 0.95)
# valeur dans [min A, max A]
A2 = jeu_alea(rng, 3, 3)
vv, _, _, _ = J.jeu_fictif(A2, 4000)
plat = [c for r in A2 for c in r]
check("valeur ∈ [min A, max A]", min(plat) - 1e-9 <= vv <= max(plat) + 1e-9)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = J.analyse([])
st2, _ = J.analyse([[1, 2], [3]])
check("matrice vide → ABSTENTION", st1 == ABSTENTION)
check("matrice mal formée → ABSTENTION", st2 == ABSTENTION)
st3, _ = J.analyse([[0, 1], [1, 0]])
check("matrice valide → JEU", st3 == JEU)

print(f"\nRÉSULTAT jeux_zero_somme : {ok}/{total}")
assert ok == total
