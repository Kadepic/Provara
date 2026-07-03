"""
PALIER 2 — INFÉRENCE ANYTIME-VALID (séquence de confiance, brique 35, 2026-06-25).

Un intervalle de confiance CLASSIQUE n'est valide qu'à un instant FIXÉ. Si on REGARDE les données au fil de l'eau et
qu'on s'arrête « quand ça nous arrange » (peeking), le taux d'erreur EXPLOSE — un piège réel (essais A/B arrêtés tôt).
La SÉQUENCE DE CONFIANCE (Robbins, mélange normal) est valide À TOUS LES INSTANTS SIMULTANÉMENT :

  P( ∃t : μ ∉ ICₜ ) ≤ α          ->  on peut surveiller en continu et s'arrêter n'importe quand, sans tricher.

Rayon (sous-gaussien de proxy σ, mélange normal de paramètre ρ) :
  rayonₜ = √( 2σ²(t+ρ)·[ ln(1/α) + ½·ln((t+ρ)/ρ) ] ) / t           ICₜ = X̄ₜ ± rayonₜ

Prix de cette validité « anytime » : l'intervalle est un peu plus large qu'un IC à instant fixe (qui, lui, ment dès
qu'on regarde plusieurs fois). INVARIANT (prouvé MC) : la couverture UNIFORME-EN-TEMPS ≥ 1−α, là où un IC fixe répété
sous-couvre. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def rayon_cs(t, sigma, alpha=0.05, rho=1.0):
    """Rayon de la séquence de confiance à l'instant t (≥1) pour une moyenne sous-gaussienne de proxy `sigma`."""
    if t < 1:
        return float("inf")
    return math.sqrt(2.0 * sigma * sigma * (t + rho) * (math.log(1.0 / alpha) + 0.5 * math.log((t + rho) / rho))) / t


class SequenceConfiance:
    """Séquence de confiance en ligne pour une moyenne. `observe(x)` à chaque obs ; `intervalle()` à tout instant
    donne un IC valide même si on a regardé/arrêté quand on voulait. `sigma` = proxy sous-gaussien (écart-type connu
    ou borne)."""

    __slots__ = ("sigma", "alpha", "rho", "somme", "t")

    def __init__(self, sigma, alpha=0.05, rho=1.0):
        self.sigma = float(sigma)
        self.alpha = alpha
        self.rho = rho
        self.somme = 0.0
        self.t = 0

    def observe(self, x):
        self.somme += float(x)
        self.t += 1

    def intervalle(self):
        if self.t < 1:
            return (ABSTENTION, None, "aucune observation")
        moy = self.somme / self.t
        r = rayon_cs(self.t, self.sigma, self.alpha, self.rho)
        return (ESTIMATION, (moy, (moy - r, moy + r)), 1.0 - self.alpha)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas conclure : {res[2]}."
    moy, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Moyenne estimée ~{moy:.3f} (intervalle valide À TOUT INSTANT à {round(conf*100)}% : {bas:.3f} à {haut:.3f}) "
            "— je peux continuer à observer et m'arrêter quand je veux sans fausser ce niveau.")


if __name__ == "__main__":
    print("=== INFÉRENCE ANYTIME-VALID ===\n")
    import random
    rng = random.Random(0)
    cs = SequenceConfiance(sigma=1.0, alpha=0.05)
    for n in (10, 100, 1000):
        while cs.t < n:
            cs.observe(rng.gauss(0.3, 1.0))
        print(f"  après {n:4} obs :", formule(cs.intervalle()))
