"""
PALIER 2 — PRÉVISION AUTO-RÉGRESSIVE À h PAS, incertitude CROISSANTE avec l'horizon (brique 46, 2026-06-26).

« Prévoir une série DYNAMIQUE (température, stock, charge) plusieurs pas en avant. » Plus on regarde loin, plus c'est
incertain : les erreurs s'ACCUMULENT. L'erreur classique = garder la même largeur d'intervalle qu'à 1 pas → on est trop
sûr de soi aux horizons lointains (SUR-CONFIANCE). Distinct de `prevision.py` (tendance/saison à 1 pas) : ici la
DYNAMIQUE (auto-corrélation) et l'horizon.

Modèle AR(1) : y_t = c + φ·y_{t−1} + ε_t, ε ~ N(0, σ²). Prévision à h pas et sa variance :
  ŷ_{t+h} = μ + φ^h·(y_t − μ)    (μ = c/(1−φ))      Var(erreur_h) = σ²·(1 − φ^{2h})/(1 − φ²)
La variance CROÎT avec h (jusqu'à la variance stationnaire σ²/(1−φ²)). INVARIANT (jugé par calibration.py) :
l'intervalle à h pas couvre la vraie valeur future ~confiance À CHAQUE horizon, là où l'intervalle à largeur fixe
(variance 1 pas) sous-couvre aux horizons lointains. ABSTENTION si série trop courte / non stationnaire. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 30


def _invnorm(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p hors (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def ar1_fit(serie):
    """Estime (c, φ, σ²) d'un AR(1) par OLS sur les paires (y_{t−1}, y_t). Renvoie un dict ou None."""
    n = len(serie)
    if n < 3:
        return None
    xlag = serie[:-1]
    ycur = serie[1:]
    m = len(xlag)
    mx = sum(xlag) / m
    my = sum(ycur) / m
    sxx = 0.0
    sxy = 0.0
    for i in range(m):
        dx = xlag[i] - mx
        sxx += dx * dx
        sxy += dx * (ycur[i] - my)
    if sxx <= 0:
        return None
    phi = sxy / sxx
    c = my - phi * mx
    rss = 0.0
    for i in range(m):
        r = ycur[i] - (c + phi * xlag[i])
        rss += r * r
    sigma2 = rss / max(1, m - 2)
    return {"c": c, "phi": phi, "sigma2": sigma2, "dernier": serie[-1]}


def prevoit_h(modele, h: int, confiance: float = 0.90):
    """Prévision à h pas + intervalle dont la largeur CROÎT avec h. Renvoie (mean, (bas, haut), var)."""
    phi = modele["phi"]
    c = modele["c"]
    s2 = modele["sigma2"]
    y = modele["dernier"]
    if abs(phi) >= 1.0:
        mu = y
        var_h = s2 * h
        mean = y
    else:
        mu = c / (1.0 - phi)
        mean = mu + (phi ** h) * (y - mu)
        var_h = s2 * (1.0 - phi ** (2 * h)) / (1.0 - phi * phi)
    z = _invnorm(1 - (1 - confiance) / 2)
    demi = z * math.sqrt(var_h)
    return (mean, (mean - demi, mean + demi), var_h)


def prevoit(serie, h: int, confiance: float = 0.90, naif: bool = False):
    """Prévision AR(1) à h pas. `naif=True` -> largeur FIXE (variance 1 pas) à tous les horizons (sous-couvre loin).
    Renvoie (ESTIMATION, (mean, (bas, haut)), confiance) ou ABSTENTION."""
    if len(serie) < N_MIN:
        return (ABSTENTION, None, f"série trop courte (n={len(serie)} < {N_MIN})")
    if h < 1:
        return (ABSTENTION, None, "horizon invalide")
    mod = ar1_fit(serie)
    if mod is None:
        return (ABSTENTION, None, "AR(1) non estimable")
    mean, inter, var_h = prevoit_h(mod, h, confiance)
    if naif:
        _, inter1, _ = prevoit_h(mod, 1, confiance)
        demi1 = (inter1[1] - inter1[0]) / 2.0
        inter = (mean - demi1, mean + demi1)
    return (ESTIMATION, (mean, inter), confiance)


def formule(res, h) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas prévoir à {h} pas : {res[2]}."
    mean, (lo, hi) = res[1][0], res[1][1]
    conf = res[2]
    return (f"Prévision à {h} pas ≈ {mean:.2f} (à {round(conf*100)}% entre {lo:.2f} et {hi:.2f}). L'intervalle "
            f"s'élargit avec l'horizon — garder la largeur d'un seul pas serait trop sûr de soi.")


if __name__ == "__main__":
    import random
    print("=== PRÉVISION AUTO-RÉGRESSIVE À h PAS ===\n")
    rng = random.Random(0)
    PHI, C, SIG = 0.7, 1.0, 1.0       # μ = 1/(1−0.7) ≈ 3.33
    serie = [3.0]
    for _ in range(200):
        serie.append(C + PHI * serie[-1] + rng.gauss(0, SIG))
    mod = ar1_fit(serie)
    print(f"  estimé : φ={mod['phi']:.2f} (vrai {PHI}), c={mod['c']:.2f} (vrai {C}), σ={math.sqrt(mod['sigma2']):.2f} (vrai {SIG})")
    for h in (1, 3, 10):
        mean, (lo, hi), var = prevoit_h(mod, h, 0.90)
        print(f"  h={h:2d} : {mean:.2f}  IC=[{lo:.2f}, {hi:.2f}]  largeur={hi-lo:.2f}")
