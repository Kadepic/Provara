"""
PALIER 2 — MOYENNAGE BAYÉSIEN DE MODÈLES (BMA) : incertitude de SÉLECTION de modèle (brique, 2026-06-26).

« Plusieurs modèles plausibles (régression linéaire, quadratique, cubique…) expliquent les données ; on en CHOISIT un (le
meilleur BIC/AIC) et on prédit comme si c'était LE vrai. » C'est une SUR-CONFIANCE cachée : l'incertitude sur le CHOIX du
modèle est ignorée. Faire de la sélection puis poser un intervalle « modèle fixé » donne des bandes trop étroites
(inférence post-sélection) ; pire à l'EXTRAPOLATION, où les modèles divergent franchement.

Le BMA pondère chaque modèle par sa probabilité a posteriori (poids ∝ exp(−½·BIC)) et la variance prédictive ajoute la
variance ENTRE modèles : Var = Σ wₘ(σ²ₘ + μ²ₘ) − (Σ wₘμₘ)² (variance intra + inter). INVARIANT (jugé par calibration.py) :
la couverture de l'intervalle BMA ≈ nominal, celle du « meilleur modèle unique » (re-sélectionné à chaque jeu)
S'EFFONDRE (sur-confiante). Quand un modèle domine nettement, BMA ≈ ce modèle (aucun prix superflu). ABSTENTION si trop
peu de points. Pur Python (OLS par équations normales, inverse Gauss-Jordan).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 12


def _invnorm(p):
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
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


def _inv(M):
    n = len(M)
    A = [list(row) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-12:
            return None
        A[col], A[piv] = A[piv], A[col]
        dv = A[col][col]
        A[col] = [x / dv for x in A[col]]
        for r in range(n):
            if r != col and A[r][col] != 0.0:
                f = A[r][col]
                A[r] = [x - f * y for x, y in zip(A[r], A[col])]
    return [row[n:] for row in A]


def _design(xs, degre):
    return [[x ** p for p in range(degre + 1)] for x in xs]


def ajuste_polynome(xs, ys, degre):
    """OLS polynomial. Renvoie {beta, XtX_inv, sigma2, k, rss, n} ou None."""
    X = _design(xs, degre)
    n, k = len(X), degre + 1
    if n <= k:
        return None
    XtX = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    inv = _inv(XtX)
    if inv is None:
        return None
    Xty = [sum(X[r][i] * ys[r] for r in range(n)) for i in range(k)]
    beta = [sum(inv[i][j] * Xty[j] for j in range(k)) for i in range(k)]
    rss = sum((ys[r] - sum(beta[i] * X[r][i] for i in range(k))) ** 2 for r in range(n))
    sigma2 = rss / (n - k)
    return {"beta": beta, "XtX_inv": inv, "sigma2": sigma2, "k": k, "rss": max(rss, 1e-12), "n": n, "degre": degre}


def bic(modele):
    n, k = modele["n"], modele["k"]
    return n * math.log(modele["rss"] / n) + k * math.log(n)


def _phi_x(x, degre):
    return [x ** p for p in range(degre + 1)]


def predit_modele(modele, x0):
    """Moyenne prédictive et variance prédictive (paramètres + bruit) d'un modèle à x0."""
    k = modele["k"]
    phi = _phi_x(x0, modele["degre"])
    mu = sum(modele["beta"][i] * phi[i] for i in range(k))
    quad = sum(phi[i] * modele["XtX_inv"][i][j] * phi[j] for i in range(k) for j in range(k))
    var = modele["sigma2"] * (1.0 + quad)
    return mu, var


def poids_bic(modeles):
    """Poids a posteriori ∝ exp(−½·BIC) (normalisés)."""
    bics = [bic(m) for m in modeles]
    bmin = min(bics)
    w = [math.exp(-0.5 * (b - bmin)) for b in bics]
    s = sum(w)
    return [x / s for x in w]


def ajuste(xs, ys, degres=(1, 2, 3)):
    """Ajuste tous les modèles candidats. Renvoie (ESTIMATION, {modeles, poids}, None) ou (ABSTENTION, None, raison)."""
    if len(xs) < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={len(xs)} < {N_MIN})")
    modeles = [ajuste_polynome(xs, ys, d) for d in degres]
    modeles = [m for m in modeles if m is not None]
    if not modeles:
        return (ABSTENTION, None, "aucun modèle estimable")
    return (ESTIMATION, {"modeles": modeles, "poids": poids_bic(modeles)}, None)


def intervalle_bma(etat, x0, confiance=0.90):
    """Intervalle BMA à x0 : moyenne pondérée + variance intra+inter modèles. Renvoie (mu, (lo, hi))."""
    modeles, w = etat["modeles"], etat["poids"]
    preds = [predit_modele(m, x0) for m in modeles]
    mu = sum(w[i] * preds[i][0] for i in range(len(w)))
    var = sum(w[i] * (preds[i][1] + preds[i][0] ** 2) for i in range(len(w))) - mu ** 2
    z = _invnorm(1 - (1 - confiance) / 2)
    demi = z * math.sqrt(max(var, 0.0))
    return mu, (mu - demi, mu + demi)


def intervalle_meilleur(etat, x0, confiance=0.90):
    """Intervalle du MEILLEUR modèle unique (poids max) : ignore l'incertitude de sélection. Renvoie (mu, (lo, hi))."""
    modeles, w = etat["modeles"], etat["poids"]
    best = max(range(len(w)), key=lambda i: w[i])
    mu, var = predit_modele(modeles[best], x0)
    z = _invnorm(1 - (1 - confiance) / 2)
    demi = z * math.sqrt(max(var, 0.0))
    return mu, (mu - demi, mu + demi)


def formule(res, x0=None) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas moyenner les modèles : {res[2]}."
    w = res[1]["poids"]
    return (f"Prédiction par moyennage bayésien de modèles (poids {[round(x,2) for x in w]}) : la bande inclut la "
            f"variance ENTRE modèles — choisir le seul « meilleur » modèle serait sur-confiant (incertitude de "
            f"sélection ignorée), surtout à l'extrapolation.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    xs = [rng.uniform(0, 2) for _ in range(30)]
    ys = [2 + 1.5 * x + rng.gauss(0, 1.0) for x in xs]      # VRAI = linéaire
    st, etat, _ = ajuste(xs, ys, (1, 2, 3))
    print("=== MOYENNAGE BAYÉSIEN DE MODÈLES (BMA) vs meilleur modèle unique ===\n")
    print(f"  poids BIC (deg 1,2,3) = {[round(w,3) for w in etat['poids']]}")
    for x0 in (1.0, 2.8):
        mb, ib = intervalle_bma(etat, x0); mu, iu = intervalle_meilleur(etat, x0)
        print(f"  x0={x0}: BMA largeur={ib[1]-ib[0]:.2f}  meilleur largeur={iu[1]-iu[0]:.2f} "
              f"({'extrapolation' if x0 > 2 else 'interpolation'})")
    print(" ", formule((st, etat, None)))
