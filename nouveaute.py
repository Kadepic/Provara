"""
PALIER 2 — DÉTECTION DE NOUVEAUTÉ / HORS-DISTRIBUTION (brique 11, 2026-06-25).

Une réponse calibrée ne vaut que si l'entrée RESSEMBLE à ce qu'on a appris. Face à un point ATYPIQUE (hors du domaine
de calibration), la franchise est de le DIRE et de s'abstenir, plutôt que d'extrapoler avec une fausse assurance.

Mécanisme = p-VALEUR CONFORME (conformal anomaly detection). On attribue à chaque point un SCORE DE NON-CONFORMITÉ
(plus haut = plus atypique). Pour un point test de score s, sa p-valeur vs un jeu de calibration de scores connus :

    p = (1 + #{ score_calibration ≥ s }) / (n + 1)

Sous ÉCHANGEABILITÉ (le point test vient de la même distribution que la calibration), p est ~uniforme sur [0,1], donc
P(p ≤ α) ≤ α : déclarer « NOUVEAU » quand p < α DONNE UN TAUX DE FAUSSE ALARME ≤ α — GARANTI, sans hypothèse de loi.
C'est l'invariant de calibration appliqué à « est-ce dans mon domaine ? ».

Fournis : la p-valeur générique (score-agnostique), un scoreur k-NN prêt à l'emploi (distance moyenne aux k plus
proches voisins de référence), et l'abstention honnête « hors-domaine ».
"""
from __future__ import annotations

import math

NOUVEAU = "nouveau"
CONNU = "connu"


def pvaleur_conforme(scores_calibration, score_test) -> float:
    """p-valeur conforme d'un score test vs des scores de calibration (non-conformité, plus haut = plus atypique).
    p = (1 + #{cal ≥ test}) / (n+1). Petite p -> atypique. Valide (≥ uniforme) sous échangeabilité."""
    cal = [float(s) for s in scores_calibration]
    n = len(cal)
    if n == 0:
        raise ValueError("aucun score de calibration")
    s = float(score_test)
    sup = sum(1 for c in cal if c >= s)
    return (1.0 + sup) / (n + 1.0)


def est_nouveau(scores_calibration, score_test, alpha: float = 0.05):
    """Verdict de nouveauté : (NOUVEAU, p) si p < alpha (atypique au seuil de fausse alarme alpha), sinon (CONNU, p).
    `alpha` = taux de fausse alarme TOLÉRÉ (garanti : un point in-distribution est flaggé NOUVEAU ≤ alpha du temps)."""
    p = pvaleur_conforme(scores_calibration, score_test)
    return (NOUVEAU if p < alpha else CONNU, p)


def _distance(a, b):
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def scoreur_knn(reference, k: int = 5):
    """Renvoie une fonction point -> score de non-conformité = distance MOYENNE aux k plus proches voisins de
    `reference` (jeu de points). Score élevé = loin de tout = atypique. `reference` = liste de vecteurs (tuples/listes)."""
    ref = [tuple(float(v) for v in p) for p in reference]
    if not ref:
        raise ValueError("référence vide")
    kk = min(k, len(ref))

    def score(point):
        pt = tuple(float(v) for v in point)
        d = sorted(_distance(pt, r) for r in ref)
        return sum(d[:kk]) / kk

    return score


def formule(res) -> str:
    verdict, p = res
    if verdict == NOUVEAU:
        return (f"⚠ Ce cas semble HORS de mon domaine (p={p:.3f}) : il ne ressemble pas à ce que j'ai appris. "
                "Je préfère m'abstenir plutôt que d'extrapoler.")
    return f"Ce cas ressemble à mon domaine d'apprentissage (p={p:.3f}) : je peux me prononcer."


if __name__ == "__main__":
    print("=== DÉTECTION DE NOUVEAUTÉ (p-valeur conforme) ===\n")
    import random
    rng = random.Random(0)
    ref = [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(300)]
    cal_pts = [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(300)]
    sc = scoreur_knn(ref, k=5)
    scores_cal = [sc(p) for p in cal_pts]
    print(" ", formule(est_nouveau(scores_cal, sc((0.2, -0.3)), 0.05)))     # in-distribution
    print(" ", formule(est_nouveau(scores_cal, sc((6.0, 6.0)), 0.05)))      # loin -> nouveau
