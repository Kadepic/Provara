"""
PROFILAGE & COMPLEXITÉ EMPIRIQUE — mesurer le coût réel d'un code (brique code avancé, 2026-07-02).

POURQUOI : « code propre » inclut la PERFORMANCE — démasquer un code accidentellement quadratique/exponentiel. On
mesure le coût RÉEL (opérations comptées, mémoire, temps) et on infère la CLASSE de croissance en observant comment
le coût évolue quand la taille de l'entrée double.

FAUX=0 :
  • La classification se fait sur un coût DÉTERMINISTE (nombre d'opérations comptées, ou pic mémoire) — PAS le temps
    mur (bruité, non reproductible). Ainsi le verdict est reproductible.
  • On ne rend une classe (constante/log/linéaire/quasi-linéaire/quadratique/cubique/exponentielle) QUE si les
    exposants empiriques sont COHÉRENTS entre doublements ; sinon INDETERMINE (abstention honnête, jamais une classe
    inventée sur des mesures incohérentes).
  • `mesure_temps` / `mesure_memoire` sont des utilitaires FACTUELS (valeurs réelles), séparés du verdict de classe.
Stdlib pur (time/tracemalloc/statistics), souverain.
"""
from __future__ import annotations

import math
import statistics
import time
import tracemalloc

CONSTANTE = "constante"
LOG = "logarithmique"
LINEAIRE = "lineaire"                # inclut n·log n : empiriquement indistinguable du linéaire sur une plage bornée
QUADRATIQUE = "quadratique"
CUBIQUE = "cubique"
EXPONENTIELLE = "exponentielle"
INDETERMINE = "indetermine"


def mesure_temps(fn, arg, repetitions: int = 5) -> float:
    """Temps d'exécution MÉDIAN (secondes) — factuel, robuste au bruit par la médiane. Non utilisé pour la classe."""
    ts = []
    for _ in range(max(1, repetitions)):
        t0 = time.perf_counter()
        fn(arg)
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts)


def mesure_memoire(fn, arg) -> int:
    """Pic mémoire alloué (octets) pendant l'exécution, via tracemalloc — déterministe pour un algo donné."""
    tracemalloc.start()
    try:
        fn(arg)
        _, pic = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return pic


def _exposants(tailles, couts):
    """Exposants empiriques locaux : log(cout_ratio)/log(taille_ratio) entre points consécutifs."""
    exps = []
    for i in range(len(tailles) - 1):
        n1, n2 = tailles[i], tailles[i + 1]
        c1, c2 = couts[i], couts[i + 1]
        if n2 <= n1 or c1 <= 0 or c2 <= 0:
            continue
        exps.append(math.log(c2 / c1) / math.log(n2 / n1))
    return exps


def classe_croissance(tailles, couts) -> str:
    """Classe empirique de croissance à partir de (taille -> coût DÉTERMINISTE croissant). Abstention (INDETERMINE)
    si trop peu de points, coûts non croissants globalement, ou exposants incohérents (croissance exponentielle
    détectée à part : les exposants EXPLOSENT avec n)."""
    if len(tailles) < 3 or len(tailles) != len(couts):
        return INDETERMINE
    if any(c < 0 for c in couts):
        return INDETERMINE
    # coût quasi constant -> constante (avant toute division)
    if max(couts) <= 0 or (max(couts) - min(couts)) <= 0.05 * max(1, max(couts)):
        return CONSTANTE
    exps = _exposants(tailles, couts)
    if len(exps) < 2:
        return INDETERMINE
    # EXPONENTIELLE : l'exposant empirique CROÎT de façon MONOTONE et explose (plus vite que tout polynôme).
    # La monotonie est le garde FAUX=0 : du BRUIT a un dernier exposant élevé mais NON monotone -> écarté.
    croissant = all(exps[i + 1] >= exps[i] for i in range(len(exps) - 1))
    if croissant and exps[-1] > 4.0 and exps[-1] > exps[0] * 1.5:
        return EXPONENTIELLE
    # sinon, exposants doivent être COHÉRENTS (faible dispersion) pour conclure à un polynôme ; sinon abstention.
    moy = statistics.mean(exps)
    if statistics.pstdev(exps) > 0.5:
        return INDETERMINE                       # mesures incohérentes (bruit) -> abstention honnête
    if moy < 0.15:
        return CONSTANTE
    if moy < 0.6:
        return LOG
    if moy < 1.4:
        return LINEAIRE                           # inclut n·log n (exposant empirique ~1.1-1.3)
    if moy < 2.5:
        return QUADRATIQUE
    if moy < 3.5:
        return CUBIQUE
    return INDETERMINE                           # exposant élevé mais non exponentiel net -> prudence
