"""
PALIER 2 — TEMPERATURE SCALING (brique 19, 2026-06-25). La recalibration multi-classe MINIMALE.

Pour un classifieur multi-classe (réseau, modèle…) qui crache des LOGITS sur-confiants, la méthode standard et la plus
sobre : diviser les logits par une TEMPÉRATURE T > 0 avant le softmax —

    p_c = softmax(z_c / T)

UN SEUL paramètre, appris en minimisant la log-vraisemblance négative sur un jeu de calibration. T > 1 ADOUCIT
(réduit la sur-confiance), T < 1 durcit. PROPRIÉTÉ CLÉ : T ne change pas l'ordre des classes -> l'ARGMAX et donc la
JUSTESSE sont PRÉSERVÉS ; on ne corrige QUE la confiance. Robuste (1 paramètre = pas d'overfit), rapide.

INVARIANT (jugé par calibration.py) : sur un classifieur sur-confiant, T̂ > 1, l'ECE top-label chute hors-échantillon,
la justesse est inchangée. Si on n'a que des probabilités (pas de logits), on prend log(p) comme logits. ABSTENTION si
trop peu de données. Model-free, pur Python.
"""
from __future__ import annotations

import math

N_MIN_CAL = 30
_EPS = 1e-12


def softmax_temp(logits, T):
    """softmax(logits / T) -> dict {classe: proba}. `logits` = dict {classe: logit}."""
    m = max(logits.values())
    exp = {c: math.exp((z - m) / T) for c, z in logits.items()}
    s = sum(exp.values())
    return {c: e / s for c, e in exp.items()}


def logits_depuis_probas(probas):
    """Convertit un dict de probabilités en logits (log p, à une constante près) — pour appliquer la température
    quand on n'a pas les logits bruts."""
    return {c: math.log(max(_EPS, float(p))) for c, p in probas.items()}


def _nll(logits_list, labels, T):
    s = 0.0
    for lg, y in zip(logits_list, labels):
        p = softmax_temp(lg, T)
        s -= math.log(max(_EPS, p[y]))
    return s / len(labels)


class TemperatureScaling:
    __slots__ = ("T",)

    def __init__(self, T):
        self.T = T

    def applique(self, logits):
        """Probabilités calibrées (dict) pour un vecteur de logits (dict {classe: logit})."""
        return softmax_temp(logits, self.T)

    def applique_probas(self, probas):
        """Variante : recalibre à partir de PROBABILITÉS (converties en logits log p)."""
        return softmax_temp(logits_depuis_probas(probas), self.T)


def ajuste_temperature(logits_list, labels, bornes=(0.05, 20.0)):
    """Apprend T en minimisant la NLL par recherche en section dorée (NLL unimodale en T). `logits_list` = liste de
    dict {classe: logit} ; `labels` = vraie classe. Renvoie un TemperatureScaling ou None si trop peu de données."""
    if len(labels) < N_MIN_CAL:
        return None
    lo, hi = bornes
    phi = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c = b - phi * (b - a)
    d = a + phi * (b - a)
    fc = _nll(logits_list, labels, c)
    fd = _nll(logits_list, labels, d)
    for _ in range(60):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - phi * (b - a)
            fc = _nll(logits_list, labels, c)
        else:
            a, c, fc = c, d, fd
            d = a + phi * (b - a)
            fd = _nll(logits_list, labels, d)
    return TemperatureScaling((a + b) / 2)


def formule(ts) -> str:
    if ts.T > 1.05:
        return f"Température T={ts.T:.2f} > 1 : le modèle était SUR-confiant, j'ai adouci ses probabilités (sans changer ses choix)."
    if ts.T < 0.95:
        return f"Température T={ts.T:.2f} < 1 : le modèle était SOUS-confiant, j'ai renforcé ses probabilités."
    return f"Température T={ts.T:.2f} ≈ 1 : le modèle était déjà à peu près calibré."


if __name__ == "__main__":
    print("=== TEMPERATURE SCALING ===\n")
    import random
    rng = random.Random(0)
    classes = ["A", "B", "C"]
    lg, lab = [], []
    for _ in range(1500):
        z = {c: rng.gauss(0, 1.5) for c in classes}
        p = softmax_temp(z, 1.0)
        u = rng.random(); cum = 0; y = classes[-1]
        for c in classes:
            cum += p[c]
            if u < cum:
                y = c; break
        lg.append({c: z[c] * 3.0 for c in classes})    # logits ×3 = sur-confiant
        lab.append(y)
    ts = ajuste_temperature(lg, lab)
    print(" ", formule(ts))
    print("  ex brut :", {c: round(softmax_temp(lg[0], 1.0)[c], 2) for c in classes})
    print("  ex calib:", {c: round(ts.applique(lg[0])[c], 2) for c in classes})
