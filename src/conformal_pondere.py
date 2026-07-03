"""
PALIER 2 — CONFORME PONDÉRÉ SOUS COVARIATE SHIFT (brique 17, 2026-06-25). La couverture quand le TEST diffère du TRAIN.

Le conforme (conformal.py) suppose l'ÉCHANGEABILITÉ calibration↔test. Si la distribution des ENTRÉES change
(covariate shift : p_test(x) ≠ p_cal(x), mais P(y|x) inchangé), l'échangeabilité tombe et la couverture est perdue —
le conforme devient SUR-confiant sans le savoir. Le CONFORME PONDÉRÉ (Tibshirani et al. 2019) la restaure en PONDÉRANT
chaque point de calibration par le RAPPORT DE VRAISEMBLANCE w(x) = p_test(x) / p_cal(x) : les points de calibration
qui « ressemblent » au régime de test pèsent plus.

Quantile pondéré (au niveau 1−α) sur les résidus de calibration {rᵢ} de poids {wᵢ}, le point test recevant le poids
w(x_test) placé à +∞ :
    q = plus petit r tel que   Σ_{i: rᵢ ≤ r} pᵢ ≥ 1−α,   pᵢ = wᵢ / (Σ wⱼ + w_test)
Si la masse des résidus finis n'atteint pas 1−α (poids test trop grand), q = +∞ -> intervalle non borné (prudent).

INVARIANT (jugé par calibration.py) : avec les bons poids, la couverture ≥ 1−α MÊME sous décalage, là où le conforme
non pondéré SOUS-COUVRE (SURCONFIANT). Sans décalage (w≡1), on retombe exactement sur le conforme standard.
ABSTENTION si trop peu de points.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 10


def quantile_pondere(residus, poids, poids_test, alpha=0.1):
    """Quantile conforme PONDÉRÉ au niveau 1−α. Renvoie q (float, possiblement +inf) ou None si trop peu de points."""
    paires = sorted((abs(float(r)), float(w)) for r, w in zip(residus, poids))
    n = len(paires)
    if n < N_MIN:
        return None
    total = sum(w for _, w in paires) + float(poids_test)
    if total <= 0:
        return None
    cible = 1.0 - alpha
    cumul = 0.0
    for r, w in paires:
        cumul += w / total
        if cumul >= cible:
            return r
    return float("inf")             # même tous les résidus finis n'atteignent pas 1−α -> non borné (prudent)


def intervalle_pondere(residus_cal, poids_cal, poids_test, prediction, alpha=0.1):
    """Intervalle conforme pondéré autour de `prediction`. (ESTIMATION, (bas, haut), 1−α) ou ABSTENTION."""
    q = quantile_pondere(residus_cal, poids_cal, poids_test, alpha)
    if q is None:
        return (ABSTENTION, None, f"trop peu de points de calibration (n={len(list(residus_cal))})")
    p = float(prediction)
    return (ESTIMATION, (p - q, p + q), 1.0 - alpha)


def poids_ratio_gaussien(x, mu_cal, sd_cal, mu_test, sd_test):
    """Rapport de vraisemblance w(x) = N(x; mu_test, sd_test) / N(x; mu_cal, sd_cal) pour un shift gaussien connu."""
    def dens(v, mu, sd):
        return math.exp(-0.5 * ((v - mu) / sd) ** 2) / sd
    return dens(x, mu_test, sd_test) / dens(x, mu_cal, sd_cal)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[2]}."
    _, (bas, haut), conf = res
    if math.isinf(haut - bas):
        return f"Je ne peux pas borner l'intervalle à {round(conf*100)}% sous ce décalage : trop d'incertitude — je m'abstiens."
    return (f"La vraie valeur est entre {bas:.2f} et {haut:.2f} (garantie {round(conf*100)}%), corrigée du décalage "
            "entre mes données et la situation actuelle.")


if __name__ == "__main__":
    print("=== CONFORME PONDÉRÉ SOUS COVARIATE SHIFT ===\n")
    import random
    rng = random.Random(0)
    # bruit hétéroscédastique σ(x)=0.5+|x| ; calibration x~N(0,1), test décalé x~N(1.5,1)
    xs = [rng.gauss(0, 1) for _ in range(400)]
    residus = [rng.gauss(0, 0.5 + abs(x)) for x in xs]
    poids = [poids_ratio_gaussien(x, 0, 1, 1.5, 1) for x in xs]
    x_test = 1.5
    w_test = poids_ratio_gaussien(x_test, 0, 1, 1.5, 1)
    print(" pondéré :", formule(intervalle_pondere(residus, poids, w_test, 0.0)))
    print(" non pondéré (poids=1) :", formule(intervalle_pondere(residus, [1] * len(residus), 1.0, 0.0)))
