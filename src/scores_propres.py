"""
PALIER 2 — RÈGLES DE SCORE PROPRES & CLASSEMENT DE FORECASTERS (brique 10, 2026-06-25).

calibration.py dit SI un forecaster est calibré. Ici on MESURE et on COMPARE la qualité globale de forecasters
probabilistes avec des RÈGLES DE SCORE PROPRES — des scores minimisés EN ESPÉRANCE par la VRAIE probabilité
(« properness ») : annoncer autre chose que sa croyance honnête coûte plus cher. C'est l'incitation mathématique à
la sincérité, et l'instrument pour CLASSER des forecasters (le meilleur = le plus honnête-et-précis).

  • log_loss   — entropie croisée binaire : −moy[ y·ln p + (1−y)·ln(1−p) ]. Propre. Punit DUREMENT la sur-confiance fausse.
  • brier      — moy[ (p − y)² ]. Propre, borné [0,1].
  • crps       — Continuous Ranked Probability Score (forecast = ÉCHANTILLON) : moy[ E|X−y| − ½E|X−X'| ]. Propre,
    pour les prévisions à VALEUR RÉELLE ; récompense la justesse ET la dispersion calibrée (punit le trop-étroit).
  • score_spherique — récompense propre (plus haut = mieux), bornée.
  • classe_forecasters — range des forecasters par une règle propre (le calibré/vrai gagne en espérance).

Décomposition : log-loss/Brier = CALIBRATION + RAFFINEMENT. Un bon score exige les DEUX (être calibré ne suffit pas
si on est vague). C'est le complément naturel de calibration.py.
"""
from __future__ import annotations

import math

_EPS = 1e-15


def _pairs(probas, issues):
    p = [float(v) for v in probas]
    y = [1.0 if v else 0.0 for v in issues]
    if len(p) != len(y):
        raise ValueError(f"probas ({len(p)}) et issues ({len(y)}) de tailles différentes")
    if not p:
        raise ValueError("aucune donnée")
    return p, y


def log_loss(probas, issues) -> float:
    """Entropie croisée binaire (proba de la classe positive). Propre. 0 = parfait. Probas clampées loin de 0/1
    (anti-log(0)) UNIQUEMENT ici : un « 100 % » faux est puni fortement mais reste fini."""
    p, y = _pairs(probas, issues)
    p = [min(1.0 - _EPS, max(_EPS, v)) for v in p]
    return -sum(y[i] * math.log(p[i]) + (1 - y[i]) * math.log(1 - p[i]) for i in range(len(p))) / len(p)


def brier(probas, issues) -> float:
    """Score de Brier d'un forecast de proba P(y=1) : moyenne de (p − y)². Propre, borné [0,1]."""
    p, y = _pairs(probas, issues)
    return sum((p[i] - y[i]) ** 2 for i in range(len(p))) / len(p)


def score_spherique(probas, issues) -> float:
    """Score sphérique (RÉCOMPENSE propre, plus haut = mieux) : moy[ (y·p + (1−y)(1−p)) / sqrt(p² + (1−p)²) ]."""
    p, y = _pairs(probas, issues)
    s = 0.0
    for i in range(len(p)):
        proba_observee = y[i] * p[i] + (1 - y[i]) * (1 - p[i])
        s += proba_observee / math.sqrt(p[i] ** 2 + (1 - p[i]) ** 2)
    return s / len(p)


def crps(echantillons, verites) -> float:
    """CRPS moyen pour des prévisions à valeur réelle données par ÉCHANTILLON. `echantillons` = liste (un par cas)
    d'échantillons prédictifs (liste de valeurs) ; `verites` = vraie valeur de chaque cas. Propre, ≥ 0, 0 = parfait
    (Dirac sur la vérité). Pour un point unique, CRPS = |prévision − vérité| (MAE). Punit la sous-dispersion."""
    if len(echantillons) != len(verites):
        raise ValueError("echantillons et verites de tailles différentes")
    if not echantillons:
        raise ValueError("aucune donnée")
    tot = 0.0
    for ech, y in zip(echantillons, verites):
        xs = [float(v) for v in ech]
        m = len(xs)
        if m == 0:
            raise ValueError("échantillon vide")
        y = float(y)
        terme1 = sum(abs(x - y) for x in xs) / m
        if m == 1:
            tot += terme1
            continue
        # E|X−X'| via tri (O(m log m)) : Σ_{i<j}|x_i−x_j| = Σ_k (2k−m+1) x_(k)
        xs.sort()
        s = 0.0
        for k, x in enumerate(xs):
            s += (2 * k - m + 1) * x
        terme2 = (2.0 * s) / (m * m)        # = (1/m²)·Σ_{i,j}|x_i−x_j|
        tot += terme1 - 0.5 * terme2
    return tot / len(echantillons)


def classe_forecasters(sorties, issues, regle: str = "log_loss"):
    """Classe des forecasters PROBABILISTES par une règle propre. `sorties` = dict {nom: liste_de_probas}.
    Renvoie une liste [(nom, score)] triée du MEILLEUR au pire. `regle` ∈ {log_loss, brier} (pertes : plus bas = mieux)
    ou 'spherique' (récompense : plus haut = mieux). Le forecaster honnête-et-précis arrive en tête (properness)."""
    f = {"log_loss": log_loss, "brier": brier, "spherique": score_spherique}[regle]
    scores = [(nom, f(probas, issues)) for nom, probas in sorties.items()]
    scores.sort(key=lambda t: t[1], reverse=(regle == "spherique"))
    return scores


if __name__ == "__main__":
    print("=== SCORES PROPRES & CLASSEMENT ===\n")
    import random
    rng = random.Random(0)
    q = [rng.random() for _ in range(4000)]
    y = [1 if rng.random() < qi else 0 for qi in q]
    def durcis(p, k):
        return p ** k / (p ** k + (1 - p) ** k)
    sorties = {"calibré": q,
               "sur-confiant": [durcis(p, 3) for p in q],
               "sous-confiant": [durcis(p, 0.4) for p in q],
               "ignorant (0.5)": [0.5] * len(q)}
    for nom, s in classe_forecasters(sorties, y, "log_loss"):
        print(f"  log-loss {nom:16} = {s:.4f}")
    print("  CRPS (sample) trop étroit vs calibré :")
    cal = [[rng.gauss(0, 1) for _ in range(50)] for _ in range(2000)]
    etroit = [[rng.gauss(0, 0.3) for _ in range(50)] for _ in range(2000)]
    vt = [rng.gauss(0, 1) for _ in range(2000)]
    print(f"    calibré={crps(cal, vt):.3f}  trop_étroit={crps(etroit, vt):.3f}")
