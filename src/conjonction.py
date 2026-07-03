"""
PALIER 2 — SOPHISME DE LA CONJONCTION (problème de Linda) & COHÉRENCE DES JUGEMENTS : juger P(A∧B) > P(A) est
sur-confiant (brique 110, 2026-06-27).

« Linda est employée de banque » (A) vs « Linda est employée de banque ET féministe » (A∧B). La description la rendant
représentative d'une féministe, beaucoup jugent P(A∧B) > P(A). C'est IMPOSSIBLE : un événement conjoint est INCLUS dans
chacun de ses conjoints, donc par MONOTONIE de la mesure de probabilité
    P(A∧B) ≤ P(A)  et  P(A∧B) ≤ P(B),  toujours.
Plus finement, les BORNES DE FRÉCHET encadrent la conjonction cohérente :
    max(0, P(A)+P(B)−1) ≤ P(A∧B) ≤ min(P(A), P(B)).

Un jugement qui viole P(A∧B) ≤ P(A) est INCOHÉRENT — et EXPLOITABLE par un LIVRE HOLLANDAIS : on achète à l'agent le pari
sur (A∧B) à son prix p_AB et on lui vend le pari sur A à son prix p_A ; comme A∧B ⊆ A, l'agent subit une PERTE SÛRE de
(p_AB − p_A) dans TOUS les états du monde.

LA CORRECTION : contraindre tout jugement de conjonction dans les bornes de Fréchet (cohérence). La représentativité
n'est pas une probabilité.

LE MODE D'ÉCHEC DÉMASQUÉ : la « confiance » dans un classement P(A∧B) > P(A) est sur-confiante et perd à coup sûr.
Distinct de copules (72, structure de dépendance continue) et bayes (combinaison de preuves). ABSTENTION si entrées hors
[0,1]. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def bornes_frechet(pA, pB):
    """Encadrement cohérent de P(A∧B) : [max(0, pA+pB−1), min(pA, pB)] (Fréchet-Hoeffding)."""
    return (max(0.0, pA + pB - 1.0), min(pA, pB))


def coherent(pA, pB, pAB, tol=1e-9):
    """Le jugement (pA, pB, pAB) respecte-t-il les bornes de Fréchet ?"""
    lo, hi = bornes_frechet(pA, pB)
    return lo - tol <= pAB <= hi + tol


def sophisme_conjonction(pA, pAB):
    """Vrai si P(A∧B) > P(A) — viol de monotonie (le cœur du sophisme de Linda)."""
    return pAB > pA


def livre_hollandais(pA, pAB):
    """Profit GARANTI du teneur de livre (perte sûre de l'agent) en exploitant un jugement P(A∧B) vs P(A).
    Stratégie : acheter à l'agent le pari (A∧B) à p_AB, lui vendre le pari A à p_A. Comme A∧B ⊆ A, le profit garanti
    (minimum sur tous les états) vaut p_AB − p_A. > 0 ⇒ l'agent perd à coup sûr."""
    # états : A∧B, A∧¬B, ¬A. Flux de trésorerie de l'agent = +p_A (vente A) − p_AB (achat A∧B), puis payoffs.
    cash = pA - pAB
    payoffs = {"A∧B": (1 - 1), "A∧¬B": (0 - 1), "¬A": (0 - 0)}    # reçoit 1 si A∧B, paie 1 si A
    pertes_agent = {e: -(cash + d) for e, d in payoffs.items()}   # perte de l'agent par état
    return min(pertes_agent.values())                              # profit garanti du teneur (min perte agent)


def analyse(pA, pB, pAB):
    """Façade. (ANALYSE, {coherent, bornes, sophisme, profit_livre_hollandais}) ou (ABSTENTION)."""
    if not all(0.0 <= x <= 1.0 for x in (pA, pB, pAB)):
        return (ABSTENTION, "probabilités hors [0,1]")
    lo, hi = bornes_frechet(pA, pB)
    return (ANALYSE, {"coherent": coherent(pA, pB, pAB), "bornes": (lo, hi),
                      "sophisme": sophisme_conjonction(pA, pAB), "pA": pA, "pB": pB, "pAB": pAB,
                      "profit_livre_hollandais": livre_hollandais(pA, pAB)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    lo, hi = i["bornes"]
    if i["sophisme"]:
        return (f"P(A∧B)={i['pAB']:.2f} > P(A)={i['pA']:.2f} : INCOHÉRENT (un conjoint inclut sa conjonction). Bornes de "
                f"Fréchet cohérentes : [{lo:.2f}, {hi:.2f}]. Un livre hollandais extrait un profit sûr de "
                f"{i['profit_livre_hollandais']:.2f} dans tous les états. Juger ainsi par représentativité est sur-confiant.")
    return (f"P(A∧B)={i['pAB']:.2f} ≤ P(A)={i['pA']:.2f} : cohérent (bornes de Fréchet [{lo:.2f}, {hi:.2f}]). Aucun livre "
            f"hollandais possible (profit garanti {i['profit_livre_hollandais']:.2f} ≤ 0).")


if __name__ == "__main__":
    print("=== SOPHISME DE LA CONJONCTION (Linda) ===\n")
    # jugement typique : P(employée de banque)=0.2, P(féministe)=0.7, P(banque ET féministe)=0.4 (> 0.2 !)
    print("  jugement de représentativité :")
    print(" ", formule(analyse(0.2, 0.7, 0.4)))
    print("\n  jugement cohérent :")
    print(" ", formule(analyse(0.2, 0.7, 0.15)))
