"""
PALIER 2 — BANDIT ADVERSARIAL (EXP3) : garantir un faible regret SANS supposer un monde stochastique (brique 73,
2026-06-27).

Dans un bandit, à chaque tour on choisit un bras et on n'observe QUE sa récompense. Un algorithme GLOUTON (jouer le
bras empiriquement meilleur) suppose implicitement que les récompenses sont STATIONNAIRES/aléatoires — c'est
SUR-CONFIANT : un environnement ADVERSARIAL (récompenses choisies pour piéger) peut l'enfermer sur un mauvais bras →
regret LINÉAIRE (croît comme T).

EXP3 (poids exponentiels + exploration forcée) ne suppose RIEN sur les récompenses et garantit un regret SOUS-LINÉAIRE
contre N'IMPORTE QUELLE séquence :
    p_i = (1−γ)·w_i/Σw + γ/K       (probabilité de jouer i, avec un plancher d'exploration γ/K)
    x̂_i = x/p_i sur le bras joué    (estimateur sans biais par importance)
    w_i ← w_i·exp(γ·x̂_i/K)
Regret = (meilleur bras FIXE rétrospectif) − (gain de l'algo) ≤ ~2√((e−1)·T·K·ln K). Donc regret/T → 0 (« no-regret »).

LE MODE D'ÉCHEC DÉMASQUÉ : le glouton (s'engager sur le meilleur observé) est EXPLOITABLE → regret linéaire ;
EXP3 garde un plancher d'exploration et reste robuste (regret sous-linéaire) même dans le pire environnement.
ABSTENTION si matrice de récompenses vide / hors [0,1]. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
JOUE = "joue"


def gamma_optimal(T, K):
    """γ = min(1, √(K·ln K / ((e−1)·T))) (réglage standard)."""
    if K < 2 or T < 1:
        return 1.0
    return min(1.0, math.sqrt(K * math.log(K) / ((math.e - 1) * T)))


def exp3(rewards, gamma, rng):
    """Joue EXP3 sur la matrice `rewards` (T×K, ∈[0,1]). Renvoie (gain, pulls, prob_min). N'observe que le bras joué."""
    T, K = len(rewards), len(rewards[0])
    w = [1.0] * K
    gain = 0.0
    pulls = []
    prob_min = 1.0
    for t in range(T):
        sw = sum(w)
        p = [(1 - gamma) * w[i] / sw + gamma / K for i in range(K)]
        prob_min = min(prob_min, min(p))
        r = rng.random(); c = 0.0; arm = K - 1
        for i in range(K):
            c += p[i]
            if r <= c:
                arm = i; break
        x = rewards[t][arm]
        gain += x
        xhat = x / p[arm]
        w[arm] *= math.exp(gamma * xhat / K)
    return gain, pulls, prob_min


def glouton(rewards, rng):
    """Glouton « explore-puis-engage » : joue chaque bras 1 fois, puis TOUJOURS le meilleur observé. Exploitable."""
    T, K = len(rewards), len(rewards[0])
    obs = [0.0] * K
    gain = 0.0
    for i in range(K):
        gain += rewards[i][i % K] if False else rewards[i][i]   # round i : joue bras i
        obs[i] = rewards[i][i]
    best = max(range(K), key=lambda i: obs[i])
    for t in range(K, T):
        gain += rewards[t][best]
    return gain


def meilleur_bras_fixe(rewards):
    """Gain du meilleur bras FIXE rétrospectif (référence du regret)."""
    K = len(rewards[0])
    return max(sum(rewards[t][i] for t in range(len(rewards))) for i in range(K))


def regret(rewards, gain):
    return meilleur_bras_fixe(rewards) - gain


def joue(rewards, rng, gamma=None):
    """Façade : (JOUE, {gain, regret, regret_normalise, borne}) ou (ABSTENTION, raison)."""
    if not rewards or not rewards[0] or any(len(r) != len(rewards[0]) for r in rewards):
        return (ABSTENTION, "matrice vide ou mal formée")
    if any(x < -1e-9 or x > 1 + 1e-9 for row in rewards for x in row):
        return (ABSTENTION, "récompenses hors [0,1]")
    T, K = len(rewards), len(rewards[0])
    g = gamma if gamma is not None else gamma_optimal(T, K)
    gain, _, _ = exp3(rewards, g, rng)
    reg = regret(rewards, gain)
    borne = 2 * math.sqrt((math.e - 1) * T * K * math.log(max(K, 2)))
    return (JOUE, {"gain": gain, "regret": reg, "regret_normalise": reg / T, "borne": borne})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Bandit non joué : {res[1]}."
    info = res[1]
    return (f"EXP3 : regret={info['regret']:.1f} (≤ borne {info['borne']:.0f}), regret/T={info['regret_normalise']:.3f} "
            f"→ 0. Un glouton supposant un monde stochastique serait exploitable (regret linéaire).")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== BANDIT ADVERSARIAL (EXP3) ===\n")
    T, K = 3000, 4
    # adversaire « piège » : bras 0 récompensé au 1er tour (attire le glouton), puis bras 1 domine
    rewards = []
    for t in range(T):
        row = [0.0] * K
        if t < K:
            row[0] = 1.0          # phase d'amorce : seul le bras 0 paie
        else:
            row[1] = 1.0          # ensuite seul le bras 1 paie
        rewards.append(row)
    g = gamma_optimal(T, K)
    gain_e, _, _ = exp3(rewards, g, rng)
    gain_g = glouton(rewards, rng)
    opt = meilleur_bras_fixe(rewards)
    print(f"  meilleur bras fixe = {opt:.0f}")
    print(f"  EXP3   : gain={gain_e:.0f}  regret={opt-gain_e:.0f}  (regret/T={ (opt-gain_e)/T:.3f})")
    print(f"  glouton: gain={gain_g:.0f}  regret={opt-gain_g:.0f}  (regret/T={ (opt-gain_g)/T:.3f}, LINÉAIRE = piégé)")
    print(" ", formule(joue(rewards, rng)))
