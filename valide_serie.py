"""
PLUS LONGUE SÉRIE — run-length, état à travers la séquence (dernière niche du thème II).

`GenerateurSerie` admet un schéma stateful (best/cur) : la plus longue suite consécutive où une relation entre
voisins tient. plus_longue_serie = run de `==` ; plus_longue_croissante = run de `>`. Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (adjacence)   : l'adjacence (agrégat de paires, sans état) ne minte pas plus_longue_serie.
  2. SÉRIE (×2)        : `plus_longue_serie` (==) ET `plus_longue_croissante` (>) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle)   : l'orchestrateur (serie=True) résout plus_longue_serie à l'étage `serie`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurAdjacence, GenerateurOrchestre, GenerateurSerie
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"se/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


PLUS_LONGUE = _t("plus_longue_serie",
    "def check(c):\n    assert c([1,1,2,2,2,3]) == 3\n    assert c([5]) == 1\n    assert c([1,2,3]) == 1\ncheck(plus_longue_serie)",
    "def check(c):\n    assert c([4,4,4,4,1]) == 4\n    assert c([7,7,1,1]) == 2\ncheck(plus_longue_serie)")
PLUS_CROISSANTE = _t("plus_longue_croissante",
    "def check(c):\n    assert c([1,2,3,1,2]) == 3\n    assert c([5]) == 1\n    assert c([3,2,1]) == 1\ncheck(plus_longue_croissante)",
    "def check(c):\n    assert c([1,2,1,2,3,4]) == 4\n    assert c([9,8,7,6]) == 1\ncheck(plus_longue_croissante)")


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
    se = GenerateurSerie()

    resultats.append(_check("MUR : l'adjacence (agrégat de paires, sans état) ne minte pas plus_longue_serie",
                            _resout_gen(GenerateurAdjacence(), PLUS_LONGUE) is None))

    g1 = _resout_gen(se, PLUS_LONGUE)
    g2 = _resout_gen(se, PLUS_CROISSANTE)
    if g1:
        print(f"    plus_longue_serie      OK")
    resultats.append(_check("SÉRIE : `plus_longue_serie` (==) ET `plus_longue_croissante` (>) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), serie=True)
        etage, _, code, _ = resoudre(orch, PLUS_LONGUE, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (serie=True) résout plus_longue_serie à l'étage `{etage}`",
        code is not None and etage == "serie"))

    print()
    if all(resultats):
        print(f"SÉRIE VALIDÉE — {len(resultats)}/{len(resultats)}. La plus longue série consécutive (run-length, état) : "
              f"plus_longue_serie ET plus_longue_croissante, held-out, honnête, utilisé par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
