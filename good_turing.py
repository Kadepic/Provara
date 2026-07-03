"""
PALIER 2 — GOOD-TURING / MASSE MANQUANTE & ESPÈCES INVISIBLES : assigner 0 à l'inédit est sur-confiant (brique 109, 2026-06-27).

Après avoir observé un échantillon (mots d'une langue, espèces, requêtes…), deux réflexes sont SUR-CONFIANTS :
  • « ce que je n'ai jamais vu a une probabilité 0 » — c'est l'estimateur du maximum de vraisemblance. Sur un nouveau
    tirage inédit, il donne une vraisemblance nulle ⇒ log-loss INFINI : une certitude que l'inobservé est IMPOSSIBLE.
  • « le nombre d'espèces que j'ai vues = le nombre total d'espèces » — sous une distribution à longue traîne (Zipf),
    une foule d'espèces rares restent invisibles ; on SOUS-estime la richesse.

LA CORRECTION — GOOD-TURING (Turing & Good, 1953) : la probabilité que le PROCHAIN tirage soit une espèce INÉDITE vaut
    P₀ ≈ N₁ / N    (N₁ = nombre d'espèces vues exactement une fois, « singletons » ; N = taille de l'échantillon).
La « masse manquante » n'est donc PAS nulle. Pour la richesse totale, l'estimateur de Chao1 corrige vers le haut :
    Ŝ = S_obs + N₁² / (2·N₂).
Le lissage (Good-Turing / Laplace) réserve une probabilité POSITIVE à l'inédit ⇒ log-loss fini, bien calibré.

LE MODE D'ÉCHEC DÉMASQUÉ : la certitude « jamais vu ⇒ impossible » (proba 0) est sur-confiante ; Good-Turing estime la
masse manquante et la richesse cachée. Distinct de loi_puissance (90, exposant de queue) et maximum_entropie (80).
ABSTENTION si échantillon insuffisant. Pur Python, rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def frequences_de_frequences(comptes):
    """N_r = nombre d'espèces observées exactement r fois. comptes : dict espèce→nb d'observations."""
    Nr = {}
    for c in comptes.values():
        Nr[c] = Nr.get(c, 0) + 1
    return Nr


def masse_manquante(comptes):
    """Estimateur de Good-Turing de la probabilité que le prochain tirage soit INÉDIT : P₀ = N₁/N."""
    N = sum(comptes.values())
    N1 = sum(1 for c in comptes.values() if c == 1)
    return N1 / N if N else 0.0


def richesse_chao1(comptes):
    """Estimateur de Chao1 de la richesse totale (espèces vues + cachées) : S_obs + N₁²/(2·N₂)."""
    S_obs = len(comptes)
    N1 = sum(1 for c in comptes.values() if c == 1)
    N2 = sum(1 for c in comptes.values() if c == 2)
    surplus = (N1 * N1) / (2 * N2) if N2 > 0 else N1 * (N1 - 1) / 2
    return S_obs + surplus


def proba_inedit_naive(comptes):
    """Estimateur naïf (MLE) : tout ce qui n'a pas été vu a probabilité 0 (sur-confiant)."""
    return 0.0


def logloss_inedit(comptes, est="good_turing"):
    """Log-loss d'un tirage qui s'avère INÉDIT selon l'estimateur. MLE → +inf ; Good-Turing/Laplace → fini."""
    if est == "naive":
        p0 = proba_inedit_naive(comptes)
    elif est == "laplace":
        V = len(comptes) + 1
        p0 = 1.0 / (sum(comptes.values()) + V)        # masse add-1 réservée à l'inédit
    else:
        p0 = masse_manquante(comptes)
    return float("inf") if p0 <= 0 else -math.log(p0)


def analyse(comptes):
    """Façade. (ANALYSE, {masse_manquante, richesse_chao1, especes_vues, logloss_naif, logloss_gt}) ou (ABSTENTION)."""
    N = sum(comptes.values())
    if N < 50 or len(comptes) < 5:
        return (ABSTENTION, "échantillon insuffisant")
    return (ANALYSE, {"masse_manquante": masse_manquante(comptes), "richesse_chao1": richesse_chao1(comptes),
                      "especes_vues": len(comptes), "N": N,
                      "logloss_naif": logloss_inedit(comptes, "naive"),
                      "logloss_gt": logloss_inedit(comptes, "good_turing")})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"{i['especes_vues']} espèces vues sur N={i['N']} tirages. P(prochain inédit) ≈ {i['masse_manquante']:.3f} "
            f"(Good-Turing), PAS 0 : richesse estimée ≈ {i['richesse_chao1']:.0f} (Chao1, > {i['especes_vues']} vues). "
            f"Le log-loss du « jamais vu ⇒ proba 0 » est {i['logloss_naif']} ; Good-Turing {i['logloss_gt']:.2f}. "
            f"Assigner 0 à l'inédit est sur-confiant.")


# ───────── échantillonneur Zipf pour démo/tests ─────────
def echantillon_zipf(S, s, N, rng):
    poids = [1.0 / (r ** s) for r in range(1, S + 1)]
    Z = sum(poids)
    probs = [w / Z for w in poids]
    cum = []
    c = 0.0
    for p in probs:
        c += p
        cum.append(c)
    import bisect
    comptes = {}
    for _ in range(N):
        k = bisect.bisect_left(cum, rng.random())
        comptes[k] = comptes.get(k, 0) + 1
    return comptes, probs


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    comptes, probs = echantillon_zipf(5000, 1.1, 2000, rng)
    st, info = analyse(comptes)
    print("=== GOOD-TURING / MASSE MANQUANTE (Zipf) ===\n")
    print(" ", formule((st, info)))
    vraie = sum(probs[k] for k in range(len(probs)) if k not in comptes)
    print(f"\n  masse manquante VRAIE (simulation) = {vraie:.3f} ; Good-Turing = {info['masse_manquante']:.3f}")
