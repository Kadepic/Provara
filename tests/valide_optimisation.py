"""
DÉCISION / OPTIMISATION — choisir le MEILLEUR élément par un critère dérivé (2026-06-17, brique cognitive 2/2 du
jour). `GenerateurOptimisation` = `max|min(args[0], key=lambda _x: f(_x))`. Cœur de « décider » (vers la planification).

Critères de MORT (4) :
  1. MUR        : ni `comprehension-generale` (max/min par VALEUR) ni `index-ordonne` (sorted[k] par VALEUR) ne mintent
                  une décision par CRITÈRE dérivé (`plus_long_mot` = max par longueur).
  2. GÉNÉRAL ×2 : `plus_long_mot` (max par len) ET `plus_grand_abs` (max par |x|) mintés + held-out adverse (le critère
                  dérivé DIFFÈRE du max par valeur — c'est ce qui prouve la décision).
  3. HONNÊTE   : ne résout pas `somme_carres` (agrégat, pas une décision).
  4. VIVANT    : l'orchestrateur (optimisation=True) résout `plus_long_mot` à l'étage `optimisation`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurIndexOrdonne,
                        GenerateurOptimisation, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache


LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"opt/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# max par LONGUEUR (≠ max par valeur lexicographique : ['a','bbb','cc'] -> 'bbb', pas 'cc').
LONG = _t("plus_long_mot", "mots",
    "def check(c):\n    assert c(['a','bbb','cc']) == 'bbb'\n    assert c(['x','yy']) == 'yy'\ncheck(plus_long_mot)",
    "def check(c):\n    assert c(['aaa','b']) == 'aaa'\n    assert c(['z','zzzz','zz']) == 'zzzz'\ncheck(plus_long_mot)")
# max par MAGNITUDE (≠ max par valeur : [1,-5,3] -> -5, pas 3).
ABSMAX = _t("plus_grand_abs", "xs",
    "def check(c):\n    assert c([1,-5,3]) == -5\n    assert c([2,-1]) == 2\ncheck(plus_grand_abs)",
    "def check(c):\n    assert c([-9,4]) == -9\n    assert c([-7,2,5]) == -7\ncheck(plus_grand_abs)")
SOMME_CARRES = _t("somme_carres", "xs",
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
    opt = GenerateurOptimisation()

    r.append(_check("MUR : ni `comprehension-generale` ni `index-ordonne` (par VALEUR) ne mintent `plus_long_mot` "
                    "(décision par critère dérivé)",
                    _resout(GenerateurComprehensionGenerale([]), LONG) is None
                    and _resout(GenerateurIndexOrdonne(), LONG) is None))

    r.append(_check("GÉNÉRAL ×2 : `plus_long_mot` (max par len) ET `plus_grand_abs` (max par |x|) mintés + held-out",
                    _resout(opt, LONG) is not None and _resout(opt, ABSMAX) is not None))

    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (agrégat, pas une décision)",
                    _resout(opt, SOMME_CARRES) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), optimisation=True)
        e, _, code, _ = resoudre(orch, LONG, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (optimisation=True) résout `plus_long_mot` à l'étage `{e}`",
                    code is not None and e == "optimisation"))

    print()
    print("OPTIMISATION/DÉCISION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
