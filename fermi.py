"""
PALIER 2 — ESTIMATION D'ORDRE DE GRANDEUR (FERMI) AVEC INCERTITUDE (brique 29, 2026-06-25).

Beaucoup de quantités non-bornées ne se MESURENT pas directement (« combien d'accordeurs de piano dans une ville ? »,
« combien de cellules dans un corps ? ») mais s'ESTIMENT en les décomposant en un PRODUIT de facteurs, chacun connu à
un ORDRE DE GRANDEUR près. L'honnêteté = porter l'incertitude de chaque facteur jusqu'au résultat.

Chaque facteur i est donné par un intervalle (bas, haut) > 0 = son intervalle de confiance à `confiance`. On le modélise
LOG-NORMAL (l'incertitude multiplicative est ~symétrique en échelle log) :
    μ_i = (ln bas + ln haut)/2     σ_i = (ln haut − ln bas) / (2·z)        (z = quantile de `confiance`)
Les logs s'ADDITIONNENT (facteurs indépendants) -> résultat log-normal : μ = Σμ_i, σ = √Σσ_i². D'où :
    estimation (moyenne géométrique) = exp(μ) ;   intervalle = exp(μ ± z·σ).

INVARIANT (jugé par calibration.py) : si chaque facteur est un intervalle `confiance` HONNÊTE et que les facteurs sont
indépendants, l'intervalle du produit couvre la vraie valeur ~`confiance` (prouvé Monte-Carlo). ABSTENTION si un
facteur est invalide (bas ≤ 0 ou bas > haut). Variante Monte-Carlo fournie (loi des facteurs quelconque).
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
_Z = {0.50: 0.6745, 0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}


def estime_fermi(facteurs, confiance=0.90, conf_facteurs=None):
    """Combine des facteurs multiplicatifs incertains (liste de (bas, haut) > 0). `conf_facteurs` = niveau auquel les
    intervalles d'ENTRÉE sont donnés (défaut = `confiance`) ; `confiance` = niveau de l'intervalle de SORTIE. Séparer
    les deux rend la sortie MONOTONE (plus de confiance demandée -> intervalle plus large). Renvoie (ESTIMATION,
    (point, (bas, haut)), confiance) — log-normal analytique — ou ABSTENTION si facteur invalide."""
    cf = confiance if conf_facteurs is None else conf_facteurs
    zf = _Z.get(round(cf, 2), 1.6449)            # niveau des facteurs d'entrée
    zo = _Z.get(round(confiance, 2), 1.6449)     # niveau de la sortie
    mu, var = 0.0, 0.0
    for (b, h) in facteurs:
        b, h = float(b), float(h)
        if b <= 0 or h <= 0 or b > h:
            return (ABSTENTION, None, f"facteur invalide ({b}, {h}) : exige 0 < bas ≤ haut")
        mu += (math.log(b) + math.log(h)) / 2.0
        sig = (math.log(h) - math.log(b)) / (2.0 * zf)
        var += sig * sig
    s = math.sqrt(var)
    return (ESTIMATION, (math.exp(mu), (math.exp(mu - zo * s), math.exp(mu + zo * s))), confiance)


def estime_fermi_mc(tirages_facteurs, confiance=0.90, n=20000, seed=0):
    """Variante MONTE-CARLO : `tirages_facteurs` = liste de fonctions rng -> valeur (>0) d'un facteur (loi quelconque).
    Renvoie (ESTIMATION, (point, (bas, haut)), confiance). Le point est la médiane (robuste pour du multiplicatif)."""
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        p = 1.0
        for tir in tirages_facteurs:
            p *= float(tir(rng))
        vals.append(p)
    vals.sort()
    a = (1.0 - confiance) / 2.0

    def q(pp):
        i = pp * (n - 1)
        lo = int(i)
        return vals[lo] if lo + 1 >= n else vals[lo] * (1 - (i - lo)) + vals[lo + 1] * (i - lo)

    return (ESTIMATION, (q(0.5), (q(a), q(1.0 - a))), confiance)


def _ordre(x):
    return f"{x:.3g}"


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer : {res[2]}."
    point, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Estimation d'ordre de grandeur : ~{_ordre(point)} (à {round(conf*100)}% entre {_ordre(bas)} et "
            f"{_ordre(haut)}). C'est un ordre de grandeur raisonné, pas une mesure.")


if __name__ == "__main__":
    print("=== ESTIMATION DE FERMI ===\n")
    # accordeurs de piano à Paris : population × pianos/hab × accords/an / (accords/an/accordeur)
    facteurs = [(2e6, 2.5e6),      # habitants
                (0.02, 0.05),      # pianos par habitant (foyers + institutions)
                (0.8, 1.2),        # accords par piano par an
                (1 / 1500, 1 / 800)]  # accordeurs par accord/an (1 accordeur ≈ 800–1500 accords/an)
    print(" ", formule(estime_fermi(facteurs, 0.90)))
    print(" ", formule(estime_fermi([(1, 10), (10, 100)], 0.90)))
