"""
PALIER 2 — ERGODICITÉ : la moyenne d'ENSEMBLE n'est pas la moyenne dans le TEMPS (brique 93, 2026-06-27).

Pour un processus, la moyenne d'ENSEMBLE (espérance sur de nombreuses copies parallèles, E[X]) et la moyenne dans le
TEMPS (ce qu'UNE trajectoire vit sur la durée) coïncident SEULEMENT si le processus est ERGODIQUE. Les processus
ADDITIFS le sont ; les processus MULTIPLICATIFS (richesse, croissance, paris répétés) NE le sont PAS.

Exemple : à chaque pas, la richesse est multipliée par 1.5 (p=½) ou 0.6 (p=½).
  • moyenne d'ensemble par pas = ½·1.5 + ½·0.6 = 1.05  → E[richesse] CROÎT (1.05ᵀ).
  • taux de croissance dans le TEMPS = exp(½·ln1.5 + ½·ln0.6) = √0.9 ≈ 0.949  → une trajectoire DÉCROÎT vers 0.
La moyenne d'ensemble (>1) est portée par de rares trajectoires chanceuses ; l'individu TYPIQUE est ruiné.

LE MODE D'ÉCHEC DÉMASQUÉ : décider selon l'ESPÉRANCE E[X] (moyenne d'ensemble) pour quelqu'un qui vit UNE trajectoire
dans le temps est SUR-CONFIANT quand le processus est non-ergodique — il faut le taux de croissance TEMPOREL
(géométrique/log). ABSTENTION si facteurs/probas invalides. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ERGO = "ergodicite"


def moyenne_ensemble(facteurs, probas):
    """Moyenne d'ensemble du multiplicateur par pas = Σ pᵢ·fᵢ (arithmétique)."""
    return sum(p * f for p, f in zip(probas, facteurs))


def taux_croissance_temporel(facteurs, probas):
    """Taux de croissance dans le temps (par pas) = exp(Σ pᵢ·ln fᵢ) (géométrique). < ensemble si volatil (Jensen)."""
    return math.exp(sum(p * math.log(f) for p, f in zip(probas, facteurs)))


def trajectoire_multiplicative(rng, facteurs, probas, T, w0=1.0):
    """Simule UNE trajectoire de richesse multiplicative sur T pas."""
    w = w0
    for _ in range(T):
        u = rng.random(); c = 0.0
        for p, f in zip(probas, facteurs):
            c += p
            if u <= c:
                w *= f; break
    return w


def trajectoire_additive(rng, increments, probas, T, x0=0.0):
    """Simule UNE trajectoire ADDITIVE (ergodique) : x += increment tiré."""
    x = x0
    for _ in range(T):
        u = rng.random(); c = 0.0
        for p, d in zip(probas, increments):
            c += p
            if u <= c:
                x += d; break
    return x


def analyse(facteurs, probas):
    """Façade : compare moyenne d'ensemble et taux temporel d'un processus multiplicatif. (ERGO, infos) ou ABSTENTION."""
    if not facteurs or len(facteurs) != len(probas) or any(f <= 0 for f in facteurs) or abs(sum(probas) - 1) > 1e-9:
        return (ABSTENTION, "facteurs ≤ 0, probas non normalisées ou tailles différentes")
    me = moyenne_ensemble(facteurs, probas)
    tt = taux_croissance_temporel(facteurs, probas)
    return (ERGO, {"moyenne_ensemble": me, "taux_temporel": tt, "ensemble_croit": me > 1, "temps_croit": tt > 1,
                   "non_ergodique": abs(me - tt) > 1e-9})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if i["ensemble_croit"] and not i["temps_croit"]:
        return (f"⚠ NON-ERGODIQUE : moyenne d'ensemble {i['moyenne_ensemble']:.3f} (>1, E[X] CROÎT) mais taux TEMPOREL "
                f"{i['taux_temporel']:.3f} (<1, une trajectoire DÉCROÎT vers 0). Décider sur l'espérance serait sur-confiant.")
    return f"Moyenne d'ensemble {i['moyenne_ensemble']:.3f} ; taux temporel {i['taux_temporel']:.3f} (géométrique ≤ arithmétique)."


if __name__ == "__main__":
    import random, statistics
    rng = random.Random(0)
    fac, pr = [1.5, 0.6], [0.5, 0.5]
    print("=== ERGODICITÉ ===\n")
    print(f"  multiplicateur : moyenne d'ensemble={moyenne_ensemble(fac,pr):.3f} ; taux temporel={taux_croissance_temporel(fac,pr):.4f}")
    finals = [trajectoire_multiplicative(rng, fac, pr, 100) for _ in range(5000)]
    print(f"  après 100 pas (5000 trajectoires) : moyenne={statistics.mean(finals):.2e} (croît) ; médiane={statistics.median(finals):.2e} (ruine)")
    print(" ", formule(analyse(fac, pr)))
