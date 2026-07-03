"""
PALIER 2 — LONGUEUR DE DESCRIPTION MINIMALE (MDL, Rissanen) : choisir un modèle par COMPRESSION, pas par erreur
d'entraînement (brique 76, 2026-06-27).

Minimiser l'erreur d'AJUSTEMENT mène toujours au modèle le plus COMPLEXE (un polynôme de degré n−1 passe par tous les
points : erreur 0) — c'est SUR-CONFIANT : ce modèle a tout mémorisé et prédira mal. Le principe MDL formalise le
rasoir d'Occam : le meilleur modèle est celui qui COMPRESSE le mieux les données = minimise la longueur de description
en deux parties,
    L(modèle) + L(données | modèle).
En régression, l'approximation (Schwarz/MDL à deux parties) donne, pour un modèle à k paramètres sur n points :
    L(d) ≈ (n/2)·ln(RSS_d / n)   [coder les résidus]   +   (k/2)·ln(n)   [coder les paramètres].
RSS décroît TOUJOURS avec le degré (sur-ajustement), mais le terme (k/2)ln n PÉNALISE la complexité → L est en U,
minimisée près du VRAI degré.

LE MODE D'ÉCHEC DÉMASQUÉ : sélectionner par erreur d'entraînement (minimiser RSS) choisit le modèle maximal qui
SUR-APPREND → mauvaise prédiction (sur-confiance). MDL choisit le modèle qui généralise (meilleure erreur de test).
ABSTENTION si données insuffisantes. Pur Python (moindres carrés polynomiaux, x normalisé dans [−1,1]).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
SELECTION = "selection"


def _resol(A, b):
    """Résout A·x=b par élimination de Gauss avec pivot partiel (petits systèmes symétriques définis positifs)."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-15:
            return None
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def _normalise(xs):
    a, b = min(xs), max(xs)
    if b == a:
        return [0.0 for _ in xs]
    return [2 * (x - a) / (b - a) - 1 for x in xs]


def ajuste_poly(xs, ys, d):
    """Ajuste un polynôme de degré d par moindres carrés. Renvoie les coefficients (x supposé normalisé)."""
    k = d + 1
    # matrices de Vandermonde -> équations normales XᵀX c = Xᵀy
    pw = [[x ** j for j in range(k)] for x in xs]
    A = [[sum(pw[i][r] * pw[i][c] for i in range(len(xs))) for c in range(k)] for r in range(k)]
    bvec = [sum(pw[i][r] * ys[i] for i in range(len(xs))) for r in range(k)]
    return _resol(A, bvec)


def rss(xs, ys, coeffs):
    """Somme des carrés des résidus pour des coefficients donnés (x normalisé)."""
    s = 0.0
    for x, y in zip(xs, ys):
        pred = sum(c * x ** j for j, c in enumerate(coeffs))
        s += (pred - y) ** 2
    return s


def codelength(xs, ys, d):
    """Longueur de description MDL (deux parties) du modèle polynomial de degré d."""
    n = len(xs)
    xn = _normalise(xs)
    c = ajuste_poly(xn, ys, d)
    if c is None:
        return float("inf")
    r = rss(xn, ys, c)
    k = d + 1
    erreur = (n / 2) * math.log(max(r, 1e-12) / n)
    complexite = (k / 2) * math.log(n)
    return erreur + complexite


def selectionne_mdl(xs, ys, d_max):
    """Degré minimisant la longueur de description MDL."""
    return min(range(d_max + 1), key=lambda d: codelength(xs, ys, d))


def selectionne_train(xs, ys, d_max):
    """Degré minimisant l'erreur d'entraînement (RSS) — choisit TOUJOURS le maximal (sur-ajustement)."""
    xn = _normalise(xs)
    return min(range(d_max + 1), key=lambda d: rss(xn, ys, ajuste_poly(xn, ys, d)))


def predit(xs_train, ys_train, d, x_nouveau, bornes=None):
    """Prédit en x_nouveau avec un polynôme de degré d ajusté sur (xs_train, ys_train)."""
    a, b = (min(xs_train), max(xs_train)) if bornes is None else bornes
    xn = [2 * (x - a) / (b - a) - 1 for x in xs_train]
    c = ajuste_poly(xn, ys_train, d)
    xnn = 2 * (x_nouveau - a) / (b - a) - 1
    return sum(cj * xnn ** j for j, cj in enumerate(c))


def analyse(xs, ys, d_max):
    """Façade : (SELECTION, {degre_mdl, degre_train, codelengths}) ou (ABSTENTION, raison)."""
    if len(xs) < d_max + 2 or len(xs) != len(ys):
        return (ABSTENTION, "trop peu de points pour d_max (n < d_max+2) ou tailles différentes")
    return (SELECTION, {"degre_mdl": selectionne_mdl(xs, ys, d_max),
                        "degre_train": selectionne_train(xs, ys, d_max),
                        "codelengths": [codelength(xs, ys, d) for d in range(d_max + 1)]})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Sélection impossible : {res[1]}."
    i = res[1]
    return (f"MDL choisit le degré {i['degre_mdl']} (compression optimale) ; minimiser l'erreur d'entraînement "
            f"choisirait {i['degre_train']} (sur-ajustement, sur-confiant).")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    f = lambda x: 1 - 2 * x + 0.5 * x ** 3        # vrai degré 3
    xs = [rng.uniform(-1, 1) for _ in range(40)]
    ys = [f(x) + rng.gauss(0, 0.3) for x in xs]
    print("=== LONGUEUR DE DESCRIPTION MINIMALE (MDL) ===\n")
    for d in range(8):
        print(f"  degré {d}: RSS={rss(_normalise(xs), ys, ajuste_poly(_normalise(xs), ys, d)):.2f}  "
              f"codelength MDL={codelength(xs, ys, d):.2f}")
    print(" ", formule(analyse(xs, ys, 7)))
