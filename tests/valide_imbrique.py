"""
DONNÉES IMBRIQUÉES — itérer deux niveaux (thème I : flatten).

L'escalade a confirmé HORS-PORTÉE `flatten` (liste de listes -> liste plate). Tout le moteur itère UN niveau.
`GenerateurImbrique` admet `REDUC(elt for x in args[0] for y in x)`. flatten = [y for x in xs for y in x].

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (map-repli)  : le map-repli (un niveau) ne minte pas flatten.
  2. IMBRIQUÉ (×2)    : `flatten` (lister) ET `sum_nested` (sommer) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle)  : l'orchestrateur (imbrique=True) résout flatten à l'étage `imbrique`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurImbrique, GenerateurMapRepli, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")


def _t(fn, tests, held):
    return Tache(id=f"im/{fn}", point_entree=fn, prompt=f'def {fn}(xss):\n    """..."""',
                 tests=tests, tests_held_out=held)


FLATTEN = _t("flatten",
    "def check(c):\n    assert c([[1,2],[3]]) == [1,2,3]\n    assert c([[1],[2,3],[4]]) == [1,2,3,4]\n    assert c([[5]]) == [5]\ncheck(flatten)",
    "def check(c):\n    assert c([[1],[2],[3]]) == [1,2,3]\n    assert c([[7,8]]) == [7,8]\ncheck(flatten)")
SUM_NESTED = _t("sum_nested",
    "def check(c):\n    assert c([[1,2],[3]]) == 6\n    assert c([[1],[2,3]]) == 6\n    assert c([[10]]) == 10\ncheck(sum_nested)",
    "def check(c):\n    assert c([[1,1],[1,1]]) == 4\n    assert c([[5],[5]]) == 10\ncheck(sum_nested)")


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
    im = GenerateurImbrique([CARRE])

    resultats.append(_check("MUR : le map-repli (un seul niveau) ne minte pas flatten",
                            _resout_gen(GenerateurMapRepli([CARRE]), FLATTEN) is None))

    g1 = _resout_gen(im, FLATTEN)
    g2 = _resout_gen(im, SUM_NESTED)
    if g1:
        print(f"    flatten    -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    sum_nested -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("IMBRIQUÉ : `flatten` (lister) ET `sum_nested` (sommer) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=[CARRE], predicteur=Predicteur(store, types=TYPES_RICHES), imbrique=True)
        etage, _, code, _ = resoudre(orch, FLATTEN, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (imbrique=True) résout flatten à l'étage `{etage}`",
        code is not None and etage == "imbrique"))

    print()
    if all(resultats):
        print(f"IMBRIQUÉ VALIDÉ — {len(resultats)}/{len(resultats)}. Itérer deux niveaux (liste de listes) : flatten "
              f"ET sum_nested, held-out, honnête, utilisé par le modèle. **Thème I (structures de données) amorcé** ; "
              f"restent dict-accumulateur (word_count) et group-by (max_par_cle).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
