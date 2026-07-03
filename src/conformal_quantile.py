"""
PALIER 2 — CQR : CONFORMALIZED QUANTILE REGRESSION (brique 21, 2026-06-25). Des intervalles ADAPTATIFS et VALIDES.

Un modèle de quantiles prédit une bande [q_bas(x), q_haut(x)] (ex. quantiles α/2 et 1−α/2). Cette bande ÉPOUSE la
difficulté locale (étroite où c'est facile, large où c'est dur) — mais sa couverture n'est PAS garantie (le modèle
peut être mal calibré). Le CQR (Romano, Patterson, Candès 2019) la RECALIBRE sans rien perdre de son adaptivité :

  score de non-conformité  Eᵢ = max( q_bas(xᵢ) − yᵢ ,  yᵢ − q_haut(xᵢ) )       (>0 si yᵢ hors bande)
  correction conforme      Q  = quantile (1−α) des {Eᵢ}                         (peut être négatif = resserrer)
  intervalle final         [ q_bas(x) − Q ,  q_haut(x) + Q ]

GARANTIE (distribution-free) : couverture ≥ 1−α. DOUBLE AVANTAGE vs conforme à largeur constante : valide ET adaptatif
(la largeur varie avec x). INVARIANT jugé par calibration.py. ABSTENTION si trop peu de points.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 10


def scores_cqr(q_bas_cal, q_haut_cal, y_cal):
    """Scores de non-conformité Eᵢ = max(q_bas − y, y − q_haut)."""
    return [max(float(qb) - float(y), float(y) - float(qh))
            for qb, qh, y in zip(q_bas_cal, q_haut_cal, y_cal)]


def correction_cqr(scores, alpha=0.1):
    """Correction conforme Q = quantile (1−α) des scores (avec correction (n+1)). +inf si trop peu pour le niveau."""
    s = sorted(float(x) for x in scores)
    n = len(s)
    if n < N_MIN:
        return None
    k = math.ceil((1.0 - alpha) * (n + 1))
    if k > n:
        return float("inf")
    return s[k - 1]


def ajuste_cqr(q_bas_cal, q_haut_cal, y_cal, alpha=0.1):
    """Renvoie la correction Q (à appliquer à toute bande prédite) ou None si trop peu de points."""
    return correction_cqr(scores_cqr(q_bas_cal, q_haut_cal, y_cal), alpha)


def intervalle_cqr(q_bas_test, q_haut_test, Q, alpha=0.1):
    """Intervalle CQR recalibré pour une bande prédite (q_bas, q_haut) et la correction Q. (ESTIMATION, (bas,haut), 1−α)
    ou ABSTENTION si Q indisponible."""
    if Q is None:
        return (ABSTENTION, None, "correction CQR indisponible (trop peu de calibration)")
    return (ESTIMATION, (float(q_bas_test) - Q, float(q_haut_test) + Q), 1.0 - alpha)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[2]}."
    _, (bas, haut), conf = res
    return f"La vraie valeur est entre {bas:.2f} et {haut:.2f} (garantie {round(conf*100)}%, largeur adaptée à la difficulté locale)."


if __name__ == "__main__":
    print("=== CQR : CONFORMALIZED QUANTILE REGRESSION ===\n")
    import random
    rng = random.Random(0)
    # bruit hétéroscédastique σ(x)=0.3+|x| ; bande prédite TROP ÉTROITE (×0.6) -> sous-couvre sans CQR
    def sigma(x):
        return 0.3 + abs(x)
    xs = [rng.gauss(0, 1) for _ in range(300)]
    ys = [rng.gauss(0, sigma(x)) for x in xs]
    qb = [-1.0 * sigma(x) for x in xs]      # ~ quantile bas trop serré
    qh = [1.0 * sigma(x) for x in xs]
    Q = ajuste_cqr(qb, qh, ys, 0.1)
    print(f"  correction Q = {Q:.3f}")
    print("  x facile (0.1) :", formule(intervalle_cqr(-1 * sigma(0.1), 1 * sigma(0.1), Q)))
    print("  x dur (3.0)    :", formule(intervalle_cqr(-1 * sigma(3.0), 1 * sigma(3.0), Q)))
