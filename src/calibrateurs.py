"""
PALIER 2 — CALIBRATEURS PARAMÉTRIQUES (brique 18, 2026-06-25). La trousse complète de recalibration binaire.

classif_calibree.py fournit l'ISOTONIQUE (non paramétrique, monotone). On complète ici la trousse — chaque méthode
a son régime de prédilection, et on les met TOUTES sous le même juge (calibration.py) :

  • Platt (sigmoïde)     — p = σ(a·s + b), 2 paramètres. Idéal quand le miscalibrage est ~sigmoïdal (sur/sous-confiance
    régulière) ; très robuste en petit échantillon (peu de paramètres, lissage des cibles).
  • Histogram binning    — découpe [0,1] en B casiers, p = fréquence empirique du casier. Non paramétrique, simple,
    garantie par casier ; granularité réglable.
  • Beta calibration     — ln(p/(1−p)) = a·ln(s) − b·ln(1−s) + c, 3 paramètres. Plus flexible que Platt (gère
    l'asymétrie), reste lisse.

INVARIANT (jugé par calibration.py) : sur un classifieur SUR-confiant, chaque calibrateur RÉDUIT l'ECE hors-échantillon
et ne produit JAMAIS de sur-confiance. ABSTENTION (None) si trop peu de données. Model-free, pur Python, pas de lib.
"""
from __future__ import annotations

import bisect
import math

N_MIN_CAL = 30
_EPS = 1e-6


def _clip(p, lo=_EPS, hi=1.0 - _EPS):
    return max(lo, min(hi, p))


def _sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _regression_logistique(features, labels, dim, iters=4000, lr=0.1):
    """Descente de gradient sur la log-loss pour une régression logistique (poids `w` de taille dim + biais b).
    `features` = liste de vecteurs de taille dim. Renvoie (w, b). Convexe -> converge."""
    n = len(labels)
    w = [0.0] * dim
    b = 0.0
    for _ in range(iters):
        gw = [0.0] * dim
        gb = 0.0
        for i in range(n):
            z = b + sum(w[d] * features[i][d] for d in range(dim))
            err = _sigmoid(z) - labels[i]
            gb += err
            for d in range(dim):
                gw[d] += err * features[i][d]
        b -= lr * gb / n
        for d in range(dim):
            w[d] -= lr * gw[d] / n
    return w, b


class CalibrateurPlatt:
    """Calibration de Platt : p = σ(a·s + b). Lissage des cibles (évite l'overfit en petit échantillon)."""

    __slots__ = ("a", "b")

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def applique(self, score):
        return _sigmoid(self.a * float(score) + self.b)


def ajuste_platt(scores, labels):
    s = [float(v) for v in scores]
    y = [1.0 if v else 0.0 for v in labels]
    n = len(s)
    if n < N_MIN_CAL:
        return None
    npos = sum(y)
    nneg = n - npos
    # cibles lissées (Platt 1999) : évite p=0/1 exacts
    hi = (npos + 1.0) / (npos + 2.0)
    lo = 1.0 / (nneg + 2.0)
    cibles = [hi if yi > 0.5 else lo for yi in y]
    w, b = _regression_logistique([[si] for si in s], cibles, 1)
    return CalibrateurPlatt(w[0], b)


class CalibrateurHistogramme:
    """Histogram binning : probabilité = fréquence empirique du casier de score."""

    __slots__ = ("bornes", "valeurs", "globale")

    def __init__(self, bornes, valeurs, globale):
        self.bornes = bornes          # bornes hautes des casiers
        self.valeurs = valeurs
        self.globale = globale

    def applique(self, score):
        i = bisect.bisect_right(self.bornes, float(score))
        if i >= len(self.valeurs):
            i = len(self.valeurs) - 1
        v = self.valeurs[i]
        return v if v is not None else self.globale


def ajuste_histogramme(scores, labels, n_casiers=10):
    s = [float(v) for v in scores]
    y = [1.0 if v else 0.0 for v in labels]
    n = len(s)
    if n < N_MIN_CAL:
        return None
    sommes = [0.0] * n_casiers
    comptes = [0] * n_casiers
    for i in range(n):
        b = min(n_casiers - 1, int(s[i] * n_casiers))
        sommes[b] += y[i]
        comptes[b] += 1
    valeurs = [sommes[b] / comptes[b] if comptes[b] > 0 else None for b in range(n_casiers)]
    bornes = [(b + 1) / n_casiers for b in range(n_casiers - 1)]   # bornes internes pour bisect
    return CalibrateurHistogramme(bornes, valeurs, sum(y) / n)


class CalibrateurBeta:
    """Beta calibration : ln(p/(1−p)) = a·ln(s) − b·ln(1−s) + c (3 paramètres, gère l'asymétrie)."""

    __slots__ = ("a", "b", "c")

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def applique(self, score):
        s = _clip(float(score))
        z = self.a * math.log(s) - self.b * math.log(1.0 - s) + self.c
        return _sigmoid(z)


def ajuste_beta(scores, labels):
    s = [_clip(float(v)) for v in scores]
    y = [1.0 if v else 0.0 for v in labels]
    n = len(s)
    if n < N_MIN_CAL:
        return None
    feats = [[math.log(si), -math.log(1.0 - si)] for si in s]      # a·ln(s) + b·(−ln(1−s))
    w, c = _regression_logistique(feats, y, 2)
    return CalibrateurBeta(w[0], w[1], c)


def ajuste(scores, labels, methode="platt", **kw):
    """Fabrique unifiée : `methode` ∈ {platt, histogramme, beta}. Renvoie un calibrateur (.applique(score)) ou None."""
    if methode == "platt":
        return ajuste_platt(scores, labels)
    if methode == "histogramme":
        return ajuste_histogramme(scores, labels, kw.get("n_casiers", 10))
    if methode == "beta":
        return ajuste_beta(scores, labels)
    raise ValueError(f"méthode inconnue : {methode}")


if __name__ == "__main__":
    print("=== CALIBRATEURS PARAMÉTRIQUES ===\n")
    import random
    rng = random.Random(0)
    def sig(x):
        return 1.0 / (1.0 + math.exp(-x))
    sc, lb = [], []
    for _ in range(2000):
        z = rng.uniform(-3, 3)
        lb.append(1 if rng.random() < sig(z) else 0)
        sc.append(sig(2.5 * z))     # sur-confiant
    for m in ("platt", "histogramme", "beta"):
        c = ajuste(sc, lb, m)
        print(f"  {m:12} : score 0.95 -> {c.applique(0.95):.3f} ; 0.05 -> {c.applique(0.05):.3f}")
