"""
PALIER 2 — INFÉRENCE CAUSALE SOUS INCERTITUDE (ATE, brique 31, 2026-06-25).

« Le traitement CAUSE-t-il un effet, et de combien ? » est non-borné : l'effet existe mais on n'observe jamais le
contrefactuel (la même unité traitée ET non traitée). On l'estime avec une incertitude honnête — et on REFUSE le piège
classique : sous CONFUSION (un facteur influence à la fois le traitement et le résultat), la simple différence de
moyennes est BIAISÉE (elle mélange l'effet causal et le confondant).

  • Essai RANDOMISÉ : ATE = moyenne(traités) − moyenne(contrôles), IC par bootstrap. Sans biais (la randomisation
    casse la confusion).
  • Observationnel : IPW (Inverse Probability Weighting) — on pondère chaque unité par 1/P(son traitement | X) pour
    recréer une pseudo-population équilibrée. ATE_IPW = (1/n)[Σ_traités y/e − Σ_contrôles y/(1−e)], IC par bootstrap.
    Corrige la confusion SI le score de propension e(X) est correct (hypothèse explicite).

INVARIANT (jugé par calibration.py) : l'IC de l'estimateur APPROPRIÉ couvre le vrai ATE ~confiance ; la différence
NAÏVE sous confusion sous-couvre (SURCONFIANT, car centrée sur une valeur biaisée). ABSTENTION si trop peu / propension
dégénérée (proche de 0/1 = pas de support commun). Pur Python.
"""
from __future__ import annotations

import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 10


def _ic_bootstrap(echantillon_estimateur, confiance):
    vals = sorted(echantillon_estimateur)
    n = len(vals)
    a = (1.0 - confiance) / 2.0
    return (vals[int(a * n)], vals[min(n - 1, int((1.0 - a) * n))])


def ate_diff_moyennes(y_traites, y_controles, confiance=0.90, n_boot=2000, seed=0):
    """ATE par différence de moyennes (valide pour un essai RANDOMISÉ). Renvoie (ESTIMATION, (ate, (bas, haut)),
    confiance) ou ABSTENTION."""
    a = [float(v) for v in y_traites]
    b = [float(v) for v in y_controles]
    if len(a) < N_MIN or len(b) < N_MIN:
        return (ABSTENTION, None, f"trop peu d'unités (n<{N_MIN})")
    ate = sum(a) / len(a) - sum(b) / len(b)
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        sa = sum(a[rng.randrange(len(a))] for _ in range(len(a))) / len(a)
        sb = sum(b[rng.randrange(len(b))] for _ in range(len(b))) / len(b)
        boot.append(sa - sb)
    return (ESTIMATION, (ate, _ic_bootstrap(boot, confiance)), confiance)


def _ipw_point(y, t, e):
    n = len(y)
    s1 = sum(y[i] * t[i] / e[i] for i in range(n))
    s0 = sum(y[i] * (1 - t[i]) / (1.0 - e[i]) for i in range(n))
    return (s1 - s0) / n


def ate_ipw(y, traitement, propension, confiance=0.90, n_boot=2000, seed=0):
    """ATE par IPW (observationnel). `y` = résultats, `traitement` = 0/1, `propension` = e(X)=P(T=1|X) ∈ (0,1).
    Renvoie (ESTIMATION, (ate, (bas, haut)), confiance) ou ABSTENTION (propension dégénérée = pas de support commun)."""
    y = [float(v) for v in y]
    t = [1 if v else 0 for v in traitement]
    e = [float(v) for v in propension]
    n = len(y)
    if n < N_MIN:
        return (ABSTENTION, None, f"trop peu d'unités (n<{N_MIN})")
    if any(ei <= 0.02 or ei >= 0.98 for ei in e):
        return (ABSTENTION, None, "propension proche de 0/1 (pas de support commun) : estimation non fiable")
    ate = _ipw_point(y, t, e)
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        yy = [y[i] for i in idx]; tt = [t[i] for i in idx]; ee = [e[i] for i in idx]
        boot.append(_ipw_point(yy, tt, ee))
    return (ESTIMATION, (ate, _ic_bootstrap(boot, confiance)), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer l'effet causal : {res[2]}."
    ate, (bas, haut), conf = res[1][0], res[1][1], res[2]
    if bas > 0 or haut < 0:
        sens = "un effet POSITIF" if ate > 0 else "un effet NÉGATIF"
        return f"J'estime {sens} (ATE ≈ {ate:.3f}, à {round(conf*100)}% entre {bas:.3f} et {haut:.3f})."
    return (f"Effet estimé ATE ≈ {ate:.3f} (à {round(conf*100)}% entre {bas:.3f} et {haut:.3f}), mais l'intervalle "
            "inclut 0 — je ne peux pas affirmer qu'il y a un effet.")


if __name__ == "__main__":
    print("=== INFÉRENCE CAUSALE (ATE) ===\n")
    import random as _r
    rng = _r.Random(0)
    # confusion : X ↑ -> plus traité ET meilleur résultat. Effet causal vrai = +2.
    y, t, e = [], [], []
    for _ in range(800):
        x = rng.gauss(0, 1)
        prop = 1 / (1 + pow(2.718281828, -x))      # propension dépend de X
        ti = 1 if rng.random() < prop else 0
        yi = 3 * x + 2 * ti + rng.gauss(0, 1)       # X confond, effet causal +2
        y.append(yi); t.append(ti); e.append(prop)
    yt = [y[i] for i in range(len(y)) if t[i] == 1]
    yc = [y[i] for i in range(len(y)) if t[i] == 0]
    print("  naïf (diff moyennes, BIAISÉ par X) :", formule(ate_diff_moyennes(yt, yc)))
    print("  IPW (corrige la confusion)         :", formule(ate_ipw(y, t, e)))
