"""
PALIER 2 — STABILITÉ ALGORITHMIQUE & généralisation (Bousquet-Elisseeff 2002) (brique 74, 2026-06-27).

Un algorithme d'apprentissage A est β-uniformément STABLE si changer UN exemple du jeu d'entraînement modifie sa perte
de ≤ β partout : |ℓ(A_S, z) − ℓ(A_{S'}, z)| ≤ β. Théorème : un algorithme stable GÉNÉRALISE — avec proba ≥ 1−δ
(perte ∈ [0,M]),
    R_vrai(A_S) ≤ R_emp(A_S) + 2β + (4nβ + M)·√( ln(1/δ) / (2n) ).
Donc R_emp ≈ R_vrai dès que β est petit (algorithme « lisse » : régularisé, k-NN à grand k…).

LE MODE D'ÉCHEC DÉMASQUÉ : un algorithme INSTABLE (qui MÉMORISE, ex. 1-plus-proche-voisin) a un risque empirique
≈ 0 mais un vrai risque élevé → annoncer le risque empirique est SUR-CONFIANT. Sa stabilité β est grande, donc la
borne le SAIT (elle reste large). Un algorithme stable (grand k) a un petit écart R_vrai − R_emp et une borne serrée.
La stabilité est le PRIX/garant de la généralisation. (Distinct de PAC-Bayes/Rademacher : propriété de l'ALGORITHME,
pas de la classe.) ABSTENTION si invalide. Pur Python (k-NN régression, perte quadratique sur [0,1]).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def knn(train, x, k):
    """Prédiction k-NN régression en x = moyenne des y des k plus proches. `train` = liste de (xi, yi)."""
    vois = sorted(train, key=lambda p: abs(p[0] - x))[:k]
    return sum(p[1] for p in vois) / len(vois)


def risque(train, points, k):
    """Risque quadratique moyen de A_train sur `points` (liste de (x,y))."""
    return sum((knn(train, x, k) - y) ** 2 for x, y in points) / len(points)


def stabilite_empirique(train, population, k, rng, swaps=8):
    """β̂ ≈ max_z |ℓ(A_S,z) − ℓ(A_{S'},z)|, S' = S avec un exemple remplacé (moyenne sur quelques swaps)."""
    n = len(train)
    beta = 0.0
    for _ in range(swaps):
        i = rng.randrange(n)
        neuf = population[rng.randrange(len(population))]
        Sp = train[:i] + [neuf] + train[i + 1:]
        for x, y in population:
            d = abs((knn(train, x, k) - y) ** 2 - (knn(Sp, x, k) - y) ** 2)
            beta = max(beta, d)
    return beta


def borne_generalisation(r_emp, beta, n, delta=0.05, M=1.0):
    """Borne de Bousquet-Elisseeff : R_emp + 2β + (4nβ + M)√(ln(1/δ)/2n)."""
    return r_emp + 2 * beta + (4 * n * beta + M) * math.sqrt(math.log(1.0 / delta) / (2.0 * n))


def analyse(train, population, k, rng, delta=0.05):
    """Façade : (ANALYSE, {r_emp, r_vrai, beta, borne}) ou (ABSTENTION, raison)."""
    if not train or not population or k < 1 or k > len(train) or not (0 < delta < 1):
        return (ABSTENTION, "entrée invalide (train/pop vide, k hors [1,n], δ∉(0,1))")
    re = risque(train, train, k)
    rv = risque(train, population, k)
    beta = stabilite_empirique(train, population, k, rng)
    return (ANALYSE, {"r_emp": re, "r_vrai": rv, "beta": beta,
                      "borne": borne_generalisation(re, beta, len(train), delta)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Analyse impossible : {res[1]}."
    i = res[1]
    return (f"Stabilité β̂={i['beta']:.3f} ; risque empirique {i['r_emp']:.3f}, vrai {i['r_vrai']:.3f}, borne ≤ {i['borne']:.3f}. "
            f"Un algorithme instable (β grand) annoncerait un risque empirique sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    f = lambda x: 0.5 + 0.4 * math.sin(3 * x)
    pop = [(x, min(1, max(0, f(x) + rng.gauss(0, 0.1)))) for x in [i / 150 for i in range(150)]]
    train = [pop[rng.randrange(len(pop))] for _ in range(30)]
    print("=== STABILITÉ ALGORITHMIQUE (Bousquet-Elisseeff) ===\n")
    for k in (1, 3, 9, 15):
        info = analyse(train, pop, k, random.Random(1))[1]
        print(f"  k={k:>2} : β̂={info['beta']:.3f}  R_emp={info['r_emp']:.3f}  R_vrai={info['r_vrai']:.3f}  "
              f"écart={info['r_vrai']-info['r_emp']:+.3f}  borne≤{info['borne']:.3f}")
    print(" ", formule(analyse(train, pop, 9, random.Random(1))))
