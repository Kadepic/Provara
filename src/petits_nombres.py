"""
PALIER 2 — LOI DES PETITS NOMBRES & classement par taux brut : les extrêmes sont du bruit de petit échantillon
(brique 94, 2026-06-27).

Classer des entités (comtés, hôpitaux, écoles, joueurs) par leur TAUX BRUT (succès/essais) est SUR-CONFIANT quand les
tailles d'échantillon diffèrent : la variance d'un taux est ∝ 1/n, donc les entités à PETIT n ont les taux les plus
EXTRÊMES — en haut ET en bas du classement — même si leur taux VRAI est ordinaire. (« Les comtés au plus fort et au
plus faible taux de cancer sont les plus PETITS. ») Conclure « le meilleur/le pire » d'un taux brut, c'est confondre le
hasard avec le signal.

LA CORRECTION — RÉTRÉCISSEMENT empirique-bayésien : on tire chaque taux vers la moyenne globale μ, d'autant plus que n
est petit :  r̂ᵢ = (kᵢ + κ·μ)/(nᵢ + κ),  κ = force du prior estimée par MAXIMUM DE VRAISEMBLANCE MARGINALE
(Beta-Binomial). Si la variation observée est tout bruit (taux vrais ≈ égaux), κ → ∞ : rétrécissement total, les
extrêmes disparaissent.

LE MODE D'ÉCHEC DÉMASQUÉ : ranger/récompenser/punir sur des taux bruts à n inégaux est sur-confiant ; le rétrécissement
EB donne des estimés honnêtes (et réduit l'erreur). ABSTENTION si données insuffisantes. Pur Python (lgamma).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def taux_brut(k, n):
    return k / n if n > 0 else 0.0


def moyenne_globale(ks, ns):
    """Taux global poolé μ = Σk/Σn."""
    return sum(ks) / sum(ns)


def _lnB(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _ll_marginale(ks, ns, mu, kappa):
    """Log-vraisemblance marginale Beta-Binomiale (prior Beta(κμ, κ(1−μ)))."""
    a, b = kappa * mu, kappa * (1 - mu)
    s = 0.0
    for k, n in zip(ks, ns):
        s += _lnB(k + a, n - k + b) - _lnB(a, b)      # (le coef binomial est constant en κ)
    return s


def kappa_optimal(ks, ns, mu, grille=None):
    """Force du prior κ maximisant la vraisemblance marginale (EB). κ grand = variation = bruit ⇒ fort rétrécissement."""
    if grille is None:
        grille = [0.1, 0.5, 1, 2, 5, 10, 30, 100, 300, 1000, 1e4, 1e5]
    return max(grille, key=lambda kap: _ll_marginale(ks, ns, mu, kap))


def retrecissement(k, n, mu, kappa):
    """Estimé EB rétréci : (k + κμ)/(n + κ). Tire vers μ, d'autant plus que n est petit."""
    return (k + kappa * mu) / (n + kappa)


def analyse(ks, ns):
    """Façade : taux bruts vs rétrécis EB. (ANALYSE, {mu, kappa, bruts, retrecis}) ou (ABSTENTION, raison)."""
    if len(ks) < 5 or len(ks) != len(ns) or any(n <= 0 for n in ns):
        return (ABSTENTION, "données insuffisantes / n ≤ 0")
    mu = moyenne_globale(ks, ns)
    kap = kappa_optimal(ks, ns, mu)
    bruts = [taux_brut(k, n) for k, n in zip(ks, ns)]
    retr = [retrecissement(k, n, mu, kap) for k, n in zip(ks, ns)]
    return (ANALYSE, {"mu": mu, "kappa": kap, "bruts": bruts, "retrecis": retr})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    imax = max(range(len(i["bruts"])), key=lambda j: i["bruts"][j])
    return (f"Le « top » par taux BRUT (entité {imax}, {i['bruts'][imax]:.3f}) est rétréci à {i['retrecis'][imax]:.3f} "
            f"(μ={i['mu']:.3f}, κ={i['kappa']:g}). Classer sur des taux bruts à n inégaux serait sur-confiant — les "
            f"extrêmes sont du bruit de petit échantillon.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    p = 0.05
    # entités à VRAI taux identique mais tailles très variables
    ns = [rng.choice([20, 50, 100, 500, 2000, 10000]) for _ in range(200)]
    ks = [sum(1 for _ in range(n) if rng.random() < p) for n in ns]
    print("=== LOI DES PETITS NOMBRES (classement par taux brut) ===\n")
    bruts = [taux_brut(k, n) for k, n in zip(ks, ns)]
    top = sorted(range(len(ns)), key=lambda i: bruts[i], reverse=True)[:5]
    print(f"  vrai taux = {p} pour tous. Top 5 par taux BRUT : tailles n = {[ns[i] for i in top]} (petits !)")
    print(f"  taux bruts du top 5 : {[round(bruts[i],3) for i in top]}")
    print(" ", formule(analyse(ks, ns)))
