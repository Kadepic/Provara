"""
PALIER 2 — PRÉDICTEUR DE VENN-ABERS (brique 16, 2026-06-25). La calibration à VALIDITÉ AUTOMATIQUE.

L'isotonique (classif_calibree.py) calibre bien, mais sa validité dépend du jeu de calibration et n'est pas garantie
point par point. Le prédicteur de Venn-Abers (Vovk) produit, lui, une PAIRE de probabilités [p0, p1] avec une
GARANTIE DE VALIDITÉ : l'une des deux est parfaitement calibrée (au sens multiprobabiliste), et l'intervalle [p0, p1]
EXPRIME l'incertitude SUR LA CALIBRATION elle-même (large = peu de données / score ambigu, étroit = sûr).

Mécanisme (Inductive Venn-Abers, IVAP) : pour un score test s, on calibre l'isotonique DEUX fois sur la calibration
AUGMENTÉE du point test —
    g0 = isotonique( cal + (s, étiquette=0) ),   p0 = g0(s)
    g1 = isotonique( cal + (s, étiquette=1) ),   p1 = g1(s)
On a toujours p0 ≤ p1 ; la vraie proba est « encadrée ». Probabilité ponctuelle calibrée : p = p1 / (1 − p0 + p1).

INVARIANT (jugé par calibration.py) : la probabilité fusionnée p est CALIBRÉE même quand le score brut est
sur-confiant ; l'intervalle [p0,p1] couvre p ; sa largeur DÉCROÎT quand la calibration grandit. ABSTENTION si trop peu.
"""
from __future__ import annotations

from classif_calibree import N_MIN_CAL
import bisect

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def _isotone_pav(scores, labels):
    """Régression isotonique (PAV) -> (seuils triés, valeurs) pour évaluation en escalier. Identique en esprit à
    classif_calibree mais réutilisable ici avec un point injecté."""
    pts = sorted(zip((float(s) for s in scores), (float(y) for y in labels)))
    # PRÉ-AGRÉGATION DES EX-ÆQUO avant le PAV (cf. classif_calibree.ajuste_isotonique) : un bloc par score
    # DISTINCT. Sinon, au score maximal ex-æquo, le point injecté (s,0) se trie AVANT les (s,1) et _eval prend
    # le dernier bloc -> p0=p1=1.0 avec intervalle de largeur NULLE (fausse certitude). Neutre sur scores distincts.
    groupes = []
    for s, y in pts:
        if groupes and groupes[-1][2] == s:
            groupes[-1][0] += y
            groupes[-1][1] += 1.0
        else:
            groupes.append([y, 1.0, s])
    blocs = []
    for g in groupes:
        blocs.append(g)
        while len(blocs) >= 2 and blocs[-2][0] / blocs[-2][1] > blocs[-1][0] / blocs[-1][1]:
            sy, w, _ = blocs.pop()
            blocs[-1][0] += sy
            blocs[-1][1] += w
    seuils = [b[2] for b in blocs]
    valeurs = [b[0] / b[1] for b in blocs]
    return seuils, valeurs


def _eval(seuils, valeurs, s):
    i = bisect.bisect_right(seuils, float(s)) - 1
    if i < 0:
        i = 0
    return valeurs[i]


class VennAbers:
    """Prédicteur de Venn-Abers inductif. `cal_scores`, `cal_labels` = jeu de calibration. `predit(s)` -> (p0, p1, p)."""

    __slots__ = ("scores", "labels", "n")

    def __init__(self, cal_scores, cal_labels):
        self.scores = [float(s) for s in cal_scores]
        self.labels = [1.0 if y else 0.0 for y in cal_labels]
        self.n = len(self.scores)

    def predit(self, score):
        """(ESTIMATION, (p0, p1, p)) où [p0,p1] encadre et p = p1/(1−p0+p1) est la proba ponctuelle calibrée, ou
        ABSTENTION si calibration trop courte."""
        if self.n < N_MIN_CAL:
            return (ABSTENTION, None)
        s = float(score)
        seuils0, val0 = _isotone_pav(self.scores + [s], self.labels + [0.0])
        seuils1, val1 = _isotone_pav(self.scores + [s], self.labels + [1.0])
        p0 = _eval(seuils0, val0, s)
        p1 = _eval(seuils1, val1, s)
        denom = 1.0 - p0 + p1
        p = p1 / denom if denom > 0 else 0.5
        return (ESTIMATION, (p0, p1, p))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return "Je préfère ne pas donner de probabilité : pas assez de calibration."
    p0, p1, p = res[1]
    return (f"Probabilité ~{round(p*100)}% (encadrée par [{round(p0*100)}%, {round(p1*100)}%]). L'écart de l'encadrement "
            "dit combien je suis sûr de cette calibration : plus il est large, moins je suis certain.")


if __name__ == "__main__":
    print("=== PRÉDICTEUR DE VENN-ABERS ===\n")
    import math
    import random
    rng = random.Random(0)
    def sig(x):
        return 1.0 / (1.0 + math.exp(-x))
    sc, lb = [], []
    for _ in range(800):
        z = rng.uniform(-3, 3)
        lb.append(1 if rng.random() < sig(z) else 0)
        sc.append(sig(2.5 * z))            # score brut sur-confiant
    va = VennAbers(sc, lb)
    for s in (0.95, 0.5, 0.05):
        print(f"  score brut {s} ->", formule(va.predit(s)))
