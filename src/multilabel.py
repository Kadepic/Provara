"""
PALIER 2 — CALIBRATION MULTI-LABEL (brique 23, 2026-06-25).

Quand une instance peut porter PLUSIEURS labels vrais à la fois (tags, symptômes, thèmes…), on veut une probabilité
CALIBRÉE par label + un ensemble de labels prédits dont on CONTRÔLE le risque. Deux étages model-free :

  • CALIBRATION PAR LABEL : chaque label j est traité comme un forecast binaire P(j présent) ; on le recalibre par
    ISOTONIQUE (classif_calibree). Après ça, « label j à 30 % » est présent ~30 % du temps.
  • SEUIL À RAPPEL CONTRÔLÉ : on choisit un seuil τ tel que la fraction des VRAIS labels retenus (rappel) ≥ 1−cible,
    via le contrôle de risque conforme (risque_conforme) sur les probas calibrées des vrais labels.

INVARIANT (jugé par calibration.py + risque_conforme) : chaque proba de label est calibrée ; le rappel macro tient sa
cible sur des données fraîches. ABSTENTION (None) si trop peu de données. On ne fabrique jamais de sur-confiance.
"""
from __future__ import annotations

from classif_calibree import ajuste_isotonique, N_MIN_CAL
import risque_conforme as _RQC


class CalibrateurMultiLabel:
    __slots__ = ("labels", "calibrateurs")

    def __init__(self, labels, calibrateurs):
        self.labels = labels
        self.calibrateurs = calibrateurs

    def applique(self, scores):
        """dict {label: score_brut} -> dict {label: proba_calibrée}. Labels inconnus ignorés."""
        return {j: self.calibrateurs[j].applique(scores.get(j, 0.0)) for j in self.labels if j in self.calibrateurs}

    def predit(self, scores, seuil=0.5):
        """Ensemble des labels dont la proba calibrée ≥ seuil."""
        p = self.applique(scores)
        return {j for j, v in p.items() if v >= seuil}


def ajuste_multilabel(scores_par_ex, labels_presents):
    """`scores_par_ex` = liste de dict {label: score} ; `labels_presents` = liste d'ENSEMBLES de labels vrais.
    Calibre chaque label par isotonique. Renvoie un CalibrateurMultiLabel ou None si trop peu de données."""
    labels = sorted({j for d in scores_par_ex for j in d})
    n = len(scores_par_ex)
    if n < N_MIN_CAL or not labels:
        return None
    calibrateurs = {}
    for j in labels:
        sc = [float(d.get(j, 0.0)) for d in scores_par_ex]
        pres = [1 if j in s else 0 for s in labels_presents]
        if sum(pres) < 1:
            continue
        cal = ajuste_isotonique(sc, pres)
        if cal is not None:
            calibrateurs[j] = cal
    if not calibrateurs:
        return None
    return CalibrateurMultiLabel(labels, calibrateurs)


def seuil_rappel(calibrateur, scores_par_ex, labels_presents, cible_manques=0.10):
    """Choisit un seuil τ garantissant un RAPPEL macro ≥ 1−cible_manques (au plus `cible_manques` de vrais labels
    manqués), via le contrôle de risque conforme sur les probas calibrées des VRAIS labels présents."""
    probas_vrais = []
    for d, presents in zip(scores_par_ex, labels_presents):
        p = calibrateur.applique(d)
        for j in presents:
            if j in p:
                probas_vrais.append(p[j])
    return _RQC.controle_fnr(probas_vrais, cible_manques)


def formule(ensemble) -> str:
    if not ensemble:
        return "Aucun label assez probable — je préfère n'en affirmer aucun."
    return f"Labels retenus (probas calibrées) : {{{', '.join(sorted(map(str, ensemble)))}}}."


if __name__ == "__main__":
    print("=== CALIBRATION MULTI-LABEL ===\n")
    import math
    import random
    rng = random.Random(0)
    def sig(x):
        return 1.0 / (1.0 + math.exp(-x))
    labels = ["sport", "politique", "tech"]
    sx, sp = [], []
    for _ in range(1500):
        presents = set()
        d = {}
        for j in labels:
            z = rng.gauss(0, 1.5)
            if rng.random() < sig(z):
                presents.add(j)
            d[j] = sig(2.5 * z)            # score sur-confiant
        sx.append(d); sp.append(presents)
    cal = ajuste_multilabel(sx, sp)
    print("  ex brut :", {j: round(sx[0][j], 2) for j in labels})
    print("  ex calib:", {j: round(v, 2) for j, v in cal.applique(sx[0]).items()})
    tau = seuil_rappel(cal, sx, sp, 0.10)
    print(f"  seuil rappel≥90% : τ={tau:.3f}")
