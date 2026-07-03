"""
PALIER 2 — BAYÉSIEN SÉQUENTIEL (Beta-Bernoulli en ligne, brique 34, 2026-06-25).

Apprendre une PROPORTION inconnue AU FIL DE L'EAU (taux de clic, taux de panne, taux de succès), avec une incertitude
qui se resserre HONNÊTEMENT à mesure que les observations arrivent. Conjugaison Beta-Bernoulli :

  a priori θ ~ Beta(a₀, b₀)  ;  après k succès / m échecs :  θ | données ~ Beta(a₀+k, b₀+m)
  estimation = moyenne postérieure (a₀+k)/(a₀+b₀+k+m)  ;  INTERVALLE CRÉDIBLE = quantiles de la Beta postérieure.

Mise à jour O(1) par observation (pas de recalcul). INVARIANT (jugé par calibration.py) : sous a priori cohérent
(θ tiré de Beta(a₀,b₀)), l'intervalle crédible à `confiance` couvre le vrai θ ~`confiance` (couverture bayésienne
exacte) ; l'intervalle RÉTRÉCIT en 1/√n. Implémente la Beta incomplète + son inverse (pur Python, sans lib).
"""
from __future__ import annotations

import math

_EPS = 1e-12


def _betacf(a, b, x):
    """Fraction continue pour la Beta incomplète (Lentz). Numerical Recipes."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return h


def betai(a, b, x):
    """Beta incomplète régularisée I_x(a,b) = CDF d'une Beta(a,b) en x."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def quantile_beta(p, a, b):
    """Quantile (inverse CDF) d'une Beta(a,b) par bissection sur I_x(a,b)."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if betai(a, b, mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


class BetaBernoulli:
    """Postérieure Beta-Bernoulli mise à jour en ligne. `observe(succes)` à chaque observation 0/1."""

    __slots__ = ("a", "b", "a0", "b0")

    def __init__(self, a0=1.0, b0=1.0):
        self.a0 = a0
        self.b0 = b0
        self.a = a0
        self.b = b0

    def observe(self, succes):
        if succes:
            self.a += 1.0
        else:
            self.b += 1.0

    def observe_lot(self, succes, total):
        self.a += succes
        self.b += (total - succes)

    def moyenne(self):
        return self.a / (self.a + self.b)

    def intervalle_credible(self, confiance=0.90):
        alpha = (1.0 - confiance) / 2.0
        return (quantile_beta(alpha, self.a, self.b), quantile_beta(1.0 - alpha, self.a, self.b))

    def n(self):
        return (self.a - self.a0) + (self.b - self.b0)


def formule(bb, confiance=0.90):
    m = bb.moyenne()
    bas, haut = bb.intervalle_credible(confiance)
    return (f"D'après {int(bb.n())} observations, j'estime la proportion à ~{round(m*100)}% "
            f"(à {round(confiance*100)}% de crédibilité : entre {round(bas*100)}% et {round(haut*100)}%).")


if __name__ == "__main__":
    print("=== BAYÉSIEN SÉQUENTIEL (Beta-Bernoulli) ===\n")
    import random
    rng = random.Random(0)
    vrai = 0.3
    bb = BetaBernoulli()
    for n in (10, 100, 1000):
        while bb.n() < n:
            bb.observe(1 if rng.random() < vrai else 0)
        print(f"  après {n:4} obs :", formule(bb))
