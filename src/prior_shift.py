"""
PALIER 2 — CORRECTION DE CHANGEMENT DE PRIOR / LABEL SHIFT (Saerens-Latinne-Decaestecker) (brique, 2026-06-26).

« Un classifieur calibré sur des données ÉQUILIBRÉES est déployé sur une population où la PRÉVALENCE a changé (maladie
rare, fraude rare…). » Réutiliser tel quel ses probabilités est une SUR-CONFIANCE : sous P(y) plus faible, un « 70 % de
chances que ce soit positif » s'avère bien moins souvent vrai — la calibration casse côté classe devenue rare, parce que
le classifieur garde le prior d'ENTRAÎNEMENT.

Sous l'hypothèse LABEL SHIFT (P(x|y) inchangé, seul P(y) bouge), la correction est exacte : p_cible(y|x) ∝ p_train(y|x)·
(π_cible(y)/π_train(y)), renormalisé. Et π_cible s'estime SANS étiquettes par EM (Saerens) sur les prédictions cibles.
INVARIANT (jugé par calibration.py) : après correction, les probabilités sont CALIBRÉES sur la population cible ; sans
correction elles sont sur-confiantes (sur la classe raréfiée). Si les priors sont égaux, la correction est l'identité
(aucun prix). ABSTENTION si trop peu de données cibles pour l'EM. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 30


def _normalise(v):
    s = sum(v)
    return [x / s for x in v] if s > 0 else [1.0 / len(v)] * len(v)


def corrige_posterior(p_train, prior_train, prior_cible):
    """Corrige une distribution posterior p_train (sur K classes) du train vers la cible. Renvoie la distribution
    corrigée (renormalisée)."""
    ratio = [p_train[k] * (prior_cible[k] / prior_train[k]) for k in range(len(p_train))]
    return _normalise(ratio)


def estime_prior_cible(posteriors_cible, prior_train, n_iter: int = 200, tol: float = 1e-7):
    """EM de Saerens : estime π_cible à partir des posteriors p_train(y|x) sur des données cibles NON étiquetées.
    `posteriors_cible` = liste de distributions (K classes). Renvoie π_cible ou None."""
    if not posteriors_cible:
        return None
    K = len(posteriors_cible[0])
    pi = list(prior_train)
    for _ in range(n_iter):
        # E : posterior cible courant pour chaque point ; M : moyenne = nouveau prior
        nouveau = [0.0] * K
        for p in posteriors_cible:
            corr = corrige_posterior(p, prior_train, pi)
            for k in range(K):
                nouveau[k] += corr[k]
        nouveau = [x / len(posteriors_cible) for x in nouveau]
        if max(abs(nouveau[k] - pi[k]) for k in range(K)) < tol:
            pi = nouveau
            break
        pi = nouveau
    return pi


def adapte(posteriors_cible, prior_train, prior_cible=None):
    """Façade : adapte tous les posteriors cibles. Si `prior_cible` est None, il est estimé par EM. Renvoie
    (ESTIMATION, {prior_cible, posteriors}, None) ou (ABSTENTION, None, raison)."""
    n = len(posteriors_cible)
    if prior_cible is None and n < N_MIN:
        return (ABSTENTION, None, f"trop peu de données cibles pour l'EM (n={n} < {N_MIN})")
    pc = prior_cible if prior_cible is not None else estime_prior_cible(posteriors_cible, prior_train)
    corr = [corrige_posterior(p, prior_train, pc) for p in posteriors_cible]
    return (ESTIMATION, {"prior_cible": pc, "posteriors": corr}, None)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas corriger le changement de prévalence : {res[2]}."
    pc = res[1]["prior_cible"]
    return (f"Probabilités recalibrées pour la prévalence cible estimée {[round(x, 3) for x in pc]} : sans cette "
            f"correction de label shift, le classifieur resterait sur-confiant sur la classe devenue rare.")


if __name__ == "__main__":
    import math
    import random
    rng = random.Random(0)
    # classifieur calibré au prior d'entraînement 0.5 ; cible = positif RARE (0.1)
    pi_tr = [0.5, 0.5]
    def p_train_de_score(s):
        L = math.exp(-((s - 1.5) ** 2) / 2) / math.exp(-(s ** 2) / 2)   # vraisemblance positif/négatif
        p1 = pi_tr[1] * L / (pi_tr[1] * L + pi_tr[0])
        return [1 - p1, p1]
    posts = []
    for _ in range(2000):
        y = 1 if rng.random() < 0.1 else 0                  # vraie cible (prévalence 0.1)
        s = rng.gauss(1.5 if y else 0.0, 1.0)
        posts.append(p_train_de_score(s))
    pi_est = estime_prior_cible(posts, pi_tr)
    print("=== CORRECTION DE PRIOR (label shift) — EM de Saerens ===\n")
    print(f"  π_cible estimé (EM, sans étiquettes) = {[round(x,3) for x in pi_est]} (vrai [0.9, 0.1])")
    p = p_train_de_score(1.2)
    print(f"  point s=1.2 : p_train(positif)={p[1]:.3f} -> corrigé={corrige_posterior(p, pi_tr, pi_est)[1]:.3f} (plus prudent)")
    print(" ", formule(adapte(posts, pi_tr)))
