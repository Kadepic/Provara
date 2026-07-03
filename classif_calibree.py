"""
PALIER 2 — CLASSIFICATION CALIBRÉE (brique 4, 2026-06-25).

Un classifieur (le nôtre ou un externe) crache des SCORES souvent MAL CALIBRÉS — typiquement SUR-CONFIANTS (un
« 0.9 » qui n'est juste que 75 % du temps). Cette brique RÉPARE la calibration sans modèle paramétrique, par
RÉGRESSION ISOTONIQUE (Pool Adjacent Violators) : on apprend, sur un jeu de calibration (score, issue 0/1), la
fonction MONOTONE croissante score -> probabilité qui colle aux fréquences observées. Plus un seuil d'ABSTENTION :
sous une confiance minimale, on dit « je ne sais pas » plutôt que de deviner.

POURQUOI ISOTONIQUE (et pas Platt/sigmoïde) : non paramétrique (aucune hypothèse de forme), monotone (préserve
l'ordre du classifieur), optimal au sens des moindres carrés sous contrainte de monotonie. Model-free, ~exact.

INVARIANT : après calibration, l'instrument calibration.py doit déclarer CALIBRE là où le brut était SURCONFIANT
(prouvé valide_classif.py). On RÉPARE la sur-confiance, on n'en crée jamais.

ABSTENTION : trop peu de points de calibration -> on ne fabrique pas de calibrateur (renvoie None). À la prédiction,
confiance < seuil -> ABSTENTION.
"""
from __future__ import annotations

import bisect

ABSTENTION = "abstention"
DECISION = "decision"
N_MIN_CAL = 30


class Calibrateur:
    """Fonction monotone croissante score -> probabilité, apprise par PAV. `seuils` triés, `valeurs` alignées :
    pour un score s, on renvoie la valeur du palier dont le seuil de départ est le plus grand ≤ s (escalier)."""

    __slots__ = ("seuils", "valeurs", "n")

    def __init__(self, seuils, valeurs, n):
        self.seuils = seuils
        self.valeurs = valeurs
        self.n = n

    def applique(self, score):
        """Probabilité calibrée d'un score (clampée dans [0,1], constante par paliers)."""
        if not self.seuils:
            return None
        i = bisect.bisect_right(self.seuils, float(score)) - 1
        if i < 0:
            i = 0
        return self.valeurs[i]


def ajuste_isotonique(scores, issues):
    """Apprend un Calibrateur par Pool Adjacent Violators sur des couples (score, issue ∈ {0,1}). Renvoie None
    (abstention) si moins de N_MIN_CAL points : on ne calibre pas honnêtement avec trop peu de données."""
    pts = sorted(zip((float(s) for s in scores), (1.0 if y else 0.0 for y in issues)))
    n = len(pts)
    if n < N_MIN_CAL:
        return None
    # 1) PRÉ-AGRÉGATION DES EX-ÆQUO : un bloc initial par score DISTINCT (somme des issues, effectif). Sans ça,
    #    deux points de même score (issues 0 puis 1) restent des blocs SÉPARÉS au même seuil et applique()
    #    (bisect_right−1) renvoie le dernier -> proba 1.0 = SUR-CONFIANCE FABRIQUÉE sur scores discrets/quantifiés
    #    (la « ligne rouge » P2). Regrouper d'abord garantit UNE fréquence par score. Aucun effet sur des scores
    #    tous distincts (un point = un groupe) -> comportement identique sur les scores continus.
    groupes = []                                   # [somme_issues, effectif, score] par score distinct, croissant
    for s, y in pts:
        if groupes and groupes[-1][2] == s:
            groupes[-1][0] += y
            groupes[-1][1] += 1.0
        else:
            groupes.append([y, 1.0, s])
    # 2) Pool Adjacent Violators sur les blocs pré-agrégés : fusionne tant qu'un bloc gauche > bloc droit.
    blocs = []
    for g in groupes:
        blocs.append(g)
        while len(blocs) >= 2 and blocs[-2][0] / blocs[-2][1] > blocs[-1][0] / blocs[-1][1]:
            sy, w, _ = blocs.pop()
            blocs[-1][0] += sy
            blocs[-1][1] += w
    seuils = [b[2] for b in blocs]
    valeurs = [b[0] / b[1] for b in blocs]
    return Calibrateur(seuils, valeurs, n)


def predit(calibrateur, score, seuil_abstention=0.0):
    """Probabilité calibrée pour `score` + décision honnête. Renvoie (DECISION, proba) si la confiance (max(p,1−p))
    ≥ seuil_abstention, sinon (ABSTENTION, proba). calibrateur=None (pas calibré) -> ABSTENTION."""
    if calibrateur is None:
        return (ABSTENTION, None)
    p = calibrateur.applique(score)
    confiance = max(p, 1.0 - p)
    if confiance < seuil_abstention:
        return (ABSTENTION, p)
    return (DECISION, p)


def formule(res) -> str:
    """Parole honnête d'une prédiction calibrée."""
    statut, p = res
    if statut == ABSTENTION:
        if p is None:
            return "Je ne peux pas me prononcer : pas assez de données pour calibrer honnêtement."
        return f"Je préfère m'abstenir : ma confiance calibrée (~{round(max(p,1-p)*100)}%) est sous mon seuil de décision."
    pct = round(p * 100)
    cls = "positif" if p >= 0.5 else "négatif"
    return f"Je penche pour « {cls} » avec une probabilité calibrée de {round(max(p,1-p)*100)}% (P(positif)={pct}%)."


if __name__ == "__main__":
    print("=== CLASSIFICATION CALIBRÉE (isotonique + abstention) ===\n")
    import math
    import random
    rng = random.Random(0)
    def sigmoid(x):
        return 1.0 / (1.0 + math.exp(-x))
    # classifieur SUR-CONFIANT : score = sigmoid(2z) alors que la vraie proba = sigmoid(z)
    scores, issues = [], []
    for _ in range(2000):
        z = rng.uniform(-3, 3)
        issues.append(1 if rng.random() < sigmoid(z) else 0)
        scores.append(sigmoid(2 * z))
    cal = ajuste_isotonique(scores, issues)
    print("  score brut 0.90 -> proba calibrée", round(cal.applique(0.90), 3))
    print("  score brut 0.10 -> proba calibrée", round(cal.applique(0.10), 3))
    print(" ", formule(predit(cal, 0.95, seuil_abstention=0.6)))
    print(" ", formule(predit(cal, 0.55, seuil_abstention=0.8)))   # confiance trop faible -> abstention
