"""
PALIER 2 — TEST DE PERMUTATION : tester une différence sans supposer la normalité (brique 82, 2026-06-27).

Comparer deux groupes A et B : le t-test SUPPOSE des données ~normales. Sur des données ASYMÉTRIQUES / à queue lourde
(temps de réponse, revenus, comptages), à petit n, cette hypothèse est fausse et le t-test a un taux d'erreur de type I
DÉRÉGLÉ (souvent gonflé) → il rejette trop = SUR-CONFIANCE dans la « significativité ».

Le TEST DE PERMUTATION ne suppose RIEN sur la loi, seulement l'ÉCHANGEABILITÉ sous H0 (mêmes étiquettes
interchangeables) : on calcule la statistique observée (ex. différence de moyennes), puis on REMÉLANGE les étiquettes
des deux groupes un grand nombre de fois ; la p-value = fraction des remélanges donnant une statistique aussi extrême.
    p = (1 + #{ |T*| ≥ |T_obs| }) / (B + 1).
Elle contrôle EXACTEMENT l'erreur de type I sous échangeabilité, quelle que soit la loi.

LE MODE D'ÉCHEC DÉMASQUÉ : le t-test sur des données non-normales sur-rejette (type I > α) = sur-confiance ; le test de
permutation reste calibré (type I ≈ α) sans perdre de puissance sous normalité. ABSTENTION si un groupe est vide. Pur
Python.
"""
from __future__ import annotations

import math

from bayes_sequentiel import betai

ABSTENTION = "abstention"
TEST = "test"


def difference_moyennes(A, B):
    return sum(A) / len(A) - sum(B) / len(B)


def p_permutation(A, B, rng, n_perm=2000):
    """p-value bilatérale par permutation de la différence des moyennes (échange des étiquettes)."""
    t_obs = abs(difference_moyennes(A, B))
    pool = list(A) + list(B)
    nA = len(A)
    extreme = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        d = abs(sum(pool[:nA]) / nA - sum(pool[nA:]) / (len(pool) - nA))
        if d >= t_obs - 1e-12:
            extreme += 1
    return (1 + extreme) / (n_perm + 1)


def p_ttest_welch(A, B):
    """p-value bilatérale du t-test de Welch (suppose la normalité) via la fonction bêta incomplète."""
    nA, nB = len(A), len(B)
    mA, mB = sum(A) / nA, sum(B) / nB
    vA = sum((x - mA) ** 2 for x in A) / (nA - 1)
    vB = sum((x - mB) ** 2 for x in B) / (nB - 1)
    se2 = vA / nA + vB / nB
    if se2 <= 0:
        return 1.0
    t = (mA - mB) / math.sqrt(se2)
    df = se2 ** 2 / ((vA / nA) ** 2 / (nA - 1) + (vB / nB) ** 2 / (nB - 1))
    return betai(df / 2, 0.5, df / (df + t * t))      # p bilatéral du Student-t


def teste(A, B, rng, n_perm=2000, alpha=0.05):
    """Façade : (TEST, {p_perm, p_ttest, rejet_perm}) ou (ABSTENTION, raison)."""
    if len(A) < 2 or len(B) < 2:
        return (ABSTENTION, "groupe trop petit (n<2)")
    pp = p_permutation(A, B, rng, n_perm)
    return (TEST, {"p_perm": pp, "p_ttest": p_ttest_welch(A, B), "rejet_perm": pp < alpha,
                   "diff": difference_moyennes(A, B)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Test impossible : {res[1]}."
    i = res[1]
    return (f"Différence={i['diff']:.3f} ; p (permutation, distribution-free)={i['p_perm']:.3f} "
            f"(t-test={i['p_ttest']:.3f}). La permutation contrôle l'erreur sans supposer la normalité ; le t-test "
            f"sur données asymétriques serait sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== TEST DE PERMUTATION ===\n")
    A = [rng.gauss(0, 1) for _ in range(12)]; B = [rng.gauss(0.8, 1) for _ in range(12)]
    print(" ", formule(teste(A, B, rng)))
    # type I sous H0 avec données ASYMÉTRIQUES (exponentielles)
    for loi, gen in [("normale", lambda: rng.gauss(0, 1)), ("exponentielle (asym.)", lambda: random.expovariate(1))]:
        rej_t = rej_p = 0; N = 400
        for _ in range(N):
            A = [gen() for _ in range(8)]; B = [gen() for _ in range(8)]
            rej_t += p_ttest_welch(A, B) < 0.05
            rej_p += p_permutation(A, B, rng, 500) < 0.05
        print(f"  H0 {loi:22s}: type I t-test={rej_t/N:.3f}  permutation={rej_p/N:.3f} (nominal 0.05)")
