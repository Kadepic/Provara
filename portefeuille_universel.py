"""
PALIER 2 — PORTEFEUILLE UNIVERSEL (Cover 1991) : « miser sur le meilleur actif a posteriori » est sur-confiant
(brique 96, 2026-06-27).

Choisir l'allocation rétrospectivement optimale — tout sur l'actif qui s'est avéré le meilleur, ou une répartition fixe
« évidente » — est SUR-CONFIANT : on ne connaît PAS d'avance quel actif (ou quel mélange) gagnera. Un pari concentré n'a
aucune garantie dans le pire cas ; une mauvaise séquence le ruine.

LA CORRECTION — PORTEFEUILLE UNIVERSEL : un mélange bayésien sur TOUS les portefeuilles à rééquilibrage constant (CRP),
b_{t+1} = ∫ b·Sₜ(b) db / ∫ Sₜ(b) db où Sₜ(b) = richesse cumulée du CRP b. Sa richesse = MOYENNE des richesses de tous les
CRP. Théorème de Cover : pour m actifs, W_univ ≥ W_meilleur-CRP / (n+1)^{m−1}, donc le REGRET LOGARITHMIQUE par période
→ 0 — il traque le meilleur portceuille constant SANS modèle des rendements ni connaissance du futur.

Le « pumping de volatilité » : avec un actif stable (×1) et un actif oscillant (×2 / ×0.5), CHAQUE actif pur stagne, mais
le CRP 50/50 rééquilibré CROÎT exponentiellement — et le portefeuille universel capte cette croissance.

LE MODE D'ÉCHEC DÉMASQUÉ : s'engager sur un seul actif/une allocation fixe est sur-confiant (aucune garantie pire-cas) ;
le portefeuille universel a un regret borné prouvé. ABSTENTION si données insuffisantes. Pur Python (math).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _rendement(b, x):
    """Rendement brut d'une période : produit scalaire <b, x> (b = poids, x = relatifs de prix)."""
    return sum(bi * xi for bi, xi in zip(b, x))


def richesse_crp(b, relatifs):
    """Richesse finale d'un portefeuille à rééquilibrage CONSTANT b (rebalancé chaque période) sur la séquence."""
    w = 1.0
    for x in relatifs:
        w *= _rendement(b, x)
    return w


def richesse_actif_pur(j, relatifs):
    """Richesse finale en plaçant tout sur l'actif j (acheter-et-garder = rééquilibrage trivial du sommet du simplexe)."""
    w = 1.0
    for x in relatifs:
        w *= x[j]
    return w


def _grille_simplexe(m, pas):
    """Grille du simplexe à m actifs (poids ≥ 0, somme 1), résolution 1/pas. m=2 → [(i/pas, 1−i/pas)]."""
    if m == 2:
        return [(i / pas, 1 - i / pas) for i in range(pas + 1)]
    if m == 3:
        pts = []
        for i in range(pas + 1):
            for j in range(pas + 1 - i):
                pts.append((i / pas, j / pas, (pas - i - j) / pas))
        return pts
    raise ValueError("m ∈ {2,3}")


def richesse_universelle(relatifs, m=None, pas=200):
    """Richesse du portefeuille universel de Cover = MOYENNE des richesses CRP sur une grille uniforme du simplexe."""
    if m is None:
        m = len(relatifs[0])
    grille = _grille_simplexe(m, pas)
    ws = [richesse_crp(b, relatifs) for b in grille]
    return sum(ws) / len(ws)


def meilleur_crp(relatifs, m=None, pas=200):
    """(richesse, b) du meilleur portefeuille à rééquilibrage constant A POSTERIORI (oracle, inconnu d'avance)."""
    if m is None:
        m = len(relatifs[0])
    grille = _grille_simplexe(m, pas)
    best_b = max(grille, key=lambda b: richesse_crp(b, relatifs))
    return richesse_crp(best_b, relatifs), best_b


def poids_universels_suivants(relatifs, m=None, pas=200):
    """Allocation jouée à la période suivante : moyenne des b pondérée par la richesse CRP cumulée (Cover)."""
    if m is None:
        m = len(relatifs[0]) if relatifs else 2
    grille = _grille_simplexe(m, pas)
    ws = [richesse_crp(b, relatifs) for b in grille] if relatifs else [1.0] * len(grille)
    tot = sum(ws)
    return [sum(b[k] * w for b, w in zip(grille, ws)) / tot for k in range(m)]


def regret_log(relatifs, m=None, pas=200):
    """Regret logarithmique = ln(W_meilleur-CRP) − ln(W_univ). Borné par (m−1)·ln(n+1) (Cover)."""
    w_best, _ = meilleur_crp(relatifs, m, pas)
    w_uni = richesse_universelle(relatifs, m, pas)
    return math.log(w_best) - math.log(w_uni)


def analyse(relatifs, pas=200):
    """Façade. (ANALYSE, {w_univ, w_best, b_best, regret, regret_par_periode, n}) ou (ABSTENTION, raison)."""
    if not relatifs or len(relatifs) < 2 or any(len(x) != len(relatifs[0]) for x in relatifs):
        return (ABSTENTION, "séquence trop courte / dimensions incohérentes")
    if any(any(xi <= 0 for xi in x) for x in relatifs):
        return (ABSTENTION, "relatifs de prix ≤ 0")
    m = len(relatifs[0])
    w_uni = richesse_universelle(relatifs, m, pas)
    w_best, b_best = meilleur_crp(relatifs, m, pas)
    reg = math.log(w_best) - math.log(w_uni)
    n = len(relatifs)
    return (ANALYSE, {"w_univ": w_uni, "w_best": w_best, "b_best": b_best,
                      "regret": reg, "regret_par_periode": reg / n, "n": n})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Portefeuille universel : richesse {i['w_univ']:.3f} vs meilleur CRP a posteriori {i['w_best']:.3f} "
            f"(b*≈{tuple(round(x,2) for x in i['b_best'])}). Regret log {i['regret']:.3f} ≤ (m−1)·ln(n+1) ; par période "
            f"{i['regret_par_periode']:.4f} → 0. Miser sur le meilleur actif a posteriori serait sur-confiant — inconnu "
            f"d'avance, sans garantie pire-cas.")


if __name__ == "__main__":
    # pumping de volatilité : actif stable (×1) + actif oscillant (×2 / ×0.5)
    relatifs = [(1.0, 2.0) if t % 2 == 0 else (1.0, 0.5) for t in range(40)]
    print("=== PORTEFEUILLE UNIVERSEL (Cover) — pumping de volatilité ===\n")
    print(f"  actif pur 'stable' : richesse {richesse_actif_pur(0, relatifs):.3f}")
    print(f"  actif pur 'oscillant' : richesse {richesse_actif_pur(1, relatifs):.3f}")
    st, info = analyse(relatifs)
    print(" ", formule((st, info)))
