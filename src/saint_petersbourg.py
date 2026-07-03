"""
PALIER 2 — PARADOXE DE SAINT-PÉTERSBOURG : l'espérance de gain n'est pas le prix rationnel (brique 91, 2026-06-27).

Un jeu : on lance une pièce jusqu'à « face » au lancer n (probabilité 2⁻ⁿ) ; le gain est 2ⁿ. L'espérance de gain vaut
    E[gain] = Σ 2ⁿ·2⁻ⁿ = Σ 1 = ∞.
Pourtant personne ne paierait plus de quelques euros pour jouer. Évaluer ce jeu par son ESPÉRANCE (∞) est SUR-CONFIANT :
l'infini vient de gains astronomiques de probabilité infime, jamais réalisés.

DEUX RÉSOLUTIONS (calibrées) :
  • UTILITÉ marginale décroissante (Bernoulli, log) : un joueur de fortune W paie le prix p tel que
    E[ln(W − p + gain)] = ln(W). Ce prix est FINI et PETIT (quelques euros), et croît LENTEMENT avec la fortune.
  • BANKROLL FINI : un casino de fortune W ne peut payer que ≤ W, donc l'espérance réelle ≈ log₂(W) — finie, petite.

LE MODE D'ÉCHEC DÉMASQUÉ : utiliser l'espérance de GAIN pour fixer un prix/une décision quand la queue domine est
sur-confiant — la moyenne d'échantillon ne converge même pas (elle CROÎT avec le nombre de parties). Le prix honnête
(utilité bornée / bankroll fini) est petit et fini. ABSTENTION si fortune ≤ 0. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
PRIX = "prix"


def paiement(rng):
    """Une partie : lance jusqu'à 'face' au lancer n, gain 2ⁿ."""
    n = 1
    while rng.random() < 0.5:
        n += 1
    return 2.0 ** n


def esperance_tronquee(n_max):
    """Espérance tronquée à n_max lancers = Σ_{n=1}^{n_max} 2ⁿ·2⁻ⁿ = n_max (croît sans borne)."""
    return float(n_max)


def equivalent_certain_log(W, n_max=60):
    """Prix maximal qu'un joueur de fortune W (utilité ln) accepte : E[ln(W−p+gain)] = ln(W). Bisection."""
    if W <= 0:
        return None
    def e_util(p):
        s = 0.0
        for n in range(1, n_max + 1):
            arg = W - p + 2.0 ** n
            if arg <= 0:
                return -1e300
            s += 2.0 ** (-n) * math.log(arg)
        return s
    cible = math.log(W)
    lo, hi = 0.0, W * 0.999
    for _ in range(200):
        p = (lo + hi) / 2
        if e_util(p) > cible:        # paie encore profitable -> augmenter p
            lo = p
        else:
            hi = p
    return (lo + hi) / 2


def valeur_casino_fini(W):
    """Espérance réelle si le casino ne peut payer que ≤ W (gain plafonné). Finie ≈ log₂(W)."""
    L = int(math.floor(math.log2(W))) if W >= 2 else 0
    val = 0.0
    for n in range(1, L + 1):
        val += 2.0 ** (-n) * 2.0 ** n          # = 1 chacun
    # au-delà de L, le casino paie W (plafonné)
    val += sum(2.0 ** (-n) for n in range(L + 1, L + 200)) * W
    return val


def moyenne_jeux(rng, n_parties):
    """Moyenne empirique de n_parties (croît avec n_parties : pas de convergence)."""
    return sum(paiement(rng) for _ in range(n_parties)) / n_parties


def analyse(W):
    """Façade : (PRIX, {prix_log, valeur_casino, esperance}) ou (ABSTENTION, raison)."""
    if W <= 0:
        return (ABSTENTION, "fortune ≤ 0")
    return (PRIX, {"prix_log": equivalent_certain_log(W), "valeur_casino": valeur_casino_fini(W),
                   "esperance": float("inf")})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de prix : {res[1]}."
    i = res[1]
    return (f"Espérance de gain = ∞, MAIS le prix rationnel est FINI et petit : {i['prix_log']:.2f} (utilité log) / "
            f"{i['valeur_casino']:.2f} (casino à bankroll fini). Payer selon l'espérance serait sur-confiant.")


if __name__ == "__main__":
    import random, statistics
    rng = random.Random(0)
    print("=== PARADOXE DE SAINT-PÉTERSBOURG ===\n")
    print(f"  Espérance tronquée à n_max lancers : n_max=10 → {esperance_tronquee(10)} ; n_max=40 → {esperance_tronquee(40)} (→ ∞)")
    for n in (100, 10000, 1000000):
        m = statistics.median(moyenne_jeux(rng, n) for _ in range(15))
        print(f"  moyenne d'échantillon médiane (n={n:>7}) ≈ {m:.1f} (croît avec n)")
    print()
    for W in (100, 10000, 1000000):
        print(f"  fortune {W:>7} : prix (utilité log) = {equivalent_certain_log(W):.2f} ; casino fini = {valeur_casino_fini(W):.2f}")
    print(" ", formule(analyse(1000)))
