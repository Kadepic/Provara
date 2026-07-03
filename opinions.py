"""
PALIER 2 — AGRÉGATION D'OPINIONS D'EXPERTS (brique 25, 2026-06-25).

Plusieurs experts donnent chacun une probabilité P(événement). Comment les FUSIONNER honnêtement, sans qu'un mauvais
expert ne pollue le verdict ? Deux règles de pooling + une pondération par FIABILITÉ apprise du passé :

  • Pool LINÉAIRE : p = Σ wᵢ·pᵢ (moyenne pondérée). Robuste, conserve l'incertitude (jamais plus sûr que la moyenne).
  • Pool LOGARITHMIQUE : p ∝ Π pᵢ^wᵢ (moyenne géométrique normalisée). Plus TRANCHÉ (consensus = renforcement),
    « externally Bayesian ». À manier avec prudence (peut sur-confier si les experts sont corrélés).
  • POIDS DE FIABILITÉ : wᵢ ∝ 1 / log-loss passé de l'expert i -> les bons priment, les mauvais s'effacent.

INVARIANT (jugé par scores_propres.py / calibration.py) : la pondération par fiabilité rend le pool ROBUSTE — ajouter
un expert catastrophique ne le dégrade quasi pas (son poids tend vers 0), alors qu'une moyenne naïve serait tirée vers
le bas. Le pool bat l'expert moyen. Pur Python, model-free.
"""
from __future__ import annotations

import math

_EPS = 1e-12


def _norme(poids, noms):
    s = sum(poids[n] for n in noms)
    if s <= 0:
        return {n: 1.0 / len(noms) for n in noms}
    return {n: poids[n] / s for n in noms}


def pool_lineaire(probas_experts, poids=None):
    """Pool linéaire (moyenne pondérée) des probabilités {expert: p}. `poids` dict ou None (uniforme)."""
    noms = list(probas_experts)
    if poids is None:
        poids = {n: 1.0 for n in noms}
    w = _norme(poids, noms)
    return sum(w[n] * float(probas_experts[n]) for n in noms)


def pool_log(probas_experts, poids=None):
    """Pool logarithmique (moyenne géométrique pondérée, normalisée) : p ∝ Π pᵢ^wᵢ vs (1−p) ∝ Π(1−pᵢ)^wᵢ."""
    noms = list(probas_experts)
    if poids is None:
        poids = {n: 1.0 for n in noms}
    w = _norme(poids, noms)
    lp = sum(w[n] * math.log(max(_EPS, float(probas_experts[n]))) for n in noms)
    lq = sum(w[n] * math.log(max(_EPS, 1.0 - float(probas_experts[n]))) for n in noms)
    m = max(lp, lq)
    a, b = math.exp(lp - m), math.exp(lq - m)
    return a / (a + b)


def poids_fiabilite(sorties_experts, issues):
    """Poids ∝ 1/log-loss de chaque expert sur l'historique. `sorties_experts` = dict {expert: liste_de_probas} ;
    `issues` = liste 0/1. Renvoie dict {expert: poids} (normalisé)."""
    from scores_propres import log_loss
    poids = {nm: 1.0 / max(1e-6, log_loss(probas, issues)) for nm, probas in sorties_experts.items()}
    return _norme(poids, list(poids))


def combine(probas_experts, poids=None, methode="lineaire"):
    """Fusionne les opinions {expert: p} par `methode` ∈ {lineaire, log}. Renvoie la probabilité agrégée."""
    return pool_lineaire(probas_experts, poids) if methode == "lineaire" else pool_log(probas_experts, poids)


def formule(p, methode="lineaire") -> str:
    return (f"Avis agrégé (pool {methode}, pondéré par la fiabilité passée des experts) : ~{round(p*100)}% — "
            "une probabilité, pas une certitude.")


if __name__ == "__main__":
    print("=== AGRÉGATION D'OPINIONS D'EXPERTS ===\n")
    avis = {"expert_fiable": 0.8, "expert_moyen": 0.6, "expert_nul": 0.1}
    poids = {"expert_fiable": 0.7, "expert_moyen": 0.25, "expert_nul": 0.05}
    print("  linéaire (pondéré) :", round(pool_lineaire(avis, poids), 3))
    print("  log (pondéré)      :", round(pool_log(avis, poids), 3))
    print("  linéaire (uniforme):", round(pool_lineaire(avis), 3), "(le nul tire vers le bas)")
