"""
PLUS LONGUE SOUS-SUITE MONOTONE (DP/LIS) — sous-suite NON contiguë (front d'après, thème 4).

`GenerateurSousSuite` : DP O(n²) `dp[i]=1+max(dp[j] for j<i if xs[j] REL xs[i])`, REL ∈ {<,<=,>,>=}.
longest_increasing = `<` ; longest_decreasing = `>`. Distinct du run CONTIGU (serie).

Critères de MORT :
  1. MUR ×2          : ni `serie` (plus longue suite CONSÉCUTIVE) ni `adjacence` (paires voisines) ne mintent
                       longest_increasing (LIS saute des éléments : [1,3,2,4] -> 3, run contigu max = 2).
  2. GÉNÉRAL ×2      : `longest_increasing` (<) ET `longest_decreasing` (>) mintés + GÉNÉRALISENT au held-out
                       adverse (déjà triée, anti-triée, plateau d'égaux -> 1 en strict, singleton, vide -> 0).
  3. HONNÊTE         : ne masque PAS `nombre_elements` = len(xs) (coïncide sur suite triée, diverge sinon).
  4. VIVANT (modèle) : l'orchestrateur (sous_suite=True) résout longest_increasing à l'étage `sous-suite`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurAdjacence, GenerateurOrchestre, GenerateurSerie,
                        GenerateurSousSuite)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"ss/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


# REL `<` ; held-out adverse : triée -> len, anti-triée -> 1, plateau d'égaux -> 1 (strict), singleton, vide.
LIS = _t("longest_increasing",
    "def check(c):\n    assert c([1,3,2,4]) == 3\n    assert c([5,4,3]) == 1\ncheck(longest_increasing)",
    "def check(c):\n    assert c([1,2,3,4]) == 4\n    assert c([4,3,2,1]) == 1\n    assert c([1,3,2,4,3,5]) == 4\n    assert c([2,2,2]) == 1\n    assert c([10]) == 1\n    assert c([]) == 0\ncheck(longest_increasing)")

# REL `>` ; held-out adverse : décroissante -> len, croissante -> 1, plateau -> 1, mixte.
LDS = _t("longest_decreasing",
    "def check(c):\n    assert c([5,4,3]) == 3\n    assert c([1,2,3]) == 1\ncheck(longest_decreasing)",
    "def check(c):\n    assert c([3,1,2,1]) == 3\n    assert c([5,5,5]) == 1\n    assert c([9]) == 1\n    assert c([1,2,3,4]) == 1\ncheck(longest_decreasing)")

# tâche confusable : len(xs). COÏNCIDE sur suite triée (LIS=len) mais DIVERGE sinon -> le held-out le prouve.
NOMBRE_ELEMENTS = _t("nombre_elements",
    "def check(c):\n    assert c([1,2,3]) == 3\n    assert c([5]) == 1\ncheck(nombre_elements)",
    "def check(c):\n    assert c([3,1,2]) == 3\n    assert c([4,3,2,1]) == 4\ncheck(nombre_elements)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_gen(gen, tache, n=400):
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out
                                                    or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    resultats = []
    ss = GenerateurSousSuite()

    resultats.append(_check(
        "MUR ×2 : ni `serie` (run CONSÉCUTIF) ni `adjacence` (paires voisines) ne mintent longest_increasing (LIS saute)",
        _resout_gen(GenerateurSerie(), LIS) is None and _resout_gen(GenerateurAdjacence(), LIS) is None))

    g1 = _resout_gen(ss, LIS)
    g2 = _resout_gen(ss, LDS)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `longest_increasing` (<) ET `longest_decreasing` (>) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : ne masque PAS `nombre_elements` = len(xs) (coïncide trié, diverge sinon -> held-out le tue)",
        _resout_gen(ss, NOMBRE_ELEMENTS) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), sous_suite=True)
        etage, _, code, _ = resoudre(orch, LIS, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (sous_suite=True) résout longest_increasing à l'étage `{etage}`",
        code is not None and etage == "sous-suite"))

    print()
    if all(resultats):
        print(f"SOUS-SUITE VALIDÉE — {len(resultats)}/{len(resultats)}. Plus longue sous-suite monotone (DP, non contiguë) : "
              f"longest_increasing ET longest_decreasing, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
