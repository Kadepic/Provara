"""
PALIER 2 — ENSEMBLE CALIBRÉ (stacking de forecasters, brique 15, 2026-06-25).

Plusieurs forecasters imparfaits valent mieux qu'un — À CONDITION de les combiner honnêtement. On COMBINE leurs
probabilités (moyenne, éventuellement pondérée par leur qualité passée) puis on RECALIBRE le résultat par isotonique
(classif_calibree.py). Deux gains cumulés :
  • la moyenne réduit la VARIANCE des erreurs (les bruits indépendants des membres se compensent) -> meilleur RAFFINEMENT ;
  • la recalibration corrige le biais résiduel -> CALIBRATION.

INVARIANT (jugé par calibration.py + scores_propres.py) : l'ensemble est CALIBRÉ et a un MEILLEUR score propre
(log-loss/Brier) que CHAQUE membre, HORS-ÉCHANTILLON. + abstention sous seuil. On ne fabrique pas de sur-confiance :
la recalibration isotonique ne ment jamais en sur-promettant.
"""
from __future__ import annotations

from classif_calibree import ajuste_isotonique, N_MIN_CAL
from scores_propres import log_loss

ABSTENTION = "abstention"
DECISION = "decision"


def moyenne_ponderee(probas_membres, poids):
    """Moyenne pondérée des probabilités des membres. `probas_membres` = dict {nom: proba} ; `poids` = dict {nom: w}
    (somme > 0). Renvoie la proba moyenne."""
    s = sum(poids[n] for n in probas_membres)
    if s <= 0:
        return sum(probas_membres.values()) / len(probas_membres)
    return sum(poids[n] * float(p) for n, p in probas_membres.items()) / s


class EnsembleCalibre:
    """Combine des forecasters (moyenne pondérée) + recalibration isotonique. `ajuste(sorties, issues)` puis
    `applique({nom: proba})` / `predit({nom: proba}, seuil)`."""

    __slots__ = ("noms", "poids", "calibrateur")

    def __init__(self, noms, poids, calibrateur):
        self.noms = noms
        self.poids = poids
        self.calibrateur = calibrateur

    def applique(self, probas_membres):
        """Proba calibrée de l'ensemble pour un cas (dict {nom: proba}). Membres manquants ignorés."""
        sous = {n: probas_membres[n] for n in self.noms if n in probas_membres}
        if not sous:
            return None
        moy = moyenne_ponderee(sous, self.poids)
        return self.calibrateur.applique(moy)

    def predit(self, probas_membres, seuil_abstention=0.0):
        p = self.applique(probas_membres)
        if p is None:
            return (ABSTENTION, None)
        if max(p, 1.0 - p) < seuil_abstention:
            return (ABSTENTION, p)
        return (DECISION, p)


def ajuste_ensemble(sorties, issues, ponderation: str = "uniforme"):
    """Apprend un EnsembleCalibre. `sorties` = dict {nom: liste_de_probas} (alignées sur `issues`). `ponderation` ∈
    {uniforme, inverse_perte} (poids ∝ 1/log-loss du membre sur la calibration). Renvoie None si trop peu de données."""
    noms = sorted(sorties)
    n = len(issues)
    if n < N_MIN_CAL or not noms:
        return None
    if ponderation == "inverse_perte":
        poids = {}
        for nm in noms:
            ll = log_loss(sorties[nm], issues)
            poids[nm] = 1.0 / max(ll, 1e-6)
    else:
        poids = {nm: 1.0 for nm in noms}
    # moyenne pondérée par cas, puis isotonique sur (moyenne, issue)
    moy = []
    for i in range(n):
        moy.append(moyenne_ponderee({nm: sorties[nm][i] for nm in noms}, poids))
    cal = ajuste_isotonique(moy, issues)
    if cal is None:
        return None
    return EnsembleCalibre(noms, poids, cal)


def formule(res) -> str:
    statut, p = res
    if statut == ABSTENTION:
        if p is None:
            return "Je ne peux pas trancher : ensemble indisponible (pas assez de données / membres)."
        return f"Je m'abstiens : la confiance calibrée de l'ensemble (~{round(max(p,1-p)*100)}%) est sous mon seuil."
    return f"L'ensemble (combiné + recalibré) penche pour « {'positif' if p>=0.5 else 'négatif'} » à {round(max(p,1-p)*100)}%."


if __name__ == "__main__":
    print("=== ENSEMBLE CALIBRÉ (stacking) ===\n")
    import math
    import random
    rng = random.Random(0)
    def sig(x):
        return 1.0 / (1.0 + math.exp(-x))
    sorties = {"A": [], "B": [], "C": []}
    issues = []
    for _ in range(2000):
        z = rng.uniform(-3, 3)
        issues.append(1 if rng.random() < sig(z) else 0)
        sorties["A"].append(sig(2 * z + rng.gauss(0, 1)))     # sur-confiant + bruit
        sorties["B"].append(sig(0.6 * z + rng.gauss(0, 1)))   # sous-confiant + bruit
        sorties["C"].append(sig(z + rng.gauss(0, 1.5)))       # ~ok mais bruité
    ens = ajuste_ensemble(sorties, issues, "inverse_perte")
    cas = {"A": sorties["A"][0], "B": sorties["B"][0], "C": sorties["C"][0]}
    print("  proba ensemble pour le 1er cas :", round(ens.applique(cas), 3), "(issue =", issues[0], ")")
    print(" ", formule(ens.predit(cas, 0.6)))
