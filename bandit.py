"""
PALIER 2 — DÉCISION SÉQUENTIELLE SOUS INCERTITUDE : BANDITS (brique 24, 2026-06-25).

Quand on doit AGIR de façon répétée sans connaître les récompenses (quelle option marche le mieux ?), l'honnêteté =
EXPLORER assez pour apprendre, EXPLOITER ce qu'on sait, sans jamais sur-exploiter une option mal estimée. C'est le
problème du bandit. Deux stratégies fondées sur l'incertitude CALIBRÉE de chaque bras :

  • UCB1 (optimisme calibré) : valeur du bras a = moyenne_a + √(2·ln t / n_a). Le terme d'exploration est une BORNE DE
    CONFIANCE supérieure (Hoeffding) : on choisit le bras dont le MEILLEUR cas plausible est le plus haut. Regret O(√(KT lnT)).
  • Thompson (échantillonnage postérieur) : tire θ_a ~ Beta(1+succès_a, 1+échecs_a), joue l'argmax. Probabilité de
    jouer un bras = probabilité (postérieure) qu'il soit le meilleur — exploration auto-calibrée. Regret O(√(KT)).

INVARIANT : le REGRET (manque à gagner vs le meilleur bras) croît SOUS-LINÉAIREMENT (regret/T → 0) — on converge vers
le bon choix, prouvé par simulation. La borne UCB est un vrai majorant de confiance (jamais sur-confiant sur un bras).
Bernoulli (récompenses 0/1) ; pur Python.
"""
from __future__ import annotations

import math
import random

UCB = "ucb"
THOMPSON = "thompson"


class Bandit:
    """Bandit à K bras (récompenses Bernoulli). `strategie` ∈ {ucb, thompson}. `choisis()` -> indice de bras,
    `observe(bras, recompense)` met à jour. Suit les statistiques pour le regret."""

    __slots__ = ("k", "strategie", "succes", "tirages", "t", "rng", "recompense_totale")

    def __init__(self, k, strategie=UCB, seed=0):
        self.k = k
        self.strategie = strategie
        self.succes = [0.0] * k
        self.tirages = [0] * k
        self.t = 0
        self.rng = random.Random(seed)
        self.recompense_totale = 0.0

    def _moyenne(self, a):
        return self.succes[a] / self.tirages[a] if self.tirages[a] > 0 else 0.0

    def borne_sup(self, a):
        """Borne de confiance supérieure UCB du bras a (moyenne + rayon d'exploration)."""
        if self.tirages[a] == 0:
            return float("inf")
        return self._moyenne(a) + math.sqrt(2.0 * math.log(max(1, self.t)) / self.tirages[a])

    def choisis(self):
        """Indice du bras à jouer selon la stratégie."""
        if self.strategie == UCB:
            for a in range(self.k):
                if self.tirages[a] == 0:
                    return a                      # chaque bras au moins une fois
            return max(range(self.k), key=self.borne_sup)
        # Thompson : Beta(1+succès, 1+échecs)
        meilleurs, best = [], -1.0
        for a in range(self.k):
            s = self.succes[a]
            f = self.tirages[a] - s
            theta = self.rng.betavariate(1.0 + s, 1.0 + f)
            if theta > best:
                best, meilleurs = theta, a
        return meilleurs

    def observe(self, bras, recompense):
        self.tirages[bras] += 1
        self.succes[bras] += float(recompense)
        self.t += 1
        self.recompense_totale += float(recompense)

    def meilleur_estime(self):
        return max(range(self.k), key=self._moyenne)


def simule(moyennes_vraies, T, strategie=UCB, seed=0):
    """Joue T tours sur des bras Bernoulli de moyennes connues. Renvoie (regret_total, fraction_bras_optimal)."""
    rng = random.Random(seed * 7919 + 1)
    b = Bandit(len(moyennes_vraies), strategie, seed)
    opt = max(moyennes_vraies)
    a_opt = moyennes_vraies.index(opt)
    n_opt = 0
    for _ in range(T):
        a = b.choisis()
        r = 1.0 if rng.random() < moyennes_vraies[a] else 0.0
        b.observe(a, r)
        if a == a_opt:
            n_opt += 1
    regret = opt * T - b.recompense_totale
    return regret, n_opt / T


def formule(strategie, regret, T) -> str:
    return (f"Stratégie {strategie} sur {T} décisions : regret moyen {regret/T:.4f} par tour "
            "(décroît vers 0 — j'apprends le bon choix sans sur-exploiter une option mal connue).")


if __name__ == "__main__":
    print("=== BANDITS SOUS INCERTITUDE CALIBRÉE ===\n")
    moyennes = [0.2, 0.5, 0.55, 0.9]
    for strat in (UCB, THOMPSON):
        reg, fopt = simule(moyennes, 5000, strat, seed=1)
        print(" ", formule(strat, reg, 5000), f"| bras optimal joué {fopt:.1%}")
