"""
PALIER 2 — PRÉVISION TEMPORELLE AVEC INTERVALLE DE PRÉDICTION (brique 30, 2026-06-25).

Prévoir « la prochaine valeur » d'une série = un sujet non-borné par excellence : le futur n'est pas encore déterminé.
L'honnêteté = un point + un INTERVALLE DE PRÉDICTION calibré, jamais une fausse précision. Méthode model-free :

  1. TENDANCE : régression linéaire de y sur le temps (pente + ordonnée).
  2. SAISONNALITÉ (optionnelle, période m) : moyenne des résidus détendus par phase.
  3. INTERVALLE : résidus une-étape-en-avant (hold-out temporel : on rejoue la prévision à chaque pas avec SEULEMENT
     le passé) -> quantile conforme de |résidus| -> point ± q. Couvre la vraie prochaine valeur ~`confiance`.

Le hold-out temporel (prévision à 1 pas rejouée sur l'historique) donne des résidus HONNÊTES (hors-échantillon),
donc une couverture calibrée et NON sur-confiante (vs des résidus in-sample, trop optimistes). INVARIANT jugé par
calibration.py. ABSTENTION si série trop courte. Pur Python.
"""
from __future__ import annotations

import conformal as _CF

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 12


def _ols(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    pente = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den if den > 0 else 0.0
    ord_ = my - pente * mx
    return pente, ord_


def _saison(residus, periode):
    """Moyenne des résidus par phase (0..periode-1)."""
    s = [0.0] * periode
    c = [0] * periode
    for i, r in enumerate(residus):
        s[i % periode] += r
        c[i % periode] += 1
    return [s[p] / c[p] if c[p] else 0.0 for p in range(periode)]


def _prevoit_un(serie, periode):
    """Prévision 1-pas À PARTIR de `serie` (passé seul). Renvoie le point prédit pour l'indice len(serie)."""
    n = len(serie)
    xs = list(range(n))
    pente, ord_ = _ols(xs, serie)
    pred_tendance = ord_ + pente * n
    if periode and n >= 2 * periode:
        residus = [serie[i] - (ord_ + pente * i) for i in range(n)]
        sa = _saison(residus, periode)
        return pred_tendance + sa[n % periode]
    return pred_tendance


def prevoit(serie, periode=None, confiance=0.90):
    """Prévoit la PROCHAINE valeur de `serie` + intervalle de prédiction calibré. Renvoie
    (ESTIMATION, (point, (bas, haut)), confiance) ou ABSTENTION. `periode` = saisonnalité (ex. 7, 12) ou None."""
    y = [float(v) for v in serie]
    n = len(y)
    if n < N_MIN:
        return (ABSTENTION, None, f"série trop courte (n={n} < {N_MIN})")
    # résidus une-étape-en-avant en rejouant la prévision sur l'historique (hold-out temporel)
    debut = max(4, (2 * periode) if periode else 4)
    residus = []
    for t in range(debut, n):
        pred = _prevoit_un(y[:t], periode)
        residus.append(abs(y[t] - pred))
    if len(residus) < 8:
        return (ABSTENTION, None, f"trop peu de résidus hold-out (n={len(residus)}) pour calibrer l'intervalle")
    q = _CF.quantile_conforme(residus, 1.0 - confiance)
    if q is None:
        return (ABSTENTION, None, "pas assez de résidus pour le niveau demandé")
    point = _prevoit_un(y, periode)
    return (ESTIMATION, (point, (point - q, point + q)), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas prévoir : {res[2]}."
    point, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Je prévois ~{point:.2f} pour la prochaine valeur, mais le futur est incertain : à {round(conf*100)}% "
            f"elle tombera entre {bas:.2f} et {haut:.2f}.")


if __name__ == "__main__":
    print("=== PRÉVISION TEMPORELLE ===\n")
    import random
    rng = random.Random(0)
    serie = [0.5 * t + 3 * ((t % 7) - 3) + rng.gauss(0, 1.5) for t in range(60)]   # tendance + saison 7 + bruit
    print(" ", formule(prevoit(serie, periode=7, confiance=0.90)))
    print(" ", formule(prevoit(serie[:5])))   # trop court
