"""
PALIER 2 — PRÉVISION MULTIVARIÉE PAR VAR(1) + RÉGION CONJOINTE (brique, 2026-06-26).

« Prévoir PLUSIEURS séries couplées à la fois (ventes & trafic & stock) à l'horizon h. » Deux pièges de sur-confiance :
(1) l'incertitude CROÎT avec l'horizon (un VAR propage le bruit : Σ_h = A Σ_{h-1} Aᵀ + Σ) — l'ignorer sous-estime le
risque lointain ; (2) construire une BOÎTE d'intervalles INDÉPENDANTS par composante (chacun au niveau 1−α) ignore la
CORRÉLATION des innovations : l'événement CONJOINT « tout tombe dans la boîte » couvre alors (1−α)^d ≪ 1−α (multiplicité)
— SUR-CONFIANCE conjointe.

Le remède : un VAR(1) X_t = c + A·X_{t-1} + e_t (e_t corrélé, cov Σ) donne une moyenne ET une covariance de prévision
Σ_h ; la RÉGION CONJOINTE est l'ellipsoïde de Mahalanobis { y : (y−μ)ᵀ Σ_h⁻¹ (y−μ) ≤ seuil }, dont le seuil est calibré
de façon CONFORME (quantile empirique des scores D² sur un jeu de calibration — sans hypothèse gaussienne). INVARIANT
(jugé par calibration.py) : la couverture CONJOINTE de l'ellipsoïde ≈ nominal ; celle de la boîte indépendante S'EFFONDRE
(sur-confiante). ABSTENTION si série trop courte. Pur Python (OLS multivarié, inverse par Gauss-Jordan).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 30


def _zeros(r, c):
    return [[0.0] * c for _ in range(r)]


def _matmul(A, B):
    n, m, p = len(A), len(B), len(B[0])
    out = _zeros(n, p)
    for i in range(n):
        Ai = A[i]
        for k in range(m):
            a = Ai[k]
            if a == 0.0:
                continue
            Bk = B[k]
            oi = out[i]
            for j in range(p):
                oi[j] += a * Bk[j]
    return out


def _transpose(A):
    return [list(col) for col in zip(*A)]


def _matvec(A, v):
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def _inv(M):
    """Inverse par Gauss-Jordan avec pivot partiel. Renvoie None si singulière."""
    n = len(M)
    A = [list(row) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-12:
            return None
        A[col], A[piv] = A[piv], A[col]
        d = A[col][col]
        A[col] = [x / d for x in A[col]]
        for r in range(n):
            if r != col and A[r][col] != 0.0:
                f = A[r][col]
                A[r] = [a - f * b for a, b in zip(A[r], A[col])]
    return [row[n:] for row in A]


def var_fit(serie):
    """Ajuste un VAR(1) : X_t = c + A·X_{t-1} + e_t, par OLS équation par équation. `serie` = liste de vecteurs (≥ N_MIN).
    Renvoie {c, A, Sigma} (Sigma = covariance des résidus) ou None."""
    T = len(serie)
    if T < N_MIN:
        return None
    d = len(serie[0])
    # régresseurs Z_t = [1, X_{t-1}] -> cible X_t, pour t=1..T-1
    Z = [[1.0] + list(serie[t - 1]) for t in range(1, T)]
    Y = [list(serie[t]) for t in range(1, T)]
    ZT = _transpose(Z)
    ZTZ = _matmul(ZT, Z)
    inv = _inv(ZTZ)
    if inv is None:
        return None
    ZTY = _matmul(ZT, Y)
    B = _matmul(inv, ZTY)              # (d+1) x d : ligne 0 = intercept, lignes 1.. = A^T
    c = [B[0][j] for j in range(d)]
    A = [[B[1 + k][j] for k in range(d)] for j in range(d)]   # A[j][k]
    # résidus -> Sigma
    resid = []
    for t in range(1, T):
        pred = [c[j] + sum(A[j][k] * serie[t - 1][k] for k in range(d)) for j in range(d)]
        resid.append([serie[t][j] - pred[j] for j in range(d)])
    m = len(resid)
    Sigma = _zeros(d, d)
    for r in resid:
        for i in range(d):
            for j in range(d):
                Sigma[i][j] += r[i] * r[j] / m
    return {"c": c, "A": A, "Sigma": Sigma, "d": d}


def prevision(model, x_last, h: int = 1):
    """Prévision à h pas : moyenne μ_h et covariance Σ_h (qui CROÎT avec h). Renvoie (mu, Sigma_h)."""
    c, A, Sig, d = model["c"], model["A"], model["Sigma"], model["d"]
    mu = list(x_last)
    cov = _zeros(d, d)
    for _ in range(h):
        mu = [c[j] + sum(A[j][k] * mu[k] for k in range(d)) for j in range(d)]
        # Σ_h = A Σ_{h-1} Aᵀ + Σ
        cov = [[sum(A[i][a] * cov[a][b] * A[j][b] for a in range(d) for b in range(d)) + Sig[i][j]
                for j in range(d)] for i in range(d)]
    return mu, cov


def mahalanobis2(y, mu, cov_inv):
    dv = [y[i] - mu[i] for i in range(len(y))]
    return sum(dv[i] * cov_inv[i][j] * dv[j] for i in range(len(y)) for j in range(len(y)))


def seuil_conforme(scores_d2, confiance: float = 0.90):
    """Seuil = quantile conforme (⌈(n+1)·conf⌉/n)-ème des scores D² de calibration. Distribution-free."""
    s = sorted(scores_d2)
    n = len(s)
    rang = min(n - 1, math.ceil((n + 1) * confiance) - 1)
    return s[rang]


def demi_largeurs_boite(cov, confiance: float = 0.90):
    """Demi-largeurs marginales par composante au niveau `confiance` (gaussien) — IGNORE la corrélation."""
    z = _invnorm(1 - (1 - confiance) / 2)
    return [z * math.sqrt(max(cov[i][i], 0.0)) for i in range(len(cov))]


def _invnorm(p: float) -> float:
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
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def ajuste(serie):
    if len(serie) < N_MIN:
        return (ABSTENTION, None, f"série trop courte (T={len(serie)} < {N_MIN})")
    m = var_fit(serie)
    if m is None:
        return (ABSTENTION, None, "VAR non estimable (régresseurs singuliers)")
    return (ESTIMATION, m, None)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas prévoir la série multivariée : {res[2]}."
    return ("Prévision VAR multivariée avec RÉGION CONJOINTE (ellipsoïde de Mahalanobis, seuil conforme) : elle tient "
            "compte de la corrélation entre composantes et de la croissance de l'incertitude avec l'horizon — une boîte "
            "d'intervalles indépendants serait sur-confiante sur l'événement conjoint.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    A = [[0.5, 0.2], [-0.1, 0.4]]
    c = [0.3, -0.2]
    serie, x = [], [0.0, 0.0]
    for _ in range(300):
        e0 = rng.gauss(0, 1.0); e1 = 0.8 * e0 + rng.gauss(0, 0.6)   # innovations CORRÉLÉES
        x = [c[0] + A[0][0]*x[0] + A[0][1]*x[1] + e0, c[1] + A[1][0]*x[0] + A[1][1]*x[1] + e1]
        serie.append(x)
    st, m, _ = ajuste(serie)
    print("=== PRÉVISION VAR(1) MULTIVARIÉE + région conjointe ===\n")
    print(f"  A estimé = {[[round(v,2) for v in row] for row in m['A']]} (vrai {A})")
    for h in (1, 3, 6):
        _, cov = prevision(m, serie[-1], h)
        print(f"  horizon h={h} : trace(Σ_h)={cov[0][0]+cov[1][1]:.2f} (croît avec h)")
    print(" ", formule((st, m, None)))
