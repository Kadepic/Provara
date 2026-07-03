"""
PALIER 2 — SUR-DISPERSION DES COMPTAGES (Poisson vs binomiale négative, brique 48, 2026-06-26).

« Compter des événements (réclamations, défauts, visites) — mais la réalité VARIE plus qu'un Poisson ne le prédit
(hétérogénéité cachée, grappes). » Un Poisson impose Var = Moyenne ; les vrais comptages sont souvent SUR-DISPERSÉS
(Var > Moyenne). Si on suppose Poisson, l'intervalle prédictif (largeur ∝ √μ) est TROP ÉTROIT → il rate les comptages
réels → SUR-CONFIANCE.

On estime la SUR-DISPERSION  φ̂ = Var/Moyenne (φ≈1 = Poisson ; φ>1 = sur-dispersé) et on prédit par une BINOMIALE
NÉGATIVE de mêmes moyenne et variance (NegBin(r,p) : mean=r(1−p)/p, var=mean/p ⇒ p=1/φ, r=μ/(φ−1)). INVARIANT (jugé
par calibration.py) : l'intervalle NegBin couvre le comptage réel ~confiance, là où l'intervalle Poisson sous-couvre.
Un TEST de sur-dispersion dit quand Poisson suffit. ABSTENTION si trop peu de données. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 20


def moyenne_variance(comptes):
    n = len(comptes)
    if n < 2:
        return None
    m = sum(comptes) / n
    v = sum((c - m) ** 2 for c in comptes) / (n - 1)
    return (m, v)


def dispersion(comptes):
    """φ̂ = Var/Moyenne (>1 = sur-dispersé). Renvoie φ ou None."""
    mv = moyenne_variance(comptes)
    if mv is None or mv[0] <= 0:
        return None
    return mv[1] / mv[0]


def test_surdispersion(comptes):
    """Test de sur-dispersion (statistique de dispersion de Pearson ~ χ²/(n−1), approx normale). Renvoie
    (phi, z, surdisperse_bool). z grand (>2) = sur-dispersion significative."""
    mv = moyenne_variance(comptes)
    if mv is None or mv[0] <= 0:
        return None
    m = mv[0]
    n = len(comptes)
    pearson = sum((c - m) ** 2 / m for c in comptes)       # ~ χ²_{n-1} sous Poisson
    dof = n - 1
    z = (pearson - dof) / math.sqrt(2 * dof)               # normalisation
    return (mv[1] / m, z, z > 2.0)


def _qpois(m, p):
    if m <= 0:
        return 0
    kmax = int(m + 12 * math.sqrt(m) + 20)
    cum = 0.0
    pk = math.exp(-m)
    for k in range(kmax + 1):
        if k > 0:
            pk *= m / k
        cum += pk
        if cum >= p:
            return k
    return kmax


def _qnegbin(r, p, prob):
    if r <= 0:
        return 0
    log1mp = math.log(1.0 - p) if p < 1.0 else -1e9
    logpk = r * math.log(p)
    mean = r * (1.0 - p) / p
    kmax = int(mean + 15 * math.sqrt(mean + 1.0) + 30)
    cum = 0.0
    for k in range(kmax + 1):
        if k > 0:
            logpk += math.log((k - 1 + r) / k) + log1mp
        cum += math.exp(logpk)
        if cum >= prob:
            return k
    return kmax


def intervalle_poisson(comptes, confiance: float = 0.90):
    """Intervalle prédictif d'un NOUVEAU comptage sous l'hypothèse POISSON (naïf si sur-dispersé). (mean,(bas,haut))."""
    mv = moyenne_variance(comptes)
    m = mv[0]
    a = (1.0 - confiance) / 2.0
    return (m, (_qpois(m, a), _qpois(m, 1.0 - a)))


def intervalle_negbin(comptes, confiance: float = 0.90):
    """Intervalle prédictif NegBin (mêmes moyenne et variance que l'échantillon). Renvoie (ESTIMATION, (mean,(bas,
    haut)), confiance) ou ABSTENTION."""
    n = len(comptes)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu de données (n={n} < {N_MIN})")
    mv = moyenne_variance(comptes)
    if mv is None or mv[0] <= 0:
        return (ABSTENTION, None, "moyenne nulle / non estimable")
    m, v = mv
    a = (1.0 - confiance) / 2.0
    if v <= m * 1.001:                                     # pas de sur-dispersion -> Poisson
        return (ESTIMATION, (m, (_qpois(m, a), _qpois(m, 1.0 - a))), confiance)
    phi = v / m
    p = 1.0 / phi
    r = m / (phi - 1.0)
    return (ESTIMATION, (m, (_qnegbin(r, p, a), _qnegbin(r, p, 1.0 - a))), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas prédire le comptage : {res[2]}."
    m, (bas, haut) = res[1][0], res[1][1]
    conf = res[2]
    return (f"Comptage attendu ≈ {m:.1f} (à {round(conf*100)}% entre {bas} et {haut}). Sur-dispersion prise en "
            f"compte — supposer un Poisson donnerait un intervalle trop étroit.")


if __name__ == "__main__":
    import random
    print("=== SUR-DISPERSION DES COMPTAGES (Poisson vs NegBin) ===\n")
    rng = random.Random(0)
    # comptes sur-dispersés : mélange Poisson-Gamma (NegBin), moyenne 8, φ≈3
    MU, PHI = 8.0, 3.0
    p = 1.0 / PHI; r = MU / (PHI - 1.0)
    def tire():
        lam = rng.gammavariate(r, (1 - p) / p)            # Gamma -> NegBin
        k = 0; L = math.exp(-lam); q = 1.0
        while True:
            q *= rng.random()
            if q <= L:
                break
            k += 1
        return k
    comptes = [tire() for _ in range(300)]
    phi, z, sur = test_surdispersion(comptes)
    print(f"  φ̂={phi:.2f} (vrai {PHI}) ; z={z:.1f} ; sur-dispersé={sur}")
    print("  Poisson :", intervalle_poisson(comptes, 0.90))
    print("  NegBin  :", formule(intervalle_negbin(comptes, 0.90)))
