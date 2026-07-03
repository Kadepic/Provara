"""
PALIER 2 — COVARIANCE EN GRANDE DIMENSION (Marchenko-Pastur, rétrécissement de Ledoit-Wolf) : la matrice de covariance
empirique est SUR-CONFIANTE quand p/n n'est pas petit (brique 77, 2026-06-27).

Avec p variables et n observations, la covariance EMPIRIQUE S est un estimateur naïf de la vraie covariance Σ. Quand
p/n n'est pas petit (peu d'observations par variable), S est très bruitée : même si toutes les variables sont
INDÉPENDANTES (Σ=I, toutes les valeurs propres = 1), les valeurs propres de S s'ÉTALENT sur tout l'intervalle de
MARCHENKO-PASTUR :
    [ (1−√c)², (1+√c)² ]·σ²        avec c = p/n.
La plus grande valeur propre SUR-ESTIME la direction de risque dominante, la plus petite SOUS-ESTIME (matrice
quasi-singulière) → le conditionnement explose. Utiliser S telle quelle (inversion, portefeuille, Mahalanobis) =
SUR-CONFIANCE : on « voit » des corrélations et des facteurs qui sont du pur bruit.

LA CORRECTION — RÉTRÉCISSEMENT (Ledoit-Wolf) : Ŝ = (1−α)·S + α·μ·I (μ = valeur propre moyenne) tire les valeurs
propres vers la cible → resserre le spectre, réduit le conditionnement et l'erreur d'estimation.

LE MODE D'ÉCHEC DÉMASQUÉ : prendre S au pied de la lettre en grande dimension sur-estime corrélations/facteurs ; le
rétrécissement le corrige (plus proche de la vérité). ABSTENTION si n<2 / dimensions incohérentes. Pur Python
(valeurs propres par rotations de Jacobi).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def valeurs_propres(A, iters=200, tol=1e-12):
    """Valeurs propres d'une matrice SYMÉTRIQUE par la méthode de Jacobi (pivot du plus grand hors-diagonale)."""
    n = len(A)
    M = [row[:] for row in A]
    for _ in range(iters * n * n):
        p, q, mx = 0, 1, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(M[i][j]) > mx:
                    mx = abs(M[i][j]); p, q = i, j
        if mx < tol:
            break
        app, aqq, apq = M[p][p], M[q][q], M[p][q]
        if abs(app - aqq) < 1e-300:
            phi = math.pi / 4
        else:
            phi = 0.5 * math.atan2(2 * apq, app - aqq)
        c, s = math.cos(phi), math.sin(phi)
        for k in range(n):
            mkp, mkq = M[k][p], M[k][q]
            M[k][p] = c * mkp + s * mkq
            M[k][q] = -s * mkp + c * mkq
        for k in range(n):
            mpk, mqk = M[p][k], M[q][k]
            M[p][k] = c * mpk + s * mqk
            M[q][k] = -s * mpk + c * mqk
    return sorted(M[i][i] for i in range(n))


def covariance_echantillon(X):
    """Covariance empirique (centrée) d'une liste de n vecteurs de dimension p : S = (1/n)Σ (x−x̄)(x−x̄)ᵀ."""
    n = len(X); p = len(X[0])
    moy = [sum(X[i][j] for i in range(n)) / n for j in range(p)]
    S = [[0.0] * p for _ in range(p)]
    for x in X:
        d = [x[j] - moy[j] for j in range(p)]
        for i in range(p):
            for j in range(p):
                S[i][j] += d[i] * d[j] / n
    return S


def bornes_marchenko_pastur(p, n, sigma2=1.0):
    """Support de Marchenko-Pastur des valeurs propres : [(1−√c)², (1+√c)²]·σ², c=p/n."""
    c = p / n
    return ((1 - math.sqrt(c)) ** 2 * sigma2, (1 + math.sqrt(c)) ** 2 * sigma2)


def retrecissement(S, alpha):
    """Rétrécissement Ŝ=(1−α)S+α·μ·I (μ=trace/p), α∈[0,1]. Resserre le spectre vers la cible isotrope."""
    p = len(S)
    mu = sum(S[i][i] for i in range(p)) / p
    return [[(1 - alpha) * S[i][j] + (alpha * mu if i == j else 0.0) for j in range(p)] for i in range(p)]


def conditionnement(eigs):
    """Nombre de conditionnement = λ_max/λ_min (explose en grande dimension)."""
    mn = min(eigs)
    return max(eigs) / mn if mn > 1e-12 else float("inf")


def frobenius(A, B):
    """Distance de Frobenius ‖A−B‖_F."""
    return math.sqrt(sum((A[i][j] - B[i][j]) ** 2 for i in range(len(A)) for j in range(len(A))))


def max_correlation_hors_diag(S):
    """Plus grande corrélation empirique (en valeur absolue) hors diagonale."""
    p = len(S)
    mx = 0.0
    for i in range(p):
        for j in range(i + 1, p):
            d = math.sqrt(S[i][i] * S[j][j])
            if d > 0:
                mx = max(mx, abs(S[i][j]) / d)
    return mx


def analyse(X, alpha=0.5):
    """Façade : (ANALYSE, {p, n, eigs, cond, eigs_retr, cond_retr, mp}) ou (ABSTENTION, raison)."""
    if len(X) < 2 or not X[0] or any(len(x) != len(X[0]) for x in X):
        return (ANALYSE if False else ABSTENTION, "n<2 ou dimensions incohérentes")
    n, p = len(X), len(X[0])
    S = covariance_echantillon(X)
    Sr = retrecissement(S, alpha)
    eigs = valeurs_propres(S)
    return (ANALYSE, {"p": p, "n": n, "eigs": eigs, "cond": conditionnement(eigs),
                      "eigs_retr": valeurs_propres(Sr), "cond_retr": conditionnement(valeurs_propres(Sr)),
                      "mp": bornes_marchenko_pastur(p, n)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Analyse impossible : {res[1]}."
    i = res[1]
    return (f"p={i['p']}, n={i['n']} : valeurs propres empiriques ∈ [{i['eigs'][0]:.2f}, {i['eigs'][-1]:.2f}] "
            f"(vraies = 1) ; conditionnement {i['cond']:.1f}. Le rétrécissement le ramène à {i['cond_retr']:.1f}. "
            f"Prendre la covariance empirique telle quelle serait sur-confiant en grande dimension.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== COVARIANCE EN GRANDE DIMENSION (Marchenko-Pastur) ===\n")
    print("  Vérif Jacobi : valeurs propres de [[2,1],[1,2]] =", [round(v, 3) for v in valeurs_propres([[2, 1], [1, 2]])], "(attendu 1,3)")
    for p, n in [(20, 200), (20, 40), (20, 25)]:
        X = [[rng.gauss(0, 1) for _ in range(p)] for _ in range(n)]   # vraie Σ = I
        info = analyse(X, 0.5)[1]
        print(f"  p={p}, n={n} (c={p/n}): val.propres ∈ [{info['eigs'][0]:.2f}, {info['eigs'][-1]:.2f}] "
              f"MP=[{info['mp'][0]:.2f}, {info['mp'][1]:.2f}] cond={info['cond']:.1f} → retréci cond={info['cond_retr']:.1f}")
    print(" ", formule(analyse([[rng.gauss(0, 1) for _ in range(15)] for _ in range(30)], 0.5)))
