"""
VALIDATION du FILTRE DE KALMAN ROBUSTE (kalman_robuste.py). Vérifie : bien spécifié ⇒ calibré (couverture ≈ 0.95,
NIS ≈ 1, variance annoncée ≈ MSE réelle = point fixe de Riccati) ; covariance sous-estimée ⇒ SUR-CONFIANT (couverture
s'effondre, NIS>1) DÉTECTÉ par le NIS SANS vérité-terrain ; inflation de covariance RESTAURE la couverture ; trop
d'inflation ⇒ sous-confiance. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import kalman_robuste as KR
from kalman_robuste import ABSTENTION, COHERENT, SURCONFIANT, SOUSCONFIANT

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


def simule(rng, a, q_true, r_true, T):
    x = 0.0; xs = []; ys = []
    for _ in range(T):
        x = a * x + rng.gauss(0, math.sqrt(q_true))
        xs.append(x); ys.append(x + rng.gauss(0, math.sqrt(r_true)))
    return xs, ys


def mesures(rng, a, q_true, r_true, q_a, r_a, inflation, T=2500, runs=4, burn=50):
    """Couverture 95%, NIS moyen, MSE réelle, variance annoncée moyenne (après burn-in), agrégés sur plusieurs runs."""
    cov_t = nis_t = mse_t = var_t = 0.0; cnt = 0
    for _ in range(runs):
        xs, ys = simule(rng, a, q_true, r_true, T)
        res = KR.filtre(ys, a, q_a, r_a, inflation=inflation)
        for t in range(burn, T):
            e, v, xt = res["est"][t], res["var"][t], xs[t]
            cov_t += 1 if abs(xt - e) <= 1.96 * math.sqrt(v) else 0
            mse_t += (xt - e) ** 2; var_t += v; cnt += 1
        nis_t += KR.nis_moyen(res)
    return cov_t / cnt, nis_t / runs, mse_t / cnt, var_t / cnt


rng = random.Random(64)
a, q_true, r_true = 0.95, 1.0, 1.0

# ─── 1. Bien spécifié ⇒ calibré ───
print("=== Bien spécifié : couverture ≈ 0.95, NIS ≈ 1, variance ≈ MSE ===")
cov, nis, mse, varr = mesures(rng, a, q_true, r_true, q_true, r_true, 1.0)
print(f"   couverture={cov:.3f} NIS={nis:.3f} MSE={mse:.3f} var_annoncée={varr:.3f}")
check("couverture 95% ≈ nominal (0.93–0.965)", 0.93 <= cov <= 0.965)
check("NIS ≈ 1 (0.9–1.1)", 0.9 <= nis <= 1.1)
check("variance annoncée ≈ MSE réelle (filtre cohérent)", abs(varr - mse) / mse < 0.1)
# diagnostic COHERENT
xs, ys = simule(rng, a, q_true, r_true, 4000)
verdict, _ = KR.diagnostic(KR.filtre(ys, a, q_true, r_true))
check("diagnostic = COHERENT", verdict == COHERENT)

# ─── 2. Covariance sous-estimée ⇒ SUR-CONFIANT (détecté par NIS) ───
print("=== q sous-estimé : SUR-CONFIANT (couverture s'effondre, NIS>1) ===")
covU, nisU, mseU, varrU = mesures(rng, a, q_true, r_true, 0.05, r_true, 1.0)
print(f"   couverture={covU:.3f} NIS={nisU:.3f} (MSE={mseU:.3f} >> var annoncée={varrU:.3f})")
check("couverture s'effondre (< 0.75) = sur-confiance", covU < 0.75)
check("NIS > 1.5 (innovations trop grandes)", nisU > 1.5)
check("variance annoncée < MSE réelle (sous-estimation)", varrU < mseU)
xsU, ysU = simule(rng, a, q_true, r_true, 4000)
verdictU, nisd = KR.diagnostic(KR.filtre(ysU, a, 0.05, r_true))
check("NIS DÉTECTE la sur-confiance SANS vérité-terrain (verdict SURCONFIANT)", verdictU == SURCONFIANT)

# ─── 3. Inflation de covariance RESTAURE la couverture ───
print("=== Inflation λ : restaure la couverture ===")
covR, nisR, _, _ = mesures(rng, a, q_true, r_true, 0.05, r_true, 4.0)
print(f"   λ=4 sur le filtre sous-spécifié : couverture={covR:.3f} NIS={nisR:.3f}")
check("inflation restaure la couverture (≥ 0.92)", covR >= 0.92)
check("inflation ramène le NIS vers/sous 1 (≤ 1.3)", nisR <= 1.3)

# ─── 4. Trop d'inflation ⇒ sous-confiance (sur les INNOVATIONS, détectée par NIS) ───
# (NB la couverture d'ÉTAT reste ~0.95 à inflation extrême : K→1, le filtre suit la mesure et P→r par dégénérescence ;
#  le signal fiable de sur-inflation est le NIS, pas la couverture d'état.)
print("=== Sur-inflation : sous-confiance des innovations (NIS<1) ===")
covO, nisO, _, _ = mesures(rng, a, q_true, r_true, q_true, r_true, 25.0)
print(f"   λ=25 : couverture_état={covO:.3f} NIS={nisO:.3f}")
check("sur-inflation → NIS < 0.7 (innovations sur-couvertes = sous-confiance)", nisO < 0.7)
verdictO, _ = KR.diagnostic(KR.filtre(simule(rng, a, q_true, r_true, 4000)[1], a, q_true, r_true, inflation=25.0))
check("diagnostic sur-inflation = SOUSCONFIANT", verdictO == SOUSCONFIANT)

# ─── 5. Régime permanent = point fixe de Riccati ───
print("=== Variance en régime permanent = point fixe de Riccati ===")
Pss = KR.steady_state_P(a, q_true, r_true)
Pm = a * a * Pss + q_true; K = Pm / (Pm + r_true)
check("P_ss = (1−K)(a²P_ss+q) (point fixe)", abs(Pss - (1 - K) * Pm) < 1e-9)
check("MSE réelle bien spécifiée ≈ P_ss", abs(mse - Pss) / Pss < 0.1)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = KR.analyse([], a, q_true, r_true)
st2, _ = KR.analyse([1.0, 2.0], a, q_true, -1.0)
check("données vides → ABSTENTION", st1 == ABSTENTION)
check("r ≤ 0 → ABSTENTION", st2 == ABSTENTION)
st3, _ = KR.analyse([1.0, 0.5, 1.2, 0.8] * 20, a, q_true, r_true)
check("cas valide → verdict", st3 in (COHERENT, SURCONFIANT, SOUSCONFIANT))

print(f"\nRÉSULTAT kalman_robuste : {ok}/{total}")
assert ok == total
