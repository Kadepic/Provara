"""
PALIER 2 — PRÉDICTION CONFORME (brique 3, 2026-06-25).

La garantie de couverture la plus PROPRE du non-borné : un ensemble/intervalle prédit contient la vraie réponse
AU MOINS (1−α) du temps, SANS AUCUNE hypothèse de loi — seulement l'ÉCHANGEABILITÉ des données (calibration et
test tirées du même processus, ordre indifférent). C'est l'incarnation directe de l'invariant : la couverture est
GARANTIE par construction, jamais sur-confiante (au pire trop prudente d'un cran fini).

Mécanisme (split conformal) : sur un jeu de CALIBRATION dont on connaît la vérité, on mesure un SCORE DE NON-CONFORMITÉ
par point (régression : |y − ŷ| ; classification : 1 − p_vraie_classe). Le quantile conforme
    q = score trié à l'indice  ⌈(n+1)(1−α)⌉
borne la non-conformité du futur point avec proba ≥ 1−α. D'où :
  • RÉGRESSION : intervalle = (prédiction − q, prédiction + q).
  • CLASSIFICATION : ensemble = { classes dont la non-conformité ≤ q } (peut être vide, singleton, ou multiple).

ABSTENTION HONNÊTE : si ⌈(n+1)(1−α)⌉ > n (trop peu de points de calibration pour garantir ce niveau), on ne fabrique
PAS d'intervalle fini -> abstention (ex. : 90 % exige n ≥ 9 ; 99 % exige n ≥ 99).

PUISSANCE vs incertitude.py : `predit_intervalle` (quantiles empiriques) suppose les données i.i.d. et peut sous-couvrir
si le modèle de moyenne est biaisé. Le conforme couvre MÊME avec un modèle MAL SPÉCIFIÉ ou un bruit asymétrique/lourd
(prouvé dans valide_conformal.py). C'est sa raison d'être.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
ENSEMBLE = "ensemble"


def _indice_quantile(n, alpha):
    """Indice (1-based) du score conforme, ou None si trop peu de points pour garantir 1−α."""
    k = math.ceil((n + 1) * (1.0 - alpha))
    if k > n:
        return None
    return k


def quantile_conforme(scores, alpha=0.1):
    """Quantile conforme d'une liste de scores de non-conformité (≥ 0), ou None (abstention) si n trop petit
    pour le niveau demandé. C'est la borne q telle que P(score_futur ≤ q) ≥ 1−α sous échangeabilité."""
    s = sorted(float(x) for x in scores)
    n = len(s)
    if n == 0:
        return None
    k = _indice_quantile(n, alpha)
    if k is None:
        return None
    return s[k - 1]


def intervalle_conforme(residus_cal, prediction, alpha=0.1):
    """INTERVALLE conforme pour une RÉGRESSION : à partir des résidus de calibration (idéalement |y−ŷ| en valeur
    absolue), renvoie (ESTIMATION, (bas, haut), 1−α) garantissant une couverture ≥ 1−α, ou ABSTENTION si trop peu
    de points. `residus_cal` peut être signé : on prend la valeur absolue (score symétrique)."""
    scores = [abs(float(r)) for r in residus_cal]
    q = quantile_conforme(scores, alpha)
    if q is None:
        n = len(scores)
        return (ABSTENTION, None, f"trop peu de points de calibration (n={n}) pour garantir {round((1-alpha)*100)}%")
    p = float(prediction)
    return (ESTIMATION, (p - q, p + q), 1.0 - alpha)


def ensemble_conforme(probas_vraie_cal, probas_test, alpha=0.1):
    """ENSEMBLE conforme pour une CLASSIFICATION. `probas_vraie_cal` = liste des probabilités attribuées à la VRAIE
    classe sur le jeu de calibration (score de non-conformité = 1 − p). `probas_test` = dict {classe: proba} pour
    le point à prédire. Renvoie (ENSEMBLE, set_de_classes, 1−α) — le vrai label y est dedans ≥ 1−α du temps — ou
    ABSTENTION si trop peu de calibration. L'ensemble peut être VIDE (signal d'incertitude forte) ou MULTIPLE."""
    scores = [1.0 - float(p) for p in probas_vraie_cal]
    q = quantile_conforme(scores, alpha)
    if q is None:
        return (ABSTENTION, None, f"trop peu de points de calibration (n={len(scores)}) pour garantir {round((1-alpha)*100)}%")
    retenues = {c for c, p in probas_test.items() if (1.0 - float(p)) <= q}
    return (ENSEMBLE, retenues, 1.0 - alpha)


def formule(res, quoi="intervalle") -> str:
    """Parole honnête d'une prédiction conforme. `quoi` ∈ {intervalle, ensemble}."""
    statut = res[0]
    if statut == ABSTENTION:
        return f"Je préfère ne pas me prononcer : {res[2]}."
    if quoi == "ensemble":
        _, classes, conf = res
        pct = round(conf * 100)
        if not classes:
            return (f"Aucune classe n'est assez plausible pour mon seuil de {pct}% — je signale une incertitude forte "
                    "plutôt que de deviner.")
        if len(classes) == 1:
            return f"La réponse est {next(iter(classes))} (avec une garantie de couverture de {pct}%)."
        return (f"Je n'arrive pas à trancher : la vraie réponse est dans {{{', '.join(map(str, sorted(map(str, classes))))}}} "
                f"avec une garantie de {pct}% — je préfère donner cet ensemble honnête qu'un seul nom trop sûr.")
    _, (bas, haut), conf = res
    pct = round(conf * 100)
    return (f"La vraie valeur est entre {bas:.2f} et {haut:.2f} avec une garantie de couverture de {pct}% "
            "(sans hypothèse sur la loi des données).")


if __name__ == "__main__":
    print("=== PRÉDICTION CONFORME ===\n")
    import random
    rng = random.Random(0)
    residus = [abs(rng.gauss(0, 2)) for _ in range(200)]
    print(" ", formule(intervalle_conforme(residus, 10.0, 0.1), "intervalle"))
    print(" ", formule(intervalle_conforme([1, 2], 10.0, 0.1), "intervalle"))      # trop peu -> abstention
    proba_vraie = [rng.random() ** 0.5 for _ in range(200)]
    print(" ", formule(ensemble_conforme(proba_vraie, {"chat": 0.7, "chien": 0.2, "oiseau": 0.1}, 0.1), "ensemble"))
    print(" ", formule(ensemble_conforme(proba_vraie, {"chat": 0.4, "chien": 0.35, "oiseau": 0.25}, 0.1), "ensemble"))
