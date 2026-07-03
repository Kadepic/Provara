"""
PALIER 2 — E-PROCESS / TEST PAR PARI (e-values, Ville) : tester une hypothèse en pouvant s'arrêter N'IMPORTE QUAND
sans gonfler l'erreur (brique 69, 2026-06-27).

Une e-VALUE pour une hypothèse nulle H0 est une variable aléatoire E ≥ 0 avec E_{H0}[E] ≤ 1 : c'est le gain d'un PARI
équitable-sous-H0. Un e-PROCESS (Eₜ)ₜ est une martingale (ou sur-martingale) de richesse sous H0, partant de 1. Par
l'inégalité de VILLE :
    P_{H0}( ∃t : Eₜ ≥ 1/α ) ≤ α.
On peut donc REJETER H0 dès que la richesse Eₜ ≥ 1/α, à un instant QUELCONQUE (même choisi après avoir vu les
données), avec erreur de type I garantie ≤ α. Le p-value anytime-valid est pₜ = 1 / maxₛ≤ₜ Eₛ.

LE MODE D'ÉCHEC DÉMASQUÉ : le p-value CLASSIQUE à n fixe, si on REGARDE en continu et qu'on s'arrête au premier
« significatif » (peeking / optional stopping), a une erreur de type I qui EXPLOSE (≫ α) — sur-confiance dans le rejet.
L'e-process contrôle l'erreur SOUS arrêt optionnel. Bonus : les e-values se MULTIPLIENT (combiner des expériences
indépendantes) et une e-value de MÉLANGE reste valide sans connaître l'effet. ABSTENTION si paramètres invalides.
Pur Python (test d'une proportion : H0 p=p0 vs p>p0).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
TEST = "test"


def e_process_simple(xs, p0, p1):
    """E-process du rapport de vraisemblance pour H0:p=p0 vs alternative p1 : Eₜ = Π (p1/p0)^x ((1−p1)/(1−p0))^{1−x}.
    Martingale sous H0 (E=1). Renvoie la suite (Eₜ)."""
    r1, r0 = p1 / p0, (1 - p1) / (1 - p0)
    E = 1.0
    out = []
    for x in xs:
        E *= r1 if x else r0
        out.append(E)
    return out


def e_process_melange(xs, p0, grille_p1):
    """E-process de MÉLANGE (moyenne sur une grille d'alternatives) : robuste à un effet inconnu. Reste une martingale
    sous H0. Eₜ = moyenne sur p1 des e-process simples."""
    r = [(p1 / p0, (1 - p1) / (1 - p0)) for p1 in grille_p1]
    wealth = [1.0] * len(grille_p1)
    out = []
    for x in xs:
        for i, (r1, r0) in enumerate(r):
            wealth[i] *= r1 if x else r0
        out.append(sum(wealth) / len(wealth))
    return out


def seuil(alpha):
    """Seuil de rejet de Ville : 1/α."""
    return 1.0 / alpha


def p_anytime(e_values):
    """p-value anytime-valid pₜ = 1 / maxₛ≤ₜ Eₛ (running max)."""
    out, mx = [], 0.0
    for E in e_values:
        mx = max(mx, E)
        out.append(1.0 / mx if mx > 0 else 1.0)
    return out


def test_sequentiel(xs, p0, alpha=0.05, grille_p1=None):
    """Teste H0:p=p0 en s'arrêtant dès que Eₜ ≥ 1/α (martingale de mélange). Renvoie (TEST, {rejet, E_final, seuil})
    ou (ABSTENTION, raison). rejet = instant de rejet (1-indexé) ou None."""
    if not xs or not (0 < p0 < 1) or not (0 < alpha < 1):
        return (ABSTENTION, "données vides / p0∉(0,1) / α∉(0,1)")
    if grille_p1 is None:
        grille_p1 = [p0 + (1 - p0) * k / 10 for k in range(1, 10)]
    es = e_process_melange(xs, p0, grille_p1)
    s = seuil(alpha)
    rejet = next((t for t, E in enumerate(es, 1) if E >= s), None)
    return (TEST, {"rejet": rejet, "E_final": es[-1], "seuil": s})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Test impossible : {res[1]}."
    info = res[1]
    if info["rejet"] is None:
        return f"H0 non rejetée (richesse E={info['E_final']:.2f} < seuil {info['seuil']:.1f}, type I ≤ α garanti même en s'arrêtant n'importe quand)."
    return (f"H0 rejetée à t={info['rejet']} (richesse ≥ {info['seuil']:.1f}). Erreur de type I ≤ α garantie SOUS arrêt "
            f"optionnel — un p-value classique répété serait sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== E-PROCESS / TEST PAR PARI (Ville) ===\n")
    p0 = 0.5
    for p_vrai, lab in [(0.5, "H0 vraie"), (0.65, "H1 vraie (effet)")]:
        xs = [1 if rng.random() < p_vrai else 0 for _ in range(300)]
        st, info = test_sequentiel(xs, p0, 0.05)
        print(f"  p_vrai={p_vrai} ({lab:16s}): E_final={info['E_final']:8.2f}  rejet à t={info['rejet']}")
    xs = [1 if rng.random() < 0.65 else 0 for _ in range(300)]
    print(" ", formule(test_sequentiel(xs, p0, 0.05)))
