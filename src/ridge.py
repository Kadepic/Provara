"""
PALIER 2 — RÉGRESSION RIDGE sous COLINÉARITÉ : des coefficients précis-en-apparence mais sauvages (brique 89,
2026-06-27).

Quand deux prédicteurs sont fortement CORRÉLÉS (colinéarité), les moindres carrés ordinaires (OLS) ne peuvent PAS
séparer leurs effets : la solution β̂=(XᵀX)⁻¹Xᵀy a une VARIANCE énorme — un minuscule changement des données fait
BONDIR les coefficients (et parfois INVERSE leur SIGNE), même si leur somme reste stable. Rapporter ces coefficients
comme s'ils étaient bien déterminés est SUR-CONFIANT.

La RÉGRESSION RIDGE ajoute une pénalité λ·‖β‖² :  β̂_ridge = (XᵀX + λI)⁻¹ Xᵀy. Elle accepte un petit BIAIS contre une
forte baisse de VARIANCE → coefficients STABLES et meilleure prédiction. λ=0 ⇒ OLS ; λ→∞ ⇒ β→0 (rétrécissement).

LE MODE D'ÉCHEC DÉMASQUÉ : se fier aux coefficients OLS sous colinéarité est sur-confiant (ils ne sont pas
identifiables) ; ridge stabilise et généralise mieux. Sans colinéarité, OLS va bien (ridge n'apporte rien).
ABSTENTION si système singulier / données insuffisantes. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
RIDGE = "ridge"


def _resol(A, b):
    """Résout A·x=b (élimination de Gauss, pivot partiel)."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-300:
            return None
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def ajuste(X, y, lam=0.0):
    """Coefficients (XᵀX + λI)⁻¹Xᵀy. λ=0 → OLS. X = liste de lignes (features). Renvoie β ou None (singulier)."""
    n, p = len(X), len(X[0])
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
    for a in range(p):
        XtX[a][a] += lam
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(p)]
    return _resol(XtX, Xty)


def predit(x, beta):
    return sum(xi * bi for xi, bi in zip(x, beta))


def mse(X, y, beta):
    return sum((predit(X[i], beta) - y[i]) ** 2 for i in range(len(X))) / len(X)


def analyse(X, y, lam=1.0):
    """Façade : compare OLS et ridge. (RIDGE, {beta_ols, beta_ridge, ...}) ou (ABSTENTION, raison)."""
    if len(X) < len(X[0]) + 1 or len(X) != len(y):
        return (ABSTENTION, "données insuffisantes (n ≤ p) ou tailles différentes")
    bo = ajuste(X, y, 0.0)
    br = ajuste(X, y, lam)
    if bo is None or br is None:
        return (ABSTENTION, "système singulier (XᵀX non inversible)")
    norm = lambda b: sum(v * v for v in b) ** 0.5
    return (RIDGE, {"beta_ols": bo, "beta_ridge": br, "norme_ols": norm(bo), "norme_ridge": norm(br), "lambda": lam})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'ajustement : {res[1]}."
    i = res[1]
    return (f"OLS β={[round(b,2) for b in i['beta_ols']]} (‖β‖={i['norme_ols']:.2f}) vs ridge "
            f"β={[round(b,2) for b in i['beta_ridge']]} (‖β‖={i['norme_ridge']:.2f}). Sous colinéarité, les "
            f"coefficients OLS sont instables (sur-confiants) ; ridge les stabilise.")


if __name__ == "__main__":
    import random, statistics
    rng = random.Random(0)
    def donnees(rng, n, collin, b1=1.0, b2=1.0, bruit=0.5):
        X, y = [], []
        for _ in range(n):
            x1 = rng.gauss(0, 1)
            x2 = x1 + rng.gauss(0, collin)        # collin petit = forte colinéarité
            X.append([x1, x2]); y.append(b1 * x1 + b2 * x2 + rng.gauss(0, bruit))
        return X, y
    print("=== RÉGRESSION RIDGE sous colinéarité ===\n")
    for collin, lab in [(1.0, "indépendants"), (0.05, "très colinéaires")]:
        b1s, b1s_r = [], []
        for _ in range(200):
            X, y = donnees(rng, 50, collin)
            b1s.append(ajuste(X, y, 0.0)[0]); b1s_r.append(ajuste(X, y, 1.0)[0])
        print(f"  {lab:18s}: écart-type de β₁ — OLS={statistics.pstdev(b1s):.2f}  ridge={statistics.pstdev(b1s_r):.2f}")
    X, y = donnees(rng, 50, 0.05)
    print(" ", formule(analyse(X, y, 1.0)))
