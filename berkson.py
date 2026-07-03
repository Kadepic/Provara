"""
PALIER 2 — PARADOXE DE BERKSON / BIAIS DE COLLISION : sélectionner sur un EFFET COMMUN fabrique une corrélation
fantôme (brique 92, 2026-06-27).

Deux traits A et B INDÉPENDANTS dans la population peuvent apparaître fortement CORRÉLÉS (souvent NÉGATIVEMENT) dès
qu'on n'observe qu'un SOUS-ENSEMBLE sélectionné sur un COLLISIONNEUR — une variable que A et B influencent tous deux
(« admis à l'hôpital si maladie A OU B », « recruté si compétent OU pistonné », « célèbre si talentueux OU chanceux »).
Parmi les sélectionnés, si A est faux il a FALLU que B soit vrai → A et B s'anti-corrèlent artificiellement.

Conditionner sur un collisionneur (ou son descendant) OUVRE un chemin non causal entre A et B (≠ confusion, où c'est un
ANCÊTRE commun qu'il faut au contraire contrôler — cf. [[causal]] ; ≠ Simpson, qui est un renversement d'agrégation).

LE MODE D'ÉCHEC DÉMASQUÉ : conclure « A protège de B » (ou toute association) à partir d'un échantillon SÉLECTIONNÉ est
SUR-CONFIANT — l'association est INDUITE par la sélection, pas réelle. L'attitude honnête : repérer le collisionneur et
NE PAS contrôler/sélectionner dessus. ABSTENTION si données insuffisantes. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
BERKSON = "berkson"


def correlation(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (sx * sy) if sx > 0 and sy > 0 else 0.0


def selectionne_collisionneur(A, B, seuil):
    """Indices sélectionnés sur le collisionneur C = A+B > seuil (ex. 'admis si A ou B élevé')."""
    return [i for i in range(len(A)) if A[i] + B[i] > seuil]


def correlation_population(A, B):
    return correlation(A, B)


def correlation_selectionnee(A, B, seuil):
    idx = selectionne_collisionneur(A, B, seuil)
    if len(idx) < 3:
        return None
    return correlation([A[i] for i in idx], [B[i] for i in idx])


def analyse(A, B, seuil):
    """Façade : compare corr(A,B) en population vs dans l'échantillon sélectionné sur le collisionneur.
    (BERKSON, {corr_pop, corr_sel, biais}) ou (ABSTENTION, raison)."""
    if len(A) < 30 or len(A) != len(B):
        return (ABSTENTION, "données insuffisantes ou tailles différentes")
    cp = correlation_population(A, B)
    cs = correlation_selectionnee(A, B, seuil)
    if cs is None:
        return (ABSTENTION, "trop peu de sélectionnés")
    return (BERKSON, {"corr_pop": cp, "corr_sel": cs, "biais": cs - cp})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Corrélation A–B : population {i['corr_pop']:+.2f} (≈ indépendants) → échantillon SÉLECTIONNÉ "
            f"{i['corr_sel']:+.2f}. L'association {('négative' if i['corr_sel']<0 else 'apparente')} est INDUITE par la "
            f"sélection (biais de collision) — y voir un lien réel serait sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    A = [rng.gauss(0, 1) for _ in range(5000)]
    B = [rng.gauss(0, 1) for _ in range(5000)]        # indépendants
    print("=== PARADOXE DE BERKSON / BIAIS DE COLLISION ===\n")
    print(f"  population : corr(A,B) = {correlation(A, B):+.3f} (indépendants)")
    for seuil in (1.0, 1.5, 2.0):
        cs = correlation_selectionnee(A, B, seuil)
        print(f"  sélection sur A+B>{seuil} : corr(A,B) = {cs:+.3f} (fantôme négative)")
    print(" ", formule(analyse(A, B, 1.5)))
