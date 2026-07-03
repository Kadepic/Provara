"""
PALIER 2 — JACKKNIFE+ CONFORME (brique 20, 2026-06-25). La couverture SANS sacrifier de données à un split.

Le conforme split (conformal.py) gâche une partie des données pour la calibration. Le JACKKNIFE+ (Barber, Candès,
Ramdas, Tibshirani 2021) utilise TOUTES les données via le LEAVE-ONE-OUT : pour chaque point i, on note le résidu
hors-échantillon Rᵢ = |yᵢ − μ₋ᵢ(xᵢ)| (μ₋ᵢ = modèle ajusté SANS i). Pour un point test x, l'intervalle est

    [ q⁻_α { μ₋ᵢ(x) − Rᵢ } ,  q⁺_{1−α} { μ₋ᵢ(x) + Rᵢ } ]

GARANTIE (distribution-free, échangeabilité) : couverture ≥ 1 − 2α (en pratique ≈ 1 − α). Idéal en PETIT échantillon
(rien n'est gaspillé). Fourni : la fonction générique (on lui passe les μ₋ᵢ(x) et les Rᵢ) + une commodité « prédicteur
moyenne » (LOO trivial) pour l'utiliser clé en main. ABSTENTION si trop peu de points.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 10


def _q_bas(valeurs, alpha):
    """q⁻_α : ⌊α(n+1)⌋-ième plus petite valeur (ou −inf si trop peu)."""
    v = sorted(valeurs)
    n = len(v)
    k = math.floor(alpha * (n + 1))
    if k < 1:
        return float("-inf")
    return v[k - 1]


def _q_haut(valeurs, alpha):
    """q⁺_{1−α} : ⌈(1−α)(n+1)⌉-ième plus petite valeur (ou +inf si trop peu)."""
    v = sorted(valeurs)
    n = len(v)
    k = math.ceil((1.0 - alpha) * (n + 1))
    if k > n:
        return float("inf")
    return v[k - 1]


def intervalle_jackknife_plus(mu_loo_test, residus_loo, alpha=0.1):
    """Intervalle jackknife+ générique. `mu_loo_test[i]` = μ₋ᵢ(x_test) ; `residus_loo[i]` = Rᵢ. Renvoie
    (ESTIMATION, (bas, haut), 1−α) ou ABSTENTION. Couverture garantie ≥ 1−2α."""
    if len(mu_loo_test) != len(residus_loo):
        raise ValueError("mu_loo_test et residus_loo de tailles différentes")
    n = len(residus_loo)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={n} < {N_MIN})")
    bas_vals = [mu_loo_test[i] - residus_loo[i] for i in range(n)]
    haut_vals = [mu_loo_test[i] + residus_loo[i] for i in range(n)]
    return (ESTIMATION, (_q_bas(bas_vals, alpha), _q_haut(haut_vals, alpha)), 1.0 - alpha)


def jackknife_plus_moyenne(ys, alpha=0.1):
    """Commodité : prédicteur = MOYENNE (LOO trivial μ₋ᵢ = moyenne sans i, indépendant de x). Renvoie une fonction
    `intervalle()` (l'intervalle est le même pour tout x) ou (ABSTENTION, ...) si trop peu. Démontre la garantie
    jackknife+ clé en main, sans dépendance à un modèle externe."""
    y = [float(v) for v in ys]
    n = len(y)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={n} < {N_MIN})")
    s = sum(y)
    mu_loo = [(s - y[i]) / (n - 1) for i in range(n)]           # μ₋ᵢ = moyenne sans i
    residus = [abs(y[i] - mu_loo[i]) for i in range(n)]
    return intervalle_jackknife_plus(mu_loo, residus, alpha)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[2]}."
    _, (bas, haut), conf = res
    return f"La vraie valeur est entre {bas:.2f} et {haut:.2f} (garantie ≥ {round(conf*100)}%, sans gâcher de données)."


if __name__ == "__main__":
    print("=== JACKKNIFE+ CONFORME ===\n")
    import random
    rng = random.Random(0)
    ys = [rng.gauss(10, 2) for _ in range(60)]
    print(" ", formule(jackknife_plus_moyenne(ys, 0.1)))
    print(" ", formule(jackknife_plus_moyenne([1, 2, 3], 0.1)))   # trop peu
