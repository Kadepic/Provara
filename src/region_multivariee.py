"""
PALIER 2 — RÉGIONS DE PRÉDICTION MULTIVARIÉES CONFORMES (Mahalanobis, brique 42, 2026-06-26).

« Prédire un vecteur (pas un scalaire) — position (lat, lon), (taille, poids), (prix, volume) — avec une RÉGION qui
contient la vraie valeur avec 90 % de chance. » Le piège naïf : prendre un intervalle à 90 % PAR coordonnée et les
croiser en une BOÎTE. Quand les coordonnées sont corrélées (ou simplement d>1), la couverture JOINTE de cette boîte
tombe BIEN sous 90 % → SUR-CONFIANCE (on croit couvrir 90 %, on couvre 70 %).

La PRÉDICTION CONFORME multivariée le répare sans hypothèse de loi : on mesure la non-conformité par la distance de
MAHALANOBIS  D²(y) = (y−μ̂)ᵀ Σ̂⁻¹ (y−μ̂)  (μ̂, Σ̂ estimés sur un sous-échantillon d'apprentissage), on calibre le SEUIL
sur un jeu de calibration indépendant (quantile conforme (⌈(n+1)(1−α)⌉)/n), et la région = { y : D²(y) ≤ seuil }.
GARANTIE distribution-free : couverture jointe ≥ 1−α en échantillon fini, sous échangeabilité — quelles que soient la
forme/corrélation. INVARIANT (jugé par calibration.py) : la région conforme couvre ~1−α, la boîte marginale SOUS-couvre.
ABSTENTION si calibration trop petite / covariance singulière. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_CAL = 20


def _moyenne_vec(rows):
    d = len(rows[0])
    mu = [0.0] * d
    for r in rows:
        for j in range(d):
            mu[j] += r[j]
    n = len(rows)
    for j in range(d):
        mu[j] /= n
    return mu


def _cov(rows, mu):
    n = len(rows)
    d = len(mu)
    S = [[0.0] * d for _ in range(d)]
    for r in rows:
        for i in range(d):
            di = r[i] - mu[i]
            for j in range(d):
                S[i][j] += di * (r[j] - mu[j])
    inv = 1.0 / (n - 1) if n > 1 else 1.0
    for i in range(d):
        for j in range(d):
            S[i][j] *= inv
    return S


def _inv(M):
    """Inverse par Gauss-Jordan avec pivot partiel. Renvoie None si singulière."""
    d = len(M)
    A = [[M[i][j] for j in range(d)] + [1.0 if i == k else 0.0 for k in range(d)] for i in range(d)]
    for col in range(d):
        piv = col
        for r in range(col + 1, d):
            if abs(A[r][col]) > abs(A[piv][col]):
                piv = r
        if abs(A[piv][col]) < 1e-12:
            return None
        A[col], A[piv] = A[piv], A[col]
        pv = A[col][col]
        for j in range(2 * d):
            A[col][j] /= pv
        for r in range(d):
            if r != col:
                f = A[r][col]
                if f != 0.0:
                    for j in range(2 * d):
                        A[r][j] -= f * A[col][j]
    return [[A[i][j + d] for j in range(d)] for i in range(d)]


def _mahal(y, mu, Sinv):
    d = len(mu)
    diff = [y[j] - mu[j] for j in range(d)]
    s = 0.0
    for i in range(d):
        acc = 0.0
        for j in range(d):
            acc += Sinv[i][j] * diff[j]
        s += diff[i] * acc
    return s


def region_conforme(train, calib, alpha: float = 0.10):
    """Région conforme de Mahalanobis. `train` estime μ̂/Σ̂ ; `calib` fixe le seuil (quantile conforme). Renvoie
    (ESTIMATION, {'mu','Sinv','seuil'}, 1−alpha) ou (ABSTENTION, None, raison)."""
    if len(calib) < N_MIN_CAL or len(train) < N_MIN_CAL:
        return (ABSTENTION, None, f"trop peu de données (train={len(train)}, calib={len(calib)}, min={N_MIN_CAL})")
    mu = _moyenne_vec(train)
    Sinv = _inv(_cov(train, mu))
    if Sinv is None:
        return (ABSTENTION, None, "covariance singulière (coordonnées colinéaires)")
    scores = []
    for y in calib:
        scores.append(_mahal(y, mu, Sinv))
    scores.sort()
    n = len(scores)
    k = math.ceil((n + 1) * (1.0 - alpha))
    if k > n:
        return (ABSTENTION, None, "calibration trop petite pour le niveau demandé (1−alpha non atteignable)")
    seuil = scores[k - 1]
    return (ESTIMATION, {"mu": mu, "Sinv": Sinv, "seuil": seuil}, 1.0 - alpha)


def dans_region(region, y) -> bool:
    return _mahal(y, region["mu"], region["Sinv"]) <= region["seuil"]


def boite_marginale(train, alpha: float = 0.10):
    """Boîte NAÏVE : intervalle empirique (1−alpha) PAR coordonnée, croisé. Sous-couvre le joint quand d>1/corrélé —
    sert à démasquer le piège. Renvoie un dict {'bornes': [(bas, haut), ...]}."""
    d = len(train[0])
    bornes = []
    for j in range(d):
        col = sorted(r[j] for r in train)
        n = len(col)
        lo = col[int((alpha / 2.0) * (n - 1))]
        hi = col[int((1.0 - alpha / 2.0) * (n - 1))]
        bornes.append((lo, hi))
    return {"bornes": bornes}


def dans_boite(box, y) -> bool:
    for j in range(len(y)):
        lo, hi = box["bornes"][j]
        if y[j] < lo or y[j] > hi:
            return False
    return True


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas construire de région de prédiction : {res[2]}."
    conf = res[2]
    d = len(res[1]["mu"])
    return (f"Région de prédiction conforme à {round(conf*100)}% en dimension {d} (ellipsoïde de Mahalanobis). "
            f"Couverture jointe garantie — une simple boîte par coordonnée, elle, sous-couvrirait.")


if __name__ == "__main__":
    import random
    print("=== RÉGIONS MULTIVARIÉES CONFORMES (Mahalanobis) ===\n")
    rng = random.Random(0)

    def echantillon(n):
        out = []
        for _ in range(n):
            z1 = rng.gauss(0, 1)
            z2 = 0.8 * z1 + 0.6 * rng.gauss(0, 1)     # corrélées
            out.append((10 + 2 * z1, 5 + 1.5 * z2))
        return out

    train = echantillon(300)
    calib = echantillon(300)
    test = echantillon(4000)
    st, reg, conf = region_conforme(train, calib, 0.10)
    box = boite_marginale(train + calib, 0.10)
    cov_reg = sum(1 for y in test if dans_region(reg, y)) / len(test)
    cov_box = sum(1 for y in test if dans_boite(box, y)) / len(test)
    print(f"  couverture cible = 0.90")
    print(f"  région conforme (Mahalanobis) : {cov_reg:.3f}  -> {formule((st, reg, conf))}")
    print(f"  boîte marginale par coordonnée : {cov_box:.3f}  (sous-couvre = sur-confiance)")
