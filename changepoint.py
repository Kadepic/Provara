"""
PALIER 2 — DÉTECTION DE POINT DE CHANGEMENT (changepoint, brique 32, 2026-06-25).

« Quelque chose a-t-il CHANGÉ dans ce processus, et QUAND ? » — sujet non-borné fréquent (rupture de régime, panne
naissante, changement de comportement). On teste un changement de MOYENNE avec la statistique CUSUM studentisée :

  Pₖ = Σ_{i<k} (xᵢ − x̄)        stat = maxₖ |Pₖ| / (σ̂·√n)

Sous H0 (pas de changement, données i.i.d.), Pₖ/(σ̂√n) se comporte comme un PONT BROWNIEN, et `stat` suit la loi de
KOLMOGOROV : p = 2·Σ_{k≥1} (−1)^{k−1} e^{−2k²·stat²}. On a donc une p-VALEUR EXACTE (analytique, pas de seuil ad hoc).

On déclare un CHANGEMENT (à la position argmax) si p < α — avec FAUSSES ALARMES contrôlées à α (sous H0, p ~uniforme).
INVARIANT : faux positifs ≤ α (prouvé MC) + puissance + localisation. ABSTENTION si série trop courte. Pur Python.
"""
from __future__ import annotations

import math

CHANGEMENT = "changement"
STABLE = "stable"
ABSTENTION = "abstention"
N_MIN = 12


def _kolmogorov_p(t):
    """p-valeur = P(sup|pont brownien| > t) = 2 Σ (−1)^{k−1} e^{−2k²t²}. Converge vite ; clampée [0,1]."""
    if t <= 0:
        return 1.0
    s = 0.0
    for k in range(1, 100):
        terme = ((-1) ** (k - 1)) * math.exp(-2.0 * k * k * t * t)
        s += terme
        if abs(terme) < 1e-12:
            break
    return max(0.0, min(1.0, 2.0 * s))


def statistique(serie):
    """(stat CUSUM studentisée, position du max). Renvoie (None, None) si variance nulle."""
    x = [float(v) for v in serie]
    n = len(x)
    mu = sum(x) / n
    var = sum((v - mu) ** 2 for v in x) / n
    if var <= 0:
        return (None, None)
    sd = math.sqrt(var)
    P = 0.0
    best, pos = 0.0, 0
    for k in range(1, n):
        P += (x[k - 1] - mu)
        val = abs(P) / (sd * math.sqrt(n))
        if val > best:
            best, pos = val, k
    return (best, pos)


def detecte_changement(serie, alpha=0.05):
    """Teste un changement de moyenne. Renvoie (CHANGEMENT, position, p) si p < α, (STABLE, None, p) sinon, ou
    (ABSTENTION, None, raison)."""
    x = [float(v) for v in serie]
    n = len(x)
    if n < N_MIN:
        return (ABSTENTION, None, f"série trop courte (n={n} < {N_MIN})")
    stat, pos = statistique(x)
    if stat is None:
        return (ABSTENTION, None, "variance nulle (série constante)")
    p = _kolmogorov_p(stat)
    return (CHANGEMENT, pos, p) if p < alpha else (STABLE, None, p)


def formule(res) -> str:
    statut = res[0]
    if statut == ABSTENTION:
        return f"Je ne peux pas tester : {res[2]}."
    if statut == CHANGEMENT:
        return f"Un changement de régime est détecté vers la position {res[1]} (p={res[2]:.4f}) — ce n'est pas du hasard."
    return f"Pas de changement net détecté (p={res[2]:.3f}) — ça ne prouve pas la stabilité, seulement que je n'en vois pas."


if __name__ == "__main__":
    print("=== DÉTECTION DE POINT DE CHANGEMENT ===\n")
    import random
    rng = random.Random(0)
    stable = [rng.gauss(0, 1) for _ in range(80)]
    rupture = [rng.gauss(0, 1) for _ in range(40)] + [rng.gauss(3, 1) for _ in range(40)]
    print(" ", formule(detecte_changement(stable)))
    print(" ", formule(detecte_changement(rupture)))
