"""
ANALYSE STATISTIQUE (2026-06-17, faculté « analyse ») — médiane/mode/moyenne/écart. `GenerateurStatistiques`.

Critères de MORT (4) :
  1. MUR        : `comprehension-generale` (sum/max/min/count) ne minte pas la `mediane` (élément central trié, indice CALCULÉ).
  2. GÉNÉRAL ×2 : `mediane` ET `mode` (valeur la plus fréquente) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `somme_carres` (agrégat simple, pas une statistique).
  4. VIVANT    : l'orchestrateur (statistiques=True) résout `mediane` à l'étage `statistiques`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurOrchestre, GenerateurStatistiques
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"stat/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests, tests_held_out=held)


MEDIANE = _t("mediane",
    "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2,3]) == 3\ncheck(mediane)",
    "def check(c):\n    assert c([1,2]) == 2\n    assert c([9,7,8]) == 8\n    assert c([10,20,30]) == 20\n    assert c([100,5,50]) == 50\n    assert c([1,5,9]) == 5\n    assert c([2,4,6,8,10]) == 6\ncheck(mediane)")
MODE = _t("mode",
    "def check(c):\n    assert c([1,1,2]) == 1\n    assert c([3,3,3,1]) == 3\ncheck(mode)",
    "def check(c):\n    assert c([5,5,2,2,2]) == 2\n    assert c([7]) == 7\ncheck(mode)")
SOMME_CARRES = _t("somme_carres",
    "def check(c):\n    assert c([1,2,3]) == 14\ncheck(somme_carres)",
    "def check(c):\n    assert c([2,3]) == 13\ncheck(somme_carres)")


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def _resout(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    r = []
    st = GenerateurStatistiques()
    r.append(_check("MUR : `comprehension-generale` ne minte pas la `mediane` (indice calculé len//2)",
                    _resout(GenerateurComprehensionGenerale([]), MEDIANE) is None))
    r.append(_check("GÉNÉRAL ×2 : `mediane` ET `mode` mintés + held-out adverse",
                    _resout(st, MEDIANE) is not None and _resout(st, MODE) is not None))
    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (agrégat simple)", _resout(st, SOMME_CARRES) is None))
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), statistiques=True)
        e, _, code, _ = resoudre(orch, MEDIANE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (statistiques=True) résout `mediane` à l'étage `{e}`",
                    code is not None and e == "statistiques"))
    print()
    print("STATISTIQUES VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
