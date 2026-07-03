"""
VALIDATION de la MALÉDICTION DU VAINQUEUR (winner_curse.py) — jugée par calibration.py. Vérifie le BIAIS positif de
l'estimé sélectionné (croissant avec K), la SOUS-COUVERTURE de l'IC naïf (SUR-CONFIANT), la couverture ≥ 1−α de l'IC
simultané (Bonferroni) du sélectionné ET de tous les effets, la correction du cas K=1 (pas de sélection), le prix
(largeur simultanée > naïve), et l'ABSTENTION. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import winner_curse as W
from winner_curse import ABSTENTION, ESTIME
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


rng = random.Random(71)
sigma = 1.0
alpha = 0.05


def biais(K, mus, reps=15000):
    b = 0.0
    for _ in range(reps):
        xs = [rng.gauss(mus[i], sigma) for i in range(K)]
        j = W.selectionne(xs)
        b += xs[j] - mus[j]
    return b / reps


# ─── 1. Biais de l'estimé sélectionné > 0, croissant avec K ───
print("=== Malédiction du vainqueur : biais > 0, croissant avec K ===")
b3 = biais(3, [0] * 3)
b20 = biais(20, [0] * 20)
print(f"   biais K=3 : {b3:.3f} ; K=20 : {b20:.3f}")
check("biais de l'estimé sélectionné > 0 (sur-estimation)", b3 > 0.1)
check("biais croît avec le nombre de candidats K", b20 > b3 + 0.3)

# ─── 2. IC NAÏF sous-couvre μ_ĵ (SUR-CONFIANT) ───
print("=== IC naïf : sous-couverture de l'effet sélectionné (sur-confiance) ===")
K = 10
mus = [0.0] * K          # tous nuls : μ_ĵ = 0
int_naif, int_sim, verit = [], [], []
N = 15000
for _ in range(N):
    xs = [rng.gauss(mus[i], sigma) for i in range(K)]
    j = W.selectionne(xs)
    int_naif.append(W.ic_naif(xs[j], sigma, alpha))
    int_sim.append(W.ic_simultane(xs[j], sigma, K, alpha))
    verit.append(mus[j])
covN = CAL.couverture(int_naif, verit)[0]
covS = CAL.couverture(int_sim, verit)[0]
vN, iN = CAL.verdict_couverture(int_naif, verit, 1 - alpha)
print(f"   couverture IC naïf={covN:.3f} ({vN}) ; IC simultané={covS:.3f} (nominal {1-alpha})")
check("l'IC naïf SOUS-COUVRE l'effet sélectionné (sur-confiant)", covN < 1 - alpha and vN == SURCONFIANT)
check("l'IC simultané (Bonferroni) couvre ≥ 1−α", covS >= 1 - alpha)

# ─── 3. L'IC simultané couvre TOUS les effets ≥ 1−α (Bonferroni) ───
print("=== IC simultané : couvre tous les μ_i simultanément ≥ 1−α ===")
mus2 = [rng.uniform(-1, 1) for _ in range(K)]
tous_couverts = 0
M = 6000
for _ in range(M):
    xs = [rng.gauss(mus2[i], sigma) for i in range(K)]
    if all(W.ic_simultane(xs[i], sigma, K, alpha)[0] <= mus2[i] <= W.ic_simultane(xs[i], sigma, K, alpha)[1] for i in range(K)):
        tous_couverts += 1
print(f"   P(tous les μ_i couverts simultanément) = {tous_couverts/M:.3f} (≥ {1-alpha})")
check("couverture simultanée de TOUS les effets ≥ 1−α", tous_couverts / M >= 1 - alpha)

# ─── 4. K=1 : pas de sélection → IC naïf correct ───
print("=== K=1 (pas de sélection) : IC naïf calibré ===")
c1 = 0
for _ in range(15000):
    x = rng.gauss(0, sigma)
    lo, hi = W.ic_naif(x, sigma, alpha)
    c1 += (lo <= 0 <= hi)
print(f"   couverture K=1 IC naïf = {c1/15000:.3f} (≈ {1-alpha})")
check("sans sélection (K=1), l'IC naïf est calibré", abs(c1 / 15000 - (1 - alpha)) < 0.02)

# ─── 5. Prix de la correction : largeur simultanée > naïve ───
print("=== Largeur : simultané > naïf ===")
wn = (lambda t: t[1] - t[0])(W.ic_naif(2.0, sigma, alpha))
ws = (lambda t: t[1] - t[0])(W.ic_simultane(2.0, sigma, K, alpha))
print(f"   largeur naïf={wn:.3f} ; simultané={ws:.3f}")
check("IC simultané plus large que naïf (prix de la correction)", ws > wn)

# ─── 6. Cas mixte : un vrai effet présent ───
print("=== Cas mixte : un vrai gros effet parmi des nulls ===")
mus3 = [4.0] + [0.0] * (K - 1)
b_mix = biais(K, mus3, 8000)
print(f"   biais (un effet=4) = {b_mix:.3f} (plus petit : le vrai gagnant est peu biaisé)")
check("avec un vrai effet dominant, le biais de sélection diminue", b_mix < b3)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = W.estime([], sigma, alpha)
st2, _ = W.estime([0.5, 1.0], -1.0, alpha)
st3, _ = W.estime([0.5, 1.0], sigma, 1.5)
check("K<1 → ABSTENTION", st1 == ABSTENTION)
check("σ≤0 → ABSTENTION", st2 == ABSTENTION)
check("α hors (0,1) → ABSTENTION", st3 == ABSTENTION)
st4, _ = W.estime([0.5, 2.0, 1.0], sigma, alpha)
check("cas valide → ESTIME", st4 == ESTIME)

print(f"\nRÉSULTAT winner_curse : {ok}/{total}")
assert ok == total
