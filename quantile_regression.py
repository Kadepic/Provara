"""
PALIER 2 — RÉGRESSION QUANTILE (perte pinball, multi-τ) sous HÉTÉROSCÉDASTICITÉ (brique 43, 2026-06-26).

« Prédire non pas la moyenne mais un QUANTILE conditionnel — la médiane, le 5ᵉ et le 95ᵉ percentile de y sachant x —
quand la DISPERSION de y change avec x (livraison de plus en plus incertaine quand la distance grandit, etc.). » Un
intervalle HOMOSCÉDASTIQUE (OLS ± z·σ, largeur CONSTANTE) ment alors : trop étroit là où ça varie beaucoup
(SUR-CONFIANCE locale), trop large là où c'est calme. Sa couverture CONDITIONNELLE casse.

La régression QUANTILE estime q_τ(x) = a_τ + b_τ·x en minimisant la perte PINBALL  ρ_τ(u) = u·(τ − 1{u<0})
(asymétrique : pénalise τ fois les sous-estimations, 1−τ fois les sur-estimations) → l'optimum est le τ-quantile
conditionnel, sans hypothèse de loi. La bande [q_τlo, q_τhi] a une largeur qui SUIT la dispersion locale. INVARIANT
(jugé par calibration.py) : pour chaque τ, P(y ≤ q_τ(x)) ≈ τ (calibration des niveaux) ET la couverture CONDITIONNELLE
de la bande tient même dans la zone à forte variance, là où l'homoscédastique sous-couvre. ABSTENTION si trop peu de
points. Pur Python (descente de sous-gradient, features standardisées).
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


def pinball(u, tau):
    return u * (tau - (1.0 if u < 0 else 0.0))


def quantile_fit(xs, ys, tau, n_iter: int = 4000, seed_step: float = 0.5):
    """Régression quantile linéaire q_τ(x)=a+b·x par descente de SOUS-GRADIENT (features standardisées, moyenne de
    Polyak). Renvoie (a, b) dans l'échelle d'origine, ou None."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / n)
    if sx <= 0:
        return None
    z = [(x - mx) / sx for x in xs]            # standardisé
    a = sum(ys) / n
    b = 0.0
    abar, bbar = 0.0, 0.0
    cnt = 0
    for t in range(1, n_iter + 1):
        ga = 0.0
        gb = 0.0
        for i in range(n):
            r = ys[i] - (a + b * z[i])
            g = (tau - 1.0) if r < 0 else tau     # sous-gradient de ρ_τ par rapport au résidu, signe inversé
            ga += -(-g)                            # d/da of -g*... -> dérive : dL/da = -g
            gb += -(-g) * z[i]
        ga /= n
        gb /= n
        # dL/da = -mean(g), dL/db = -mean(g*z)  (g comme ci-dessus) -> on descend
        lr = seed_step / math.sqrt(t)
        a -= lr * (-ga)
        b -= lr * (-gb)
        if t > n_iter // 2:                        # moyenne de Polyak sur la 2ᵉ moitié
            abar += a; bbar += b; cnt += 1
    if cnt:
        a, b = abar / cnt, bbar / cnt
    # repasser en échelle d'origine : q = a + b*(x-mx)/sx = (a - b*mx/sx) + (b/sx)*x
    return (a - b * mx / sx, b / sx)


def predit(coef, x):
    return coef[0] + coef[1] * x


def bande_quantile(xs, ys, tau_lo: float = 0.05, tau_hi: float = 0.95):
    """Ajuste q_τlo et q_τhi. Renvoie (ESTIMATION, (coef_lo, coef_hi), 1−(τlo+(1−τhi))) ou ABSTENTION. La bande
    [q_τlo(x), q_τhi(x)] a une LARGEUR qui suit la dispersion locale."""
    n = len(xs)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={n} < {N_MIN})")
    lo = quantile_fit(xs, ys, tau_lo)
    hi = quantile_fit(xs, ys, tau_hi)
    if lo is None or hi is None:
        return (ABSTENTION, None, "quantile non estimable")
    return (ESTIMATION, (lo, hi), tau_hi - tau_lo)


def bande_homoscedastique(xs, ys, confiance: float = 0.90):
    """Référence NAÏVE : OLS ± z·σ, largeur CONSTANTE (homoscédastique). Sous-couvre dans la zone à forte variance.
    Renvoie (a, b, demi_largeur) ou None — la bande est [a+b·x − demi, a+b·x + demi]."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    b = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / sxx
    a = my - b * mx
    rss = sum((ys[i] - (a + b * xs[i])) ** 2 for i in range(n))
    s = math.sqrt(rss / (n - 2))
    z = _invnorm(1 - (1 - confiance) / 2)
    return (a, b, z * s)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer la bande quantile : {res[2]}."
    conf = res[2]
    return (f"Bande de prédiction à {round(conf*100)}% par régression quantile (perte pinball) : sa largeur SUIT la "
            f"dispersion locale — un intervalle homoscédastique sous-couvrirait là où ça varie le plus.")


if __name__ == "__main__":
    import random
    print("=== RÉGRESSION QUANTILE (pinball) sous hétéroscédasticité ===\n")
    rng = random.Random(0)
    xs, ys = [], []
    for _ in range(400):
        x = rng.uniform(0, 5)
        sigma = 0.3 + 0.6 * x                       # dispersion CROÎT avec x
        xs.append(x); ys.append(1.0 + 2.0 * x + rng.gauss(0, sigma))
    med = quantile_fit(xs, ys, 0.5)
    print(f"  médiane conditionnelle : pente={med[1]:.2f} (vraie 2.0), intercept={med[0]:.2f} (vrai 1.0)")
    st, (lo, hi), conf = bande_quantile(xs, ys, 0.05, 0.95)
    for xt in (1.0, 4.0):
        print(f"  x={xt}: bande quantile [{predit(lo, xt):.2f}, {predit(hi, xt):.2f}] (largeur {predit(hi,xt)-predit(lo,xt):.2f})")
    print(" ", formule((st, (lo, hi), conf)))
