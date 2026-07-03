"""
PALIER 2 — ERREURS-EN-VARIABLES : biais d'ATTÉNUATION (brique 49, 2026-06-26).

« On régresse y sur x, mais x lui-même est MESURÉ AVEC ERREUR (capteur bruité, sondage, proxy). » Conséquence
contre-intuitive : la pente des moindres carrés est BIAISÉE VERS ZÉRO (atténuation / « regression dilution »), et son
intervalle de confiance est centré sur cette valeur FAUSSE → on annonce avec assurance une pente trop faible. C'est
distinct des outliers (régression robuste) : ici c'est le bruit sur X qui ment.

Si la variance d'erreur de mesure σ_u² est connue, on corrige par la FIABILITÉ  λ = (Var(x_obs) − σ_u²)/Var(x_obs) :
  b_corrigé = b_naïf / λ        (dé-atténuation par méthode des moments)
INVARIANT (jugé par calibration.py) : l'IC (bootstrap) de la pente CORRIGÉE couvre la vraie pente ~confiance, là où
l'IC OLS naïf sous-couvre (centré sur la pente atténuée). ABSTENTION si trop peu de points / fiabilité ≤ 0. Pur Python.
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 20


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


def _pente_var(xs, ys):
    """(pente OLS, Var(x)) ou None."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = 0.0
    sxy = 0.0
    for i in range(n):
        dx = xs[i] - mx
        sxx += dx * dx
        sxy += dx * (ys[i] - my)
    if sxx <= 0:
        return None
    return (sxy / sxx, sxx / n)


def pente_ols(xs, ys):
    pv = _pente_var(xs, ys)
    return None if pv is None else pv[0]


def fiabilite(xs_obs, sigma_u2):
    """λ = (Var(x_obs) − σ_u²)/Var(x_obs). Renvoie λ ou None."""
    pv = _pente_var(xs_obs, xs_obs)        # Var via sxx/n
    n = len(xs_obs)
    mx = sum(xs_obs) / n
    vx = sum((x - mx) ** 2 for x in xs_obs) / n
    if vx <= 0:
        return None
    return (vx - sigma_u2) / vx


def pente_corrigee(xs_obs, ys, sigma_u2):
    """Pente dé-atténuée = b_naïf / λ. Renvoie la pente ou None."""
    b = pente_ols(xs_obs, ys)
    lam = fiabilite(xs_obs, sigma_u2)
    if b is None or lam is None or lam <= 0.05:
        return None
    return b / lam


def pente_corrigee_ic(xs_obs, ys, sigma_u2, confiance: float = 0.90, n_boot: int = 500, seed: int = 0):
    """Pente corrigée + IC bootstrap. Renvoie (ESTIMATION, (pente, (bas, haut)), confiance) ou ABSTENTION."""
    n = len(xs_obs)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={n} < {N_MIN})")
    point = pente_corrigee(xs_obs, ys, sigma_u2)
    if point is None:
        return (ABSTENTION, None, "fiabilité ≤ 0 (erreur de mesure ≥ variance observée)")
    rng = random.Random(seed)
    pentes = []
    for _ in range(n_boot):
        bx, by = [], []
        for _ in range(n):
            j = rng.randrange(n)
            bx.append(xs_obs[j]); by.append(ys[j])
        b = pente_corrigee(bx, by, sigma_u2)
        if b is not None:
            pentes.append(b)
    if len(pentes) < n_boot // 2:
        return (ABSTENTION, None, "bootstrap instable")
    pentes.sort()
    a = (1.0 - confiance) / 2.0
    lo = pentes[int(a * len(pentes))]
    hi = pentes[min(len(pentes) - 1, int((1 - a) * len(pentes)))]
    return (ESTIMATION, (point, (lo, hi)), confiance)


def pente_ols_ic(xs_obs, ys, confiance: float = 0.90):
    """Pente OLS NAÏVE + IC classique (atténuée, centrée sur la mauvaise valeur). (ESTIMATION,(pente,(bas,haut)),conf)."""
    n = len(xs_obs)
    if n < N_MIN:
        return (ABSTENTION, None, "trop peu de points")
    pv = _pente_var(xs_obs, ys)
    if pv is None:
        return (ABSTENTION, None, "OLS non estimable")
    b = pv[0]
    mx = sum(xs_obs) / n
    sxx = sum((x - mx) ** 2 for x in xs_obs)
    my = sum(ys) / n
    a0 = my - b * mx
    rss = sum((ys[i] - (a0 + b * xs_obs[i])) ** 2 for i in range(n))
    s2 = rss / (n - 2)
    se = math.sqrt(s2 / sxx)
    z = _invnorm(1 - (1 - confiance) / 2)
    return (ESTIMATION, (b, (b - z * se, b + z * se)), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas corriger la pente : {res[2]}."
    b, (lo, hi), conf = res[1][0], res[1][1], res[2]
    return (f"Pente corrigée de l'erreur de mesure ≈ {b:.3f} (à {round(conf*100)}% entre {lo:.3f} et {hi:.3f}). "
            f"Les moindres carrés bruts, eux, l'atténueraient vers zéro et se tromperaient avec assurance.")


if __name__ == "__main__":
    print("=== ERREURS-EN-VARIABLES (biais d'atténuation) ===\n")
    rng = random.Random(0)
    A, B, SU = 1.0, 2.0, 1.0          # y = 1 + 2x ; erreur de mesure sur x d'écart-type 1
    xs_obs, ys = [], []
    for _ in range(200):
        xt = rng.uniform(0, 5)
        ys.append(A + B * xt + rng.gauss(0, 0.5))
        xs_obs.append(xt + rng.gauss(0, SU))
    print(f"  pente OLS naïve     = {pente_ols(xs_obs, ys):.3f}  (atténuée vers 0)")
    print(f"  fiabilité λ         = {fiabilite(xs_obs, SU*SU):.2f}")
    print(f"  pente corrigée      = {pente_corrigee(xs_obs, ys, SU*SU):.3f}  (vraie = {B})")
    print(" ", formule(pente_corrigee_ic(xs_obs, ys, SU * SU, 0.90)))
