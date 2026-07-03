"""
PRÉDICAT STRUCTUREL sur MESURES — `m1(x) CMP m2(x)` (famille B : all_unique).

La carte a montré HORS-PORTÉE `all_unique` = len(xs) == len(set(xs)). Le branchement teste des prédicats donnés ;
il ne compare pas deux PROPRIÉTÉS agrégées de l'entrée. `GenerateurPredicatMesures` admet `m1(x) CMP m2(x)` (len,
len∘set, sum, max, min × ==,!=,>,<,>=,<=). Modulaire : couvre toute une classe de validations.

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (branchement)  : le branchement ne minte pas all_unique.
  2. PRÉDICAT-MESURES   : `all_unique` (len(x) == len(set(x))) minté + GÉNÉRALISE.
  3. GÉNÉRALITÉ         : `a_des_doublons` (len(x) != len(set(x))) aussi -> autre opérateur, schéma général.
  4. VIVANT (modèle)    : l'orchestrateur (predicat_mesures=True) résout all_unique à l'étage `predicat-mesures`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurBranche, GenerateurOrchestre, GenerateurPredicatMesures)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
EST_POS = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")


def _t(fn, tests, held):
    return Tache(id=f"pm/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


ALL_UNIQUE = _t("all_unique",
    "def check(c):\n    assert c([1,2,3]) is True\n    assert c([1,1]) is False\n    assert c([1,2,2]) is False\ncheck(all_unique)",
    "def check(c):\n    assert c([1,2,3,4]) is True\n    assert c([5,5,5]) is False\n    assert c([7]) is True\ncheck(all_unique)")
# 2e tâche RÉELLEMENT à deux mesures (len != len(set)), tests DURCIS pour tuer les coïncidences (ex. [2,2]).
A_DOUBLONS = _t("a_des_doublons",
    "def check(c):\n    assert c([1,1]) is True\n    assert c([2,2]) is True\n    assert c([1,2,3]) is False\n    assert c([5]) is False\ncheck(a_des_doublons)",
    "def check(c):\n    assert c([1,2,1]) is True\n    assert c([7,8,9,10]) is False\n    assert c([0,0]) is True\n    assert c([3,4]) is False\ncheck(a_des_doublons)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_gen(gen, tache, n=400):
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and juge(code, tache.tests_held_out, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []
    pm = GenerateurPredicatMesures()

    resultats.append(_check("MUR : le branchement (prédicats donnés) ne minte pas all_unique",
                            _resout_gen(GenerateurBranche([EST_POS]), ALL_UNIQUE) is None))

    g = _resout_gen(pm, ALL_UNIQUE)
    if g:
        print(f"    all_unique -> {g.strip().splitlines()[-1].strip()}")
    resultats.append(_check("PRÉDICAT-MESURES : `all_unique` (len(x) == len(set(x))) minté + généralise", g is not None))

    g2 = _resout_gen(pm, A_DOUBLONS)
    if g2:
        print(f"    a_des_doublons -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("GÉNÉRALITÉ : `a_des_doublons` (len(x) != len(set(x))) aussi minté (autre CMP -> schéma général)",
                            g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), predicat_mesures=True)
        etage, _, code, _ = resoudre(orch, ALL_UNIQUE, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (predicat_mesures=True) résout all_unique à l'étage `{etage}`",
        code is not None and etage == "predicat-mesures"))

    print()
    if all(resultats):
        print(f"PRÉDICAT-MESURES VALIDÉ — {len(resultats)}/{len(resultats)}. Comparer deux mesures agrégées de x : "
              f"all_unique (==) ET a_des_doublons (!=), held-out durci, honnête, utilisé par le modèle. "
              f"**Famille B complète** (invariant + prédicat-mesures).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
