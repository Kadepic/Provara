"""
PALIER 2 — RÉGRESSION ROBUSTE (M-estimateur de Huber) sous CONTAMINATION (brique 41, 2026-06-26).

« Estimer une pente quand une fraction des points sont des OUTLIERS (erreurs de saisie, capteurs en panne, fraude) ? »
Les MOINDRES CARRÉS (OLS) minimisent le carré des résidus → un seul gros outlier à fort levier TORD la pente, et son
intervalle de confiance classique (variance résiduelle gonflée OU biais ignoré) devient FAUX : il rate la vraie pente
plus souvent que son niveau annoncé → SUR-CONFIANCE.

Le M-estimateur de HUBER borne l'influence des grands résidus : quadratique au centre, LINÉAIRE dans les queues
(seuil c·s, s = échelle robuste MAD). On l'ajuste par moindres carrés repondérés (IRLS) ; l'incertitude par BOOTSTRAP
de lignes (distribution-free, pas de formule sandwich fragile). INVARIANT (jugé par calibration.py) : sous bruit
contaminé connu, l'IC bootstrap de la pente de Huber COUVRE la vraie pente ~confiance, là où l'IC d'OLS sous-couvre.
Sans contamination, Huber ≈ OLS (pas de prix payé). ABSTENTION si trop peu de points / non-convergence. Pur Python.
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 12
C_HUBER = 1.345        # 95 % d'efficacité sous gaussienne


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


def _mediane(vals):
    s = sorted(vals)
    k = len(s)
    if k == 0:
        return 0.0
    return s[k // 2] if k % 2 else 0.5 * (s[k // 2 - 1] + s[k // 2])


def _wls(xs, ys, w):
    """Moindres carrés pondérés y ~ a + b·x. Renvoie (a, b) ou None."""
    sw = 0.0
    swx = 0.0
    swy = 0.0
    for i in range(len(xs)):
        sw += w[i]; swx += w[i] * xs[i]; swy += w[i] * ys[i]
    if sw <= 0:
        return None
    mx = swx / sw
    my = swy / sw
    sxx = 0.0
    sxy = 0.0
    for i in range(len(xs)):
        dx = xs[i] - mx
        sxx += w[i] * dx * dx
        sxy += w[i] * dx * (ys[i] - my)
    if sxx <= 0:
        return None
    b = sxy / sxx
    return (my - b * mx, b)


def ols(xs, ys):
    """Moindres carrés ordinaires y ~ a + b·x. Renvoie (a, b) ou None."""
    n = len(xs)
    w = [1.0] * n
    return _wls(xs, ys, w)


def huber_fit(xs, ys, c: float = C_HUBER, n_iter: int = 50, tol: float = 1e-8):
    """M-estimateur de Huber par IRLS. Renvoie (a, b) ou None."""
    n = len(xs)
    if n < 3:
        return None
    fit = ols(xs, ys)
    if fit is None:
        return None
    a, b = fit
    for _ in range(n_iter):
        resid = []
        for i in range(n):
            resid.append(ys[i] - (a + b * xs[i]))
        absr = []
        for r in resid:
            absr.append(abs(r))
        s = _mediane(absr) / 0.6745
        if s <= 1e-12:
            break
        w = []
        for r in resid:
            t = abs(r) / s
            w.append(1.0 if t <= c else c / t)
        nf = _wls(xs, ys, w)
        if nf is None:
            return None
        if abs(nf[0] - a) + abs(nf[1] - b) < tol:
            a, b = nf
            break
        a, b = nf
    return (a, b)


def huber_slope_ic(xs, ys, confiance: float = 0.95, n_boot: int = 400, seed: int = 0):
    """Pente de Huber + IC par bootstrap de lignes. Renvoie (ESTIMATION, (b, (bas, haut)), confiance) ou ABSTENTION."""
    n = len(xs)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={n} < {N_MIN})")
    fit = huber_fit(xs, ys)
    if fit is None:
        return (ABSTENTION, None, "Huber non ajustable (échelle nulle / colinéarité)")
    rng = random.Random(seed)
    pentes = []
    for _ in range(n_boot):
        bx = []
        by = []
        for _ in range(n):
            j = rng.randrange(n)
            bx.append(xs[j]); by.append(ys[j])
        f = huber_fit(bx, by)
        if f is not None:
            pentes.append(f[1])
    if len(pentes) < n_boot // 2:
        return (ABSTENTION, None, "bootstrap instable")
    pentes.sort()
    alpha = (1.0 - confiance) / 2.0
    lo = pentes[int(alpha * len(pentes))]
    hi = pentes[min(len(pentes) - 1, int((1.0 - alpha) * len(pentes)))]
    return (ESTIMATION, (fit[1], (lo, hi)), confiance)


def ols_slope_ic(xs, ys, confiance: float = 0.95):
    """Pente OLS + IC classique (t/normal, variance résiduelle). NAÏF : faux sous contamination. Renvoie
    (ESTIMATION, (b, (bas, haut)), confiance) ou ABSTENTION."""
    n = len(xs)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={n} < {N_MIN})")
    fit = ols(xs, ys)
    if fit is None:
        return (ABSTENTION, None, "OLS non estimable")
    a, b = fit
    mx = 0.0
    for v in xs:
        mx += v
    mx /= n
    sxx = 0.0
    rss = 0.0
    for i in range(n):
        dx = xs[i] - mx
        sxx += dx * dx
        r = ys[i] - (a + b * xs[i])
        rss += r * r
    if sxx <= 0 or n <= 2:
        return (ABSTENTION, None, "variance non estimable")
    s2 = rss / (n - 2)
    se = math.sqrt(s2 / sxx)
    z = _invnorm(1 - (1 - confiance) / 2)
    return (ESTIMATION, (b, (b - z * se, b + z * se)), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer la pente robuste : {res[2]}."
    b, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Pente robuste ≈ {b:.3f} (à {round(conf*100)}% entre {bas:.3f} et {haut:.3f}). Les outliers sont "
            f"bornés en influence — les moindres carrés ordinaires, eux, seraient tordus par eux.")


if __name__ == "__main__":
    print("=== RÉGRESSION ROBUSTE (Huber) sous contamination ===\n")
    rng = random.Random(0)
    A, B = 1.0, 2.0       # vraie droite y = 1 + 2x
    xs, ys = [], []
    for _ in range(80):
        xv = rng.uniform(0, 5)
        xs.append(xv)
        if rng.random() < 0.15:                 # 15 % d'outliers à fort levier
            ys.append(A + B * xv + rng.gauss(0, 0.4) - 8.0)
        else:
            ys.append(A + B * xv + rng.gauss(0, 0.4))
    print(f"  OLS   pente = {ols(xs, ys)[1]:.3f}  (tordue par les outliers)")
    print(f"  Huber pente = {huber_fit(xs, ys)[1]:.3f}  (vraie = {B})")
    print("  ", formule(huber_slope_ic(xs, ys, 0.90)))
    print("  ", formule(ols_slope_ic(xs, ys, 0.90)).replace("robuste", "OLS"))
