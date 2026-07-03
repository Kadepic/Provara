"""
PALIER 2 — CLASSIFICATION CALIBRÉE MULTI-CLASSE (brique 7, 2026-06-25). Complète classif_calibree.py (binaire).

Quand la réponse est UNE catégorie parmi K (diagnostic, langue, espèce…), on veut une PROBABILITÉ CALIBRÉE PAR CLASSE
— pas seulement la classe gagnante — plus l'abstention sous un seuil de confiance. Méthode model-free, dans l'esprit
de la brique binaire : ISOTONIQUE UN-CONTRE-TOUS (un calibrateur monotone par classe sur le score brut de cette classe
vs « est-ce la vraie classe ? »), puis NORMALISATION à somme 1.

INVARIANT (jugé par calibration.py) : après calibration, (a) la confiance de la classe gagnante est calibrée
(top-label : un « 80 % » gagne vraiment ~80 %), et (b) chaque proba P(classe=c) est calibrée (un « 30 % » se réalise
~30 %). On RÉPARE la sur-confiance d'un classifieur trop sûr, on n'en crée pas.

ABSTENTION : moins de N_MIN_CAL exemples par classe -> pas de calibrateur ; confiance gagnante < seuil -> « je ne sais pas ».
"""
from __future__ import annotations

from classif_calibree import ajuste_isotonique, N_MIN_CAL

ABSTENTION = "abstention"
DECISION = "decision"


class CalibrateurMC:
    """Un calibrateur isotonique par classe (un-contre-tous) + la liste des classes."""

    __slots__ = ("classes", "calibrateurs")

    def __init__(self, classes, calibrateurs):
        self.classes = classes
        self.calibrateurs = calibrateurs        # classe -> Calibrateur (binaire)

    def applique(self, scores):
        """scores = dict {classe: score_brut} -> dict {classe: proba_calibrée} NORMALISÉ à somme 1.
        Classe absente de l'apprentissage -> ignorée. Somme nulle -> uniforme sur les classes connues."""
        brut = {}
        for c in self.classes:
            cal = self.calibrateurs[c]
            brut[c] = cal.applique(scores.get(c, 0.0))
        s = sum(brut.values())
        if s <= 0:
            u = 1.0 / len(self.classes)
            return {c: u for c in self.classes}
        return {c: v / s for c, v in brut.items()}


def ajuste_multiclasse(scores_par_exemple, labels):
    """Apprend un CalibrateurMC. `scores_par_exemple` = liste de dict {classe: score_brut} ; `labels` = vraie classe
    de chaque exemple. Renvoie None (abstention) si une classe a moins de N_MIN_CAL exemples (calibration non fiable)."""
    classes = sorted({c for d in scores_par_exemple for c in d} | set(labels))
    calibrateurs = {}
    for c in classes:
        sc = [d.get(c, 0.0) for d in scores_par_exemple]
        iss = [1 if y == c else 0 for y in labels]
        if sum(iss) < 1 or len(sc) < N_MIN_CAL:
            return None
        cal = ajuste_isotonique(sc, iss)
        if cal is None:
            return None
        calibrateurs[c] = cal
    return CalibrateurMC(classes, calibrateurs)


def predit(calibrateur, scores, seuil_abstention=0.0):
    """Renvoie (DECISION, classe_gagnante, probas) si la confiance gagnante ≥ seuil, sinon (ABSTENTION, None, probas).
    calibrateur=None -> (ABSTENTION, None, None)."""
    if calibrateur is None:
        return (ABSTENTION, None, None)
    probas = calibrateur.applique(scores)
    gagnante = max(probas, key=probas.get)
    if probas[gagnante] < seuil_abstention:
        return (ABSTENTION, None, probas)
    return (DECISION, gagnante, probas)


def brier_multiclasse(probas_par_exemple, labels) -> float:
    """Score de Brier multi-classe : moyenne sur les exemples de Σ_c (p_c − 1{y=c})². 0 = parfait. Règle propre."""
    if not probas_par_exemple:
        raise ValueError("aucune donnée")
    total = 0.0
    for probas, y in zip(probas_par_exemple, labels):
        total += sum((p - (1.0 if c == y else 0.0)) ** 2 for c, p in probas.items())
    return total / len(probas_par_exemple)


def formule(res) -> str:
    statut = res[0]
    if statut == ABSTENTION:
        if res[2] is None:
            return "Je ne peux pas me prononcer : pas assez d'exemples pour calibrer honnêtement."
        return "Je préfère m'abstenir : aucune classe n'atteint mon seuil de confiance."
    _, gagnante, probas = res
    return f"Je penche pour « {gagnante} » à {round(probas[gagnante]*100)}% (probabilité calibrée par classe)."


if __name__ == "__main__":
    print("=== CLASSIFICATION CALIBRÉE MULTI-CLASSE ===\n")
    import math
    import random
    rng = random.Random(0)
    classes = ["A", "B", "C"]
    def softmax(zs, T=1.0):
        m = max(zs)
        es = [math.exp((z - m) / T) for z in zs]
        s = sum(es)
        return [e / s for e in es]
    ex, lab = [], []
    for _ in range(1500):
        zs = [rng.gauss(0, 1.5) for _ in classes]
        p_vrai = softmax(zs, 1.0)
        u = rng.random(); cum = 0.0; y = classes[-1]
        for i, p in enumerate(p_vrai):
            cum += p
            if u < cum:
                y = classes[i]; break
        p_brut = softmax(zs, 0.5)             # T<1 -> SUR-CONFIANT
        ex.append({c: p_brut[i] for i, c in enumerate(classes)})
        lab.append(y)
    cal = ajuste_multiclasse(ex, lab)
    print("  exemple :", formule(predit(cal, ex[0], seuil_abstention=0.5)))
    print("  probas brutes :", {c: round(ex[0][c], 2) for c in classes})
    print("  probas calibrées :", {c: round(p, 2) for c, p in cal.applique(ex[0]).items()})
