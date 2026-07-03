"""
PALIER 2 — PROCESSUS DE POISSON NON-HOMOGÈNE (intensité variable λ(t), brique 44, 2026-06-26).

« Des événements arrivent à un rythme qui CHANGE dans le temps (appels au centre selon l'heure, pannes selon l'âge,
trafic selon le jour). Combien dans la prochaine fenêtre, avec quelle incertitude HONNÊTE ? » L'erreur classique :
supposer un taux CONSTANT λ̄ = total/durée. Dans une fenêtre CHARGÉE (intensité locale > λ̄), l'intervalle de comptage
bâti sur λ̄ est centré trop bas et trop étroit → il rate les comptages réels → SUR-CONFIANCE.

Le processus de Poisson NON-HOMOGÈNE estime l'intensité LOCALE λ̂(t) (ici par bacs : λ̂_b = comptage_b / largeur_b),
et le comptage d'une fenêtre suit Poisson(∫λ). L'intervalle prédictif = quantiles de Poisson(λ̂_local·durée). INVARIANT
(jugé par calibration.py) : sur un λ(t) connu, l'intervalle NON-HOMOGÈNE couvre le comptage réel ~confiance, là où
l'hypothèse HOMOGÈNE sous-couvre dans les fenêtres chargées. ABSTENTION si trop peu d'événements. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_EVT = 30


def intensite_bins(temps, T: float, n_bins: int):
    """Estime λ̂ par bac régulier sur [0, T]. Renvoie (liste_lambda, largeur) ou None."""
    if T <= 0 or n_bins < 1:
        return None
    w = T / n_bins
    cnt = [0] * n_bins
    for t in temps:
        if 0 <= t < T:
            b = int(t / w)
            if b == n_bins:
                b -= 1
            cnt[b] += 1
    return ([c / w for c in cnt], w)


def _qnegbin(r, p, prob):
    """Plus petit k tel que cdf_NegBin(k) >= prob. NegBin(r, p) : P(N=k)=Γ(k+r)/(Γ(r)k!) p^r (1−p)^k, r réel>0.
    Modélise le PRÉDICTIF Gamma-Poisson (intègre l'incertitude d'estimation du taux)."""
    if r <= 0:
        return 0
    logp = math.log(p)
    log1mp = math.log(1.0 - p) if p < 1.0 else -1e9
    base = r * logp                                  # log P(N=0) = r·log p
    mean = r * (1.0 - p) / p
    kmax = int(mean + 15 * math.sqrt(mean + 1.0) + 30)
    cum = 0.0
    logpk = base
    for k in range(kmax + 1):
        if k > 0:
            # log P(k) = log P(k-1) + log((k-1+r)/k) + log(1-p)
            logpk += math.log((k - 1 + r) / k) + log1mp
        cum += math.exp(logpk)
        if cum >= prob:
            return k
    return kmax


def comptage(temps, a, b):
    c = 0
    for t in temps:
        if a <= t < b:
            c += 1
    return c


def intervalle_comptage(compte_obs, duree_train, duree_pred, confiance: float = 0.90):
    """Intervalle prédictif Gamma-Poisson (NegBin) du comptage d'une fenêtre FUTURE de `duree_pred`, ayant observé
    `compte_obs` événements sur `duree_train` au même régime (prior de Jeffreys 0.5). Renvoie (mean, (bas, haut)).
    La variance INCLUT l'incertitude d'estimation du taux (≈ double celle d'un Poisson plug-in à durées égales)."""
    r = compte_obs + 0.5
    p = duree_train / (duree_train + duree_pred)
    mean = r * (1.0 - p) / p
    a = (1.0 - confiance) / 2.0
    return (mean, (_qnegbin(r, p, a), _qnegbin(r, p, 1.0 - a)))


def predit_fenetre(temps, T, n_bins, a, b, confiance: float = 0.90, homogene: bool = False):
    """Prédit le comptage d'une fenêtre FUTURE équivalente à [a, b]. `homogene=True` -> taux GLOBAL (naïf, observe
    n sur T) ; sinon taux LOCAL (observe le comptage de [a,b] sur sa propre durée). Prédictif Gamma-Poisson dans les
    deux cas — seule la SOURCE du taux diffère. Renvoie (ESTIMATION, (mean, (bas, haut)), confiance) ou ABSTENTION."""
    n = len(temps)
    if n < N_MIN_EVT:
        return (ABSTENTION, None, f"trop peu d'événements (n={n} < {N_MIN_EVT})")
    duree = b - a
    if duree <= 0 or T <= 0:
        return (ABSTENTION, None, "fenêtre vide")
    if homogene:
        res = intervalle_comptage(n, T, duree, confiance)        # taux global sur tout [0,T]
    else:
        c_loc = comptage(temps, a, b)
        res = intervalle_comptage(c_loc, duree, duree, confiance)  # taux local de la fenêtre
    return (ESTIMATION, res, confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas prédire le comptage : {res[2]}."
    m, (bas, haut) = res[1][0], res[1][1]
    conf = res[2]
    return (f"Comptage attendu ≈ {m:.1f} (à {round(conf*100)}% entre {bas} et {haut}). Intensité LOCALE prise en "
            f"compte — supposer un taux constant sous-couvrirait dans les fenêtres chargées.")


if __name__ == "__main__":
    import random
    print("=== PROCESSUS DE POISSON NON-HOMOGÈNE ===\n")
    rng = random.Random(0)
    T, NB = 24.0, 24
    # intensité : calme la nuit, pic en milieu de journée
    def lam_vrai(t):
        return 2.0 + 8.0 * math.exp(-((t - 14.0) ** 2) / 8.0)

    def simule():
        evt = []
        for b in range(NB):
            m = lam_vrai(b + 0.5) * 1.0
            k = 0
            # tirage Poisson par produit d'uniformes
            L = math.exp(-m); p = 1.0
            while True:
                p *= rng.random()
                if p <= L:
                    break
                k += 1
            for _ in range(k):
                evt.append(b + rng.random())
        return evt

    temps = simule()
    print(f"  {len(temps)} événements sur [0,{T}] ; pic vers t=14")
    for (a, b, nom) in [(13, 15, 'fenêtre CHARGÉE'), (1, 3, 'fenêtre calme')]:
        nh = predit_fenetre(temps, T, NB, a, b, 0.90, homogene=False)
        ho = predit_fenetre(temps, T, NB, a, b, 0.90, homogene=True)
        print(f"  {nom} [{a},{b}] : NON-HOMOGÈNE {nh[1]}  |  HOMOGÈNE {ho[1]}")
