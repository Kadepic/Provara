"""
PALIER 2 — RÉGRESSION PAR PROCESSUS GAUSSIEN (GP, brique 45, 2026-06-26).

« Prédire une fonction lisse f(x) ET dire HONNÊTEMENT combien on est incertain — surtout LOIN des données observées
(extrapolation, trous d'échantillonnage). » Un modèle qui annonce une incertitude CONSTANTE ment : il est trop sûr de
lui là où il n'a aucune donnée (SUR-CONFIANCE épistémique). Le processus gaussien donne une incertitude qui GRANDIT
naturellement quand on s'éloigne des points observés.

Noyau exponentiel-quadratique  k(a,b) = σ_f²·exp(−(a−b)²/2ℓ²). Prédictif en x* :
  moyenne = k*ᵀ (K+σ_n²I)⁻¹ y          variance = σ_f² − k*ᵀ(K+σ_n²I)⁻¹k* + σ_n²
La variance combine bruit d'observation (σ_n², ALÉATOIRE) et incertitude du modèle (ÉPISTÉMIQUE, grande hors-données).
INVARIANT (jugé par calibration.py) : l'intervalle GP couvre ~confiance PARTOUT, y compris dans un TROU
d'échantillonnage, là où une bande de largeur CONSTANTE sous-couvre. ABSTENTION si trop peu de points / matrice
singulière. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 8


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


def _chol(A):
    """Cholesky L (A = L Lᵀ) d'une matrice symétrique définie positive. None si non-DP."""
    n = len(A)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = A[i][j]
            for k in range(j):
                s -= L[i][k] * L[j][k]
            if i == j:
                if s <= 1e-12:
                    return None
                L[i][j] = math.sqrt(s)
            else:
                L[i][j] = s / L[j][j]
    return L


def _solve_chol(L, b):
    """Résout (L Lᵀ) x = b."""
    n = len(L)
    y = [0.0] * n
    for i in range(n):
        s = b[i]
        for k in range(i):
            s -= L[i][k] * y[k]
        y[i] = s / L[i][i]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = y[i]
        for k in range(i + 1, n):
            s -= L[k][i] * x[k]
        x[i] = s / L[i][i]
    return x


def _k(a, b, sf2, ell):
    d = a - b
    return sf2 * math.exp(-(d * d) / (2.0 * ell * ell))


def gp_fit(xs, ys, ell: float = 1.0, sigma_f: float = 1.0, sigma_n: float = 0.3):
    """Ajuste un GP (noyau SE, hyperparamètres fixés). Renvoie un modèle {xs, L, alpha, sf2, ell, sn2} ou None."""
    n = len(xs)
    if n < 3:
        return None
    sf2 = sigma_f * sigma_f
    sn2 = sigma_n * sigma_n
    K = [[_k(xs[i], xs[j], sf2, ell) + (sn2 if i == j else 0.0) for j in range(n)] for i in range(n)]
    L = _chol(K)
    if L is None:
        return None
    alpha = _solve_chol(L, list(ys))
    return {"xs": list(xs), "L": L, "alpha": alpha, "sf2": sf2, "ell": ell, "sn2": sn2}


def gp_predict(model, xstar):
    """Renvoie (moyenne, variance) prédictives en xstar (variance = épistémique + bruit d'observation)."""
    xs = model["xs"]
    ks = [_k(xstar, x, model["sf2"], model["ell"]) for x in xs]
    mean = 0.0
    for i in range(len(xs)):
        mean += ks[i] * model["alpha"][i]
    v = _solve_chol(model["L"], ks)
    quad = 0.0
    for i in range(len(xs)):
        quad += ks[i] * v[i]
    var = model["sf2"] - quad + model["sn2"]
    if var < model["sn2"] * 1e-6:
        var = model["sn2"] * 1e-6
    return (mean, var)


def gp_intervalle(model, xstar, confiance: float = 0.90):
    mean, var = gp_predict(model, xstar)
    z = _invnorm(1 - (1 - confiance) / 2)
    demi = z * math.sqrt(var)
    return (mean, (mean - demi, mean + demi))


def ajuste(xs, ys, *, ell: float = 1.0, sigma_f: float = 1.0, sigma_n: float = 0.3):
    """Façade ABSTENTION-aware. Renvoie (ESTIMATION, model, None) ou (ABSTENTION, None, raison)."""
    if len(xs) < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={len(xs)} < {N_MIN})")
    m = gp_fit(xs, ys, ell, sigma_f, sigma_n)
    if m is None:
        return (ABSTENTION, None, "matrice de covariance non définie positive")
    return (ESTIMATION, m, None)


def formule(model, xstar, confiance: float = 0.90) -> str:
    mean, (lo, hi) = gp_intervalle(model, xstar, confiance)
    return (f"f({xstar}) ≈ {mean:.2f} (à {round(confiance*100)}% entre {lo:.2f} et {hi:.2f}). L'incertitude grandit "
            f"loin des données observées — une bande de largeur constante mentirait dans les zones creuses.")


if __name__ == "__main__":
    import random
    print("=== RÉGRESSION PAR PROCESSUS GAUSSIEN ===\n")
    rng = random.Random(0)

    def f(x):
        return math.sin(1.5 * x)

    xs, ys = [], []
    for _ in range(40):
        x = rng.uniform(0, 5)
        if 2.0 < x < 3.5:                  # TROU d'échantillonnage
            continue
        xs.append(x); ys.append(f(x) + rng.gauss(0, 0.2))
    st, model, _ = ajuste(xs, ys, ell=0.7, sigma_f=1.0, sigma_n=0.2)
    for xt in (1.0, 2.75, 4.5):
        mean, var = gp_predict(model, xt)
        zone = "TROU" if 2.0 < xt < 3.5 else "dense"
        print(f"  x={xt} ({zone:5s}) : vrai={f(xt):+.2f}  GP={mean:+.2f}  écart-type={math.sqrt(var):.2f}")
    print(" ", formule(model, 2.75))
