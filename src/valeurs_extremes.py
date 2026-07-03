"""
PALIER 2 — VALEURS EXTRÊMES / RISQUE DE QUEUE (VaR, brique 33, 2026-06-25).

« Quelle est la probabilité — ou la magnitude — d'un événement RARE qu'on n'a peut-être jamais observé ? » (crue
centennale, krach, perte extrême). L'empirique échoue dans la QUEUE (trop peu, voire zéro donnée au-delà du max). La
théorie des valeurs extrêmes l'extrapole honnêtement par PEAKS-OVER-THRESHOLD (POT) :

  on garde les DÉPASSEMENTS d'un seuil u élevé ; au-dessus de u, leur loi tend vers une PARETO GÉNÉRALISÉE (GPD(ξ,σ)).
  D'où :  VaR_p = u + (σ/ξ)·[ ((1−p)/ζ_u)^{−ξ} − 1 ]      P(X>x) = ζ_u·(1 + ξ(x−u)/σ)^{−1/ξ}      (ζ_u = N_u/n)

ξ > 0 = queue lourde (risque sous-estimé par une gaussienne), ξ = 0 = exponentielle, ξ < 0 = queue bornée. On estime
(ξ,σ) par méthode des moments, et l'INCERTITUDE par bootstrap des dépassements. INVARIANT (jugé par calibration.py) :
l'IC du VaR couvre la vraie valeur ~confiance sur une loi connue, là où l'empirique extrapolé ment. ABSTENTION si trop
peu de dépassements (queue non estimable). Pur Python.
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_DEPASS = 20


def ajuste_gpd(depassements):
    """Estime (ξ, σ) d'une GPD par méthode des moments. Renvoie None si trop peu / variance nulle."""
    e = [float(v) for v in depassements if v > 0]
    n = len(e)
    if n < N_MIN_DEPASS:
        return None
    m = sum(e) / n
    var = sum((v - m) ** 2 for v in e) / n
    if var <= 0 or m <= 0:
        return None
    xi = 0.5 * (1.0 - m * m / var)
    sigma = m * (1.0 - xi)
    if sigma <= 0:
        return None
    return (xi, sigma)


def _seuil(donnees, q):
    xs = sorted(float(v) for v in donnees)
    i = q * (len(xs) - 1)
    lo = int(i)
    return xs[lo] if lo + 1 >= len(xs) else xs[lo] * (1 - (i - lo)) + xs[lo + 1] * (i - lo)


def var_pot(donnees, p, seuil_quantile=0.90):
    """VaR au niveau p (ex. 0.99) par POT. Renvoie la valeur ou None si inestimable."""
    x = [float(v) for v in donnees]
    n = len(x)
    u = _seuil(x, seuil_quantile)
    dep = [v - u for v in x if v > u]
    g = ajuste_gpd(dep)
    if g is None:
        return None
    xi, sigma = g
    zeta = len(dep) / n
    r = (1.0 - p) / zeta
    if abs(xi) < 1e-6:
        return u + sigma * (-math.log(r))
    return u + (sigma / xi) * (r ** (-xi) - 1.0)


def proba_depassement(donnees, x_seuil, seuil_quantile=0.90):
    """P(X > x_seuil) par POT (pour x_seuil > u). Renvoie une probabilité ou None."""
    x = [float(v) for v in donnees]
    n = len(x)
    u = _seuil(x, seuil_quantile)
    dep = [v - u for v in x if v > u]
    g = ajuste_gpd(dep)
    if g is None or x_seuil <= u:
        return None
    xi, sigma = g
    zeta = len(dep) / n
    base = 1.0 + xi * (x_seuil - u) / sigma
    if base <= 0:
        return 0.0
    return zeta * base ** (-1.0 / xi) if abs(xi) > 1e-6 else zeta * math.exp(-(x_seuil - u) / sigma)


def var_pot_ic(donnees, p, confiance=0.90, seuil_quantile=0.90, n_boot=600, seed=0):
    """VaR POT + intervalle de confiance par bootstrap des dépassements. Renvoie (ESTIMATION, (var, (bas, haut)),
    confiance) ou ABSTENTION."""
    x = [float(v) for v in donnees]
    u = _seuil(x, seuil_quantile)
    dep = [v - u for v in x if v > u]
    n = len(x)
    if len(dep) < N_MIN_DEPASS:
        return (ABSTENTION, None, f"trop peu de dépassements (N_u={len(dep)} < {N_MIN_DEPASS})")
    point = var_pot(x, p, seuil_quantile)
    if point is None:
        return (ABSTENTION, None, "queue non estimable (GPD non ajustable)")
    rng = random.Random(seed)
    zeta = len(dep) / n
    boot = []
    for _ in range(n_boot):
        ech = [dep[rng.randrange(len(dep))] for _ in range(len(dep))]
        g = ajuste_gpd(ech)
        if g is None:
            continue
        xi, sigma = g
        r = (1.0 - p) / zeta
        v = u + (sigma * (-math.log(r)) if abs(xi) < 1e-6 else (sigma / xi) * (r ** (-xi) - 1.0))
        boot.append(v)
    if len(boot) < 50:
        return (ABSTENTION, None, "bootstrap instable (queue trop incertaine)")
    boot.sort()
    a = (1.0 - confiance) / 2.0
    return (ESTIMATION, (point, (boot[int(a * len(boot))], boot[min(len(boot) - 1, int((1 - a) * len(boot)))])), confiance)


def formule(res, p=0.99) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer le risque de queue : {res[2]}."
    var, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Niveau de risque extrême (VaR {round(p*100,2)}%) ≈ {var:.2f} (à {round(conf*100)}% entre {bas:.2f} et "
            f"{haut:.2f}). Extrapolé dans la queue, donc incertain — mais honnête sur cette incertitude.")


if __name__ == "__main__":
    print("=== VALEURS EXTRÊMES / VaR (POT-GPD) ===\n")
    rng = random.Random(0)
    # Pareto(alpha=3) : P(X>x)=x^-3 (x>=1) ; vrai VaR_p = (1-p)^(-1/3)
    donnees = [(1.0 - rng.random()) ** (-1.0 / 3.0) for _ in range(3000)]
    for p in (0.99, 0.999):
        vrai = (1 - p) ** (-1 / 3)
        print(f"  p={p} : vrai VaR={vrai:.2f} ;", formule(var_pot_ic(donnees, p, 0.90), p))
