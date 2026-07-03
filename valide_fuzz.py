"""
Validation de la BRIQUE 6 (le crible sécurité / fuzzing différentiel).

Critère de la brique :
  1. une solution robuste et correcte -> ROBUSTE ;
  2. une solution qui CRASHE sur des entrées aberrantes (liste vide/singleton)
     -> CRASH — ALORS MÊME QU'ELLE PASSE LES TESTS (la démonstration VERAX :
     "passe les tests" ≠ "survit au réel") ;
  3. une solution subtilement FAUSSE sur du non-vu -> DIVERGENCE ;
  4. une tâche sans oracle/générateur -> INCRIBLABLE (pas de faux "tout va bien").
"""

from __future__ import annotations

import dataclasses

from fuzz import CRASH, DIVERGENCE, INCRIBLABLE, ROBUSTE, crible
from juge import Limites, juge
from taches import HUMANEVAL_0 as t


# Robuste et correcte (double boucle) : survit à tout.
ROBUSTE_OK = t.solution_ref

# Passe les tests visibles (toutes les listes y ont >= 2 éléments) MAIS min([])
# plante sur liste vide / singleton -> fragile. C'est le cas VERAX.
MIN_FRAGILE = '''
from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    paires = [abs(a - b) for i, a in enumerate(numbers)
              for j, b in enumerate(numbers) if i < j]
    return min(paires) < threshold
'''

# Ne compare que les éléments ADJACENTS -> rate les paires proches non adjacentes.
ADJACENT_FAUX = '''
from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return True
    return False
'''


def _check(nom: str, condition: bool) -> bool:
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    lim = Limites(temps_s=5, cpu_s=4)

    # 1. Robuste correcte.
    r = crible(t, ROBUSTE_OK, n_essais=300, seed=0, limites=lim)
    resultats.append(_check(f"solution robuste -> ROBUSTE (vu: {r.type_faille})",
                            r.robuste and r.type_faille == ROBUSTE))

    # 2. Le cas VERAX : passe le juge, mais le crible trouve un CRASH.
    passe_juge = juge(MIN_FRAGILE, t.tests, lim).passe
    resultats.append(_check("min-fragile PASSE pourtant les tests visibles (pré-condition)", passe_juge))
    r = crible(t, MIN_FRAGILE, n_essais=300, seed=0, limites=lim)
    resultats.append(_check(f"min-fragile -> CRASH au fuzz, malgré les tests (vu: {r.type_faille})",
                            (not r.robuste) and r.type_faille == CRASH))
    print(f"        contre-exemple : ...{r.detail[-120:]}")

    # 3. Subtilement faux sur du non-vu.
    r = crible(t, ADJACENT_FAUX, n_essais=300, seed=0, limites=lim)
    resultats.append(_check(f"adjacent-faux -> DIVERGENCE (vu: {r.type_faille})",
                            (not r.robuste) and r.type_faille == DIVERGENCE))
    print(f"        contre-exemple : ...{r.detail[-120:]}")

    # 4. Tâche non criblable (sans oracle/générateur) -> on le dit honnêtement.
    tache_nue = dataclasses.replace(t, solution_ref="", gen_entrees="")
    r = crible(tache_nue, ROBUSTE_OK, n_essais=50, limites=lim)
    resultats.append(_check(f"tâche sans oracle -> INCRIBLABLE (vu: {r.type_faille})",
                            r.type_faille == INCRIBLABLE))

    print()
    if all(resultats):
        print(f"BRIQUE 6 VALIDÉE — {len(resultats)}/{len(resultats)}. "
              f"\"Passe les tests\" ne suffit pas : le crible exige de survivre au réel.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
