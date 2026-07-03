"""
PALIER 2 — BIAIS DE SURVIE (survivorship bias) : estimer sur les seuls survivants sur-estime systématiquement
(brique 85, 2026-06-27).

On n'observe souvent que les entités qui ont « survécu » (fonds encore ouverts, entreprises encore là, avions
revenus). Estimer la performance/longévité sur ces SURVIVANTS est SUR-CONFIANT : les échecs ont disparu de
l'échantillon, donc la moyenne observée dépasse la vraie moyenne de la population.
  • E[X | X a survécu (≥ seuil)] > E[X]   (biais positif = sur-optimisme).
  • Pour une loi normale : E[X|X≥τ] = μ + σ·λ(α), α=(τ−μ)/σ, λ = ratio de Mills inverse φ(α)/(1−Φ(α)) > 0.
  • LEÇON DE WALD (avions de la WWII) : les zones touchées sur les avions REVENUS sont les zones SURVIVABLES ; c'est
    là où ils ne sont PAS touchés (les abattus le sont) qu'il faut blinder. La donnée manquante porte le signal.

LE MODE D'ÉCHEC DÉMASQUÉ : prendre la moyenne des survivants pour la vraie moyenne (ou « les traits des entreprises
qui réussissent ») est sur-confiant ; sans modéliser la disparition, l'estimé survivant n'est qu'une BORNE SUPÉRIEURE.
Le biais grandit quand la sélection est forte (seuil élevé). ABSTENTION si population vide / aucun survivant. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
BIAIS = "biais"


def _phi(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _Phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def moyenne(xs):
    return sum(xs) / len(xs)


def survivants(population, seuil):
    """Entités ayant survécu (valeur ≥ seuil)."""
    return [x for x in population if x >= seuil]


def biais(population, seuil):
    """Biais de survie = moyenne(survivants) − moyenne(population) (> 0)."""
    surv = survivants(population, seuil)
    if not surv:
        return None
    return moyenne(surv) - moyenne(population)


def ratio_mills(alpha):
    """Ratio de Mills inverse λ(α) = φ(α)/(1−Φ(α))."""
    d = 1 - _Phi(alpha)
    return _phi(alpha) / d if d > 1e-300 else float("inf")


def moyenne_tronquee_normale(mu, sigma, seuil):
    """E[X | X ≥ seuil] pour X~N(μ,σ²) = μ + σ·λ((seuil−μ)/σ) (la moyenne des survivants en théorie)."""
    return mu + sigma * ratio_mills((seuil - mu) / sigma)


def taux_succes_survivant(population, seuil, bar):
    """Sur-estimation du taux de succès : P(X≥bar | survivant) vs P(X≥bar | population)."""
    surv = survivants(population, seuil)
    p_pop = sum(1 for x in population if x >= bar) / len(population)
    p_surv = sum(1 for x in surv if x >= bar) / len(surv) if surv else 0.0
    return p_surv, p_pop


def analyse(population, seuil):
    """Façade : (BIAIS, {moy_survivants, moy_population, biais, n_survivants, taux_survie}) ou (ABSTENTION, raison)."""
    if not population:
        return (ABSTENTION, "population vide")
    surv = survivants(population, seuil)
    if not surv:
        return (ABSTENTION, "aucun survivant")
    return (BIAIS, {"moy_survivants": moyenne(surv), "moy_population": moyenne(population),
                    "biais": moyenne(surv) - moyenne(population), "n_survivants": len(surv),
                    "taux_survie": len(surv) / len(population)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Moyenne des SURVIVANTS = {i['moy_survivants']:.3f} mais vraie moyenne = {i['moy_population']:.3f} "
            f"(biais +{i['biais']:.3f}, {100*i['taux_survie']:.0f}% de survie). L'estimé survivant est une borne "
            f"SUPÉRIEURE sur-confiante — les échecs disparus la gonflent.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== BIAIS DE SURVIE ===\n")
    pop = [rng.gauss(0.05, 0.2) for _ in range(5000)]   # rendements annuels
    for seuil in (-0.3, -0.05, 0.05):
        info = analyse(pop, seuil)[1]
        print(f"  seuil de survie {seuil:+.2f} : survie {100*info['taux_survie']:>2.0f}% ; "
              f"moy survivants={info['moy_survivants']:.3f} vs vraie {info['moy_population']:.3f} (biais +{info['biais']:.3f})")
    print(f"\n  Théorie (normale μ=0.05,σ=0.2, seuil 0) : E[X|survie]={moyenne_tronquee_normale(0.05,0.2,0):.3f}")
    print(" ", formule(analyse(pop, -0.05)))
