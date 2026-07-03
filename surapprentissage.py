"""
PALIER 2 — SUR-APPRENTISSAGE (overfitting) : se fier à l'ajustement EN ÉCHANTILLON est sur-confiant (brique 131, 2026-06-28).

Un modèle assez flexible (polynôme de degré élevé) peut ajuster PARFAITEMENT les données d'entraînement — erreur quasi
nulle, R² ≈ 1 — tout en GÉNÉRALISANT très mal. Juger un modèle sur sa performance EN ÉCHANTILLON est donc SUR-CONFIANT :
l'erreur d'entraînement DÉCROÎT toujours avec la complexité, mais l'erreur HORS échantillon (test) suit une courbe en U —
minimale à la BONNE complexité, puis explose quand le modèle « apprend le bruit ».

LA CORRECTION : estimer l'erreur de généralisation par VALIDATION CROISÉE / hold-out (ou pénaliser la complexité), et
choisir la complexité qui minimise l'erreur de validation — pas l'erreur d'entraînement.

LE MODE D'ÉCHEC DÉMASQUÉ : conclure qu'un modèle est bon parce qu'il colle aux données d'entraînement est sur-confiant ;
l'écart test − train (l'« optimisme ») croît avec la complexité. À la bonne complexité, train ≈ test (honnêteté).
Distinct des bornes de généralisation (PAC 63, Rademacher 66, MDL 76) — ici la divergence EMPIRIQUE train/test. rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _vraie(x):
    return 1.0 + 2.0 * x          # vraie fonction : LINÉAIRE


def genere(n, rng, bruit=0.5):
    X = [rng.uniform(-1, 1) for _ in range(n)]
    Y = [_vraie(x) + rng.gauss(0, bruit) for x in X]
    return X, Y


def ajuste_poly(X, Y, deg):
    """Régression polynomiale de degré deg par équations normales (Vandermonde)."""
    m = deg + 1
    A = [[sum(x ** (i + j) for x in X) for j in range(m)] for i in range(m)]
    b = [sum(Y[k] * X[k] ** i for k in range(len(X))) for i in range(m)]
    M = [A[i][:] + [b[i]] for i in range(m)]
    for c in range(m):
        p = max(range(c, m), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        if abs(pv) < 1e-14:
            continue
        M[c] = [v / pv for v in M[c]]
        for r in range(m):
            if r != c:
                f = M[r][c]
                M[r] = [M[r][k] - f * M[c][k] for k in range(m + 1)]
    return [M[r][m] for r in range(m)]


def _pred(coef, x):
    return sum(c * x ** i for i, c in enumerate(coef))


def mse(coef, X, Y):
    return sum((_pred(coef, x) - y) ** 2 for x, y in zip(X, Y)) / len(X)


def degre_par_holdout(Xtr, Ytr, degres, frac_val=0.4):
    """Choisit le degré minimisant l'erreur sur un hold-out (validation), pas l'erreur d'entraînement."""
    k = max(2, int(len(Xtr) * (1 - frac_val)))
    Xa, Ya = Xtr[:k], Ytr[:k]
    Xv, Yv = Xtr[k:], Ytr[k:]
    best, best_err = degres[0], float("inf")
    for d in degres:
        if d + 1 > len(Xa):
            continue
        err = mse(ajuste_poly(Xa, Ya, d), Xv, Yv)
        if err < best_err:
            best_err, best = err, d
    return best


def analyse(degres=(1, 2, 3, 5, 7, 9), n_train=15, rng=None):
    """Façade : courbes train/test selon la complexité. (ANALYSE, {courbe, degre_choisi_holdout}) ou (ABSTENTION)."""
    if rng is None or n_train < 6:
        return (ABSTENTION, "rng requis / trop peu de données")
    Xtr, Ytr = genere(n_train, rng)
    Xte, Yte = genere(3000, rng)
    courbe = []
    for d in degres:
        coef = ajuste_poly(Xtr, Ytr, d)
        courbe.append((d, {"mse_train": mse(coef, Xtr, Ytr), "mse_test": mse(coef, Xte, Yte)}))
    return (ANALYSE, {"courbe": courbe, "degre_choisi_holdout": degre_par_holdout(Xtr, Ytr, list(degres))})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    c = res[1]["courbe"]
    bas, haut = c[0][1], c[-1][1]
    return (f"Degré {c[0][0]} : train={bas['mse_train']:.2f}, test={bas['mse_test']:.2f}. Degré {c[-1][0]} : "
            f"train={haut['mse_train']:.2f} (mieux !) mais test={haut['mse_test']:.1f} (explose). Le hold-out choisit le "
            f"degré {res[1]['degre_choisi_holdout']}. Se fier à l'ajustement en échantillon est sur-confiant — l'erreur "
            f"de généralisation suit une courbe en U.")


if __name__ == "__main__":
    import random
    print("=== SUR-APPRENTISSAGE (overfitting) ===\n")
    st, info = analyse(rng=random.Random(0))
    for d, m in info["courbe"]:
        print(f"  degré {d:2d}: MSE train={m['mse_train']:.3f}  MSE test={m['mse_test']:.2f}")
    print("\n ", formule((st, info)))
