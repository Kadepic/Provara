"""
VALIDATION de la BANDE DKW (dkw.py). Vérifie la formule ε, l'encadrement F_inf≤F_n≤F_sup∈[0,1], la COUVERTURE
SIMULTANÉE ≥ 1−α (distribution-free : uniforme, normale, exponentielle), que des IC PONCTUELS (Wald) SOUS-COUVRENT la
courbe entière (multiplicité = sur-confiance), que la CDF empirique n'est pas exacte, que ε→0 avec n, et l'intervalle
de quantile dérivé. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import dkw as D
from dkw import ABSTENTION, BANDE

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


_PHI = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
# (sampler, CDF vraie, grille x = quantiles 0.1..0.9)
DISTRIBS = {
    "uniforme": (lambda rng: rng.random(), lambda x: min(1, max(0, x)),
                 [0.1 * i for i in range(1, 10)]),
    "normale": (lambda rng: rng.gauss(0, 1), _PHI,
                [-1.2816, -0.8416, -0.5244, -0.2533, 0.0, 0.2533, 0.5244, 0.8416, 1.2816]),
    "exponentielle": (lambda rng: -math.log(1 - rng.random()), lambda x: 1 - math.exp(-x) if x > 0 else 0.0,
                      [-math.log(1 - q) for q in [0.1 * i for i in range(1, 10)]]),
}

rng = random.Random(65)

# ─── 1. ε + encadrement ───
print("=== ε-DKW + encadrement F_inf ≤ F_n ≤ F_sup ∈ [0,1] ===")
check("ε = √(ln(2/α)/(2n))", abs(D.epsilon(200, 0.05) - math.sqrt(math.log(2/0.05)/400)) < 1e-12)
enc_ok = True
for _ in range(2000):
    ech = [rng.gauss(0, 1) for _ in range(rng.randint(20, 80))]
    _, b = D.bande(ech, 0.1)
    for x in (-2, -0.5, 0.7, 3):
        lo, hi = D.proba_seuil(b, x); fn = D.F_n(b, x)
        if not (0 <= lo <= fn <= hi <= 1):
            enc_ok = False
check("0 ≤ F_inf ≤ F_n ≤ F_sup ≤ 1", enc_ok)

# ─── 2 & 3. Couverture simultanée ≥ 1−α, distribution-free ───
print("=== Couverture SIMULTANÉE ≥ 1−α (distribution-free) ===")
alpha = 0.10
n = 80
TRIALS = 2000
for nom, (samp, F, grid) in DISTRIBS.items():
    couv = 0
    for _ in range(TRIALS):
        ech = [samp(rng) for _ in range(n)]
        _, b = D.bande(ech, alpha)
        if D.couvre(b, F):
            couv += 1
    c = couv / TRIALS
    print(f"   {nom:14s}: couverture bande DKW = {c:.3f} (≥ {1-alpha})")
    check(f"DKW couvre ≥ 1−α ({nom})", c >= 1 - alpha)

# ─── 4. IC ponctuels (Wald) SOUS-COUVRENT la courbe (multiplicité = sur-confiance) ───
print("=== IC ponctuels (Wald) sous-couvrent toute la courbe (sur-confiance) ===")
samp, F, grid = DISTRIBS["normale"]
z = 1.96   # niveau ponctuel 1−α = 0.95
couv_dkw_grid = couv_pt = 0
TR = 3000
for _ in range(TR):
    ech = [samp(rng) for _ in range(n)]
    _, b = D.bande(ech, 0.05)
    ok_dkw = ok_pt = True
    for x in grid:
        fn = D.F_n(b, x); fx = F(x)
        if abs(fn - fx) > b["eps"]:
            ok_dkw = False
        hw = z * math.sqrt(max(fn * (1 - fn), 1e-9) / n)   # demi-largeur Wald ponctuelle
        if abs(fn - fx) > hw:
            ok_pt = False
    couv_dkw_grid += ok_dkw; couv_pt += ok_pt
cdkw = couv_dkw_grid / TR; cpt = couv_pt / TR
print(f"   sur la grille : DKW={cdkw:.3f} (≥0.95) ; ponctuel Wald={cpt:.3f} (< 0.95)")
check("DKW couvre la grille ≥ 1−α", cdkw >= 0.95)
check("les IC ponctuels SOUS-COUVRENT la courbe (< 1−α = sur-confiant)", cpt < 0.95)

# ─── 5. CDF empirique pas exacte + ε→0 ───
print("=== CDF empirique ≠ vérité ; ε → 0 avec n ===")
ech = [rng.gauss(0, 1) for _ in range(100)]
_, b = D.bande(ech, 0.05)
check("sup|F_n − F| > 0 (l'empirique n'est PAS la vérité)", D.ks_statistique(b, _PHI) > 0)
check("ε décroît avec n", D.epsilon(50, 0.05) > D.epsilon(500, 0.05) > D.epsilon(5000, 0.05))

# ─── 6. Intervalle de quantile contient le vrai quantile ───
print("=== Intervalle de quantile (dérivé de la bande) ===")
couvq = 0; TQ = 2000
for _ in range(TQ):
    ech = [rng.random() for _ in range(120)]          # uniforme : médiane vraie = 0.5
    _, b = D.bande(ech, 0.05)
    qlo, qhi = D.intervalle_quantile(b, 0.5)
    lo = qlo if qlo is not None else -1e9
    hi = qhi if qhi is not None else 1e9
    if lo <= 0.5 <= hi:
        couvq += 1
print(f"   couverture de la médiane (uniforme) = {couvq/TQ:.3f} (≥ 0.95)")
check("l'intervalle de quantile contient le vrai quantile ≥ 1−α", couvq / TQ >= 0.95)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = D.bande([], 0.05)
st2, _ = D.bande([1, 2, 3], 1.5)
check("échantillon vide → ABSTENTION", st1 == ABSTENTION)
check("α hors (0,1) → ABSTENTION", st2 == ABSTENTION)
st3, _ = D.bande([1, 2, 3], 0.05)
check("cas valide → BANDE", st3 == BANDE)

print(f"\nRÉSULTAT dkw : {ok}/{total}")
assert ok == total
