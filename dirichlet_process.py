"""
PALIER 2 — PROCESSUS DE DIRICHLET / clustering non-paramétrique : fixer le nombre de classes K est sur-confiant
(brique 95, 2026-06-27).

Choisir K d'avance (k-means, mélange gaussien à K fixé) est SUR-CONFIANT : le modèle FORCE chaque point dans l'une des
K classes — y compris un point d'une classe NOUVELLE, jamais vue — et lui attribue une appartenance quasi certaine, sans
jamais réserver de masse à « ceci est une classe nouvelle ». Si les vraies données ont K+1 groupes, les points du groupe
surnuméraire sont confondus avec confiance dans un mauvais cluster.

LA CORRECTION — PROCESSUS DE DIRICHLET (processus du restaurant chinois, CRP) : un PRIOR sur les partitions qui laisse le
nombre de tables CROÎTRE avec les données. La prédictive CRP d'un nouveau point réserve toujours une masse α/(n+α) à une
TABLE NEUVE :
    P(table existante i) = nᵢ/(n+α) ,   P(nouvelle table) = α/(n+α).
Le nombre attendu de tables croît ~ α·ln(n) (jamais figé). Un mélange DP (Gibbs collapsé, Neal 2000 algo 3) infère donc
une LOI a posteriori sur K au lieu de la fixer, et garde une probabilité de NOUVEAUTÉ honnête pour les points atypiques.

LE MODE D'ÉCHEC DÉMASQUÉ : assigner avec confiance sous un K trop petit est sur-confiant (un point d'un 3ᵉ groupe est
mis à >0.9 dans un mauvais cluster) ; le DP garde de la masse « nouvelle classe » et récupère le vrai K. ABSTENTION si
données insuffisantes. Pur Python (math).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


# ─────────────────────────── Restaurant chinois (CRP) ───────────────────────────
def crp_predictive(tailles, alpha):
    """Prédictive CRP : (poids des tables existantes, poids d'une table NEUVE), normalisés. Réserve α/(n+α) au neuf."""
    n = sum(tailles)
    z = n + alpha
    return [t / z for t in tailles], alpha / z


def esperance_nb_tables(n, alpha):
    """E[nombre de tables] = Σ_{i=0}^{n-1} α/(α+i) ≈ α·ln(1+n/α). Croît avec n (jamais figé)."""
    return sum(alpha / (alpha + i) for i in range(n))


# ─────────────────────────── prédictive gaussienne conjuguée ───────────────────────────
def _pred_gauss(x, n_c, s_c, sigma2, mu0, tau2):
    """Densité prédictive de x pour une classe à n_c membres (somme s_c) ; variance connue σ², prior N(μ0,τ²).
    n_c=0 ⇒ prédictive a priori N(μ0, σ²+τ²) (classe NEUVE)."""
    prec = 1.0 / tau2 + n_c / sigma2
    moy = (mu0 / tau2 + s_c / sigma2) / prec
    var = sigma2 + 1.0 / prec
    return math.exp(-0.5 * (x - moy) ** 2 / var) / math.sqrt(2 * math.pi * var)


# ─────────────────────────── mélange DP : Gibbs collapsé (Neal algo 3) ───────────────────────────
def gibbs_dp(xs, alpha, sigma2, mu0, tau2, iters, rng, trace_k=None, burn=None):
    """Échantillonne les partitions d'un mélange DP gaussien 1D. Renvoie l'assignation finale (liste d'entiers).
    Si trace_k est une liste, y empile le nb de clusters de chaque balayage post-burn-in (burn = balayages ignorés)."""
    n = len(xs)
    if burn is None:
        burn = iters // 2
    z = [0] * n                      # tout le monde à la table 0 au départ
    tailles = {0: n}
    sommes = {0: sum(xs)}
    for it in range(iters):
        for i in range(n):
            c = z[i]
            tailles[c] -= 1; sommes[c] -= xs[i]
            if tailles[c] == 0:
                del tailles[c]; del sommes[c]
            labels = list(tailles.keys())
            poids = [tailles[c] * _pred_gauss(xs[i], tailles[c], sommes[c], sigma2, mu0, tau2) for c in labels]
            neuf = (max(labels) + 1) if labels else 0
            poids.append(alpha * _pred_gauss(xs[i], 0, 0.0, sigma2, mu0, tau2))
            labels.append(neuf)
            tot = sum(poids)
            r = rng.random() * tot
            cum = 0.0
            for c, w in zip(labels, poids):
                cum += w
                if r <= cum:
                    choisi = c
                    break
            else:
                choisi = labels[-1]
            z[i] = choisi
            tailles[choisi] = tailles.get(choisi, 0) + 1
            sommes[choisi] = sommes.get(choisi, 0.0) + xs[i]
        if trace_k is not None and it >= burn:
            trace_k.append(len(tailles))
    return z


def nb_clusters(z):
    return len(set(z))


# ─────────────────────────── K fixé (sur-confiant) ───────────────────────────
def assignation_k_fixe(x, centres, sigma2):
    """Modèle à K FIXÉ : softmax des vraisemblances gaussiennes sur K centres FIXES — aucune masse 'classe neuve'.
    Renvoie (assignation, proba_max)."""
    poids = [math.exp(-0.5 * (x - c) ** 2 / sigma2) for c in centres]
    tot = sum(poids)
    probs = [w / tot for w in poids]
    j = max(range(len(probs)), key=lambda k: probs[k])
    return j, probs[j]


def masse_nouveaute_dp(x, xs, z, alpha, sigma2, mu0, tau2):
    """Sous le DP : probabilité qu'un point x appartienne à une classe NEUVE (masse de nouveauté honnête)."""
    labels = sorted(set(z))
    poids = []
    for c in labels:
        membres = [xs[k] for k in range(len(xs)) if z[k] == c]
        poids.append(len(membres) * _pred_gauss(x, len(membres), sum(membres), sigma2, mu0, tau2))
    poids_neuf = alpha * _pred_gauss(x, 0, 0.0, sigma2, mu0, tau2)
    tot = sum(poids) + poids_neuf
    return poids_neuf / tot


def _mode(valeurs):
    from collections import Counter
    return Counter(valeurs).most_common(1)[0][0]


def analyse(xs, alpha=0.2, sigma2=1.0, mu0=0.0, tau2=25.0, iters=80, rng=None):
    """Façade : infère la loi a posteriori sur K via mélange DP (MODE post-burn-in, résumé bayésien honnête).
    (ANALYSE, {k_estime, k_trace, z, alpha}) ou (ABSTENTION, …)."""
    if rng is None or len(xs) < 6:
        return (ABSTENTION, "données insuffisantes / rng requis")
    trace = []
    z = gibbs_dp(xs, alpha, sigma2, mu0, tau2, iters, rng, trace_k=trace)
    return (ANALYSE, {"k_estime": _mode(trace), "k_trace": trace, "z": z, "alpha": alpha})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    k = res[1]["k_estime"]
    return (f"Le processus de Dirichlet infère K={k} classes (réserve une masse α/(n+α) à une classe NEUVE). Fixer K "
            f"d'avance serait sur-confiant — un point d'un groupe non prévu serait assigné avec certitude à un mauvais "
            f"cluster, sans masse de nouveauté.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    # 3 vrais groupes ; un modèle à K=2 fixé ignorerait le 3ᵉ
    xs = ([rng.gauss(-6, 1) for _ in range(20)] + [rng.gauss(0, 1) for _ in range(20)]
          + [rng.gauss(6, 1) for _ in range(20)])
    print("=== PROCESSUS DE DIRICHLET (clustering non-paramétrique) ===\n")
    st, info = analyse(xs, rng=rng)
    print(" ", formule((st, info)))
    j, p = assignation_k_fixe(15.0, [-6, 0, 6], 1.0)
    print(f"  K=3 fixé : point ATYPIQUE x=15 assigné au cluster {j} avec proba {p:.3f} (sur-confiant !)")
    print(f"  DP : masse 'classe NEUVE' pour x=15 = {masse_nouveaute_dp(15.0, xs, info['z'], 1.0, 1.0, 0.0, 25.0):.3f}")
    print(f"  E[nb tables] (n=60, α=1) = {esperance_nb_tables(60, 1.0):.2f} (croît ~ α·ln n)")
