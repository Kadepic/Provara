"""
PAIRES — quantification ∃ sur tous les couples i<j (front d'après, thème 5).

`GenerateurPaires` : `any(xs[i] OP xs[j] == t for i<j)`, OP ∈ {+,*,-}. two_sum_exists = ∃ i<j : xs[i]+xs[j]==t.

Critères de MORT :
  1. MUR             : `adjacence` (paires CONSÉCUTIVES i,i-1 seulement) ne minte pas two_sum_exists (couples quelconques).
  2. GÉNÉRAL ×2      : `two_sum_exists` (+) ET `two_product_exists` (*) mintés + GÉNÉRALISENT au held-out adverse
                       (un seul élément -> False car i<j strict ; zéros ; absent -> False ; doublons).
  3. HONNÊTE         : ne résout PAS `contient` = (t in xs) (appartenance d'UN élément, pas une paire).
  4. VIVANT (modèle) : l'orchestrateur (paires=True) résout two_sum_exists à l'étage `paires`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurAdjacence, GenerateurOrchestre, GenerateurPaires)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"pa/{fn}", point_entree=fn, prompt=f'def {fn}(xs, t):\n    """..."""',
                 tests=tests, tests_held_out=held)


# OP `+` ; held-out adverse : singleton -> False (i<j strict), zéros, somme absente -> False, paire au bout.
TWO_SUM = _t("two_sum_exists",
    "def check(c):\n    assert c([1,2,3],5) is True\n    assert c([1,2,3],10) is False\ncheck(two_sum_exists)",
    "def check(c):\n    assert c([1,2,3,4],7) is True\n    assert c([0,0],0) is True\n    assert c([5],5) is False\n    assert c([1,2],3) is True\n    assert c([1,2],4) is False\ncheck(two_sum_exists)")

# OP `*` ; held-out adverse : produit via zéro, singleton -> False, produit absent.
TWO_PROD = _t("two_product_exists",
    "def check(c):\n    assert c([2,3,4],6) is True\n    assert c([2,3,4],5) is False\ncheck(two_product_exists)",
    "def check(c):\n    assert c([1,5,2],10) is True\n    assert c([0,4],0) is True\n    assert c([3],9) is False\n    assert c([2,3],7) is False\ncheck(two_product_exists)")

# tâche (xs,t) hors-famille : appartenance d'UN élément. La brique (paires) ne doit PAS la résoudre.
CONTIENT = _t("contient",
    "def check(c):\n    assert c([1,2,3],2) is True\n    assert c([1,2,3],9) is False\ncheck(contient)",
    "def check(c):\n    assert c([5,6],6) is True\n    assert c([5,6],1) is False\ncheck(contient)")


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
    pa = GenerateurPaires()

    resultats.append(_check(
        "MUR : `adjacence` (paires CONSÉCUTIVES seulement) ne minte pas two_sum_exists (couples quelconques)",
        _resout_gen(GenerateurAdjacence(), TWO_SUM) is None))

    g1 = _resout_gen(pa, TWO_SUM)
    g2 = _resout_gen(pa, TWO_PROD)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `two_sum_exists` (+) ET `two_product_exists` (*) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : ne résout PAS `contient` = (t in xs) (appartenance d'UN élément, pas une paire)",
        _resout_gen(pa, CONTIENT) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), paires=True)
        etage, _, code, _ = resoudre(orch, TWO_SUM, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (paires=True) résout two_sum_exists à l'étage `{etage}`",
        code is not None and etage == "paires"))

    print()
    if all(resultats):
        print(f"PAIRES VALIDÉE — {len(resultats)}/{len(resultats)}. ∃ sur tous les couples i<j : two_sum_exists ET "
              f"two_product_exists, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
