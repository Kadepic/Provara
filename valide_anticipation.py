"""
ANTICIPATION — prédire le TERME SUIVANT d'une séquence (2026-06-17, insight Yohan « l'anticipation est une brique
cross-domaine » ; 1ʳᵉ des briques COGNITIVES). `GenerateurAnticipation` projette le futur selon la règle que les
exemples établissent (held-out = preuve qu'on a saisi la RÈGLE, pas mémorisé).

Critères de MORT (4) :
  1. MUR      : ni `adjacence` (agrège des voisins) ni `map-repli` (replie le passé) ne mintent un terme SUIVANT.
  2. GÉNÉRAL ×2 : `suite_ari` (arithmétique) ET `suite_fib` (Fibonacci-like) mintés + held-out adverse (le visible
                  désambigue la règle ; le held-out prouve la généralisation).
  3. HONNÊTE  : ne résout pas `somme_carres` (agrégat du passé, pas une projection).
  4. VIVANT   : l'orchestrateur (anticipation=True) résout `suite_ari` à l'étage `anticipation`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurAdjacence, GenerateurAnticipation, GenerateurMapRepli,
                        GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"anti/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests, tests_held_out=held)


SUITE_ARI = _t("suite_ari",
    "def check(c):\n    assert c([1,2,3]) == 4\n    assert c([10,20,30]) == 40\ncheck(suite_ari)",
    "def check(c):\n    assert c([5,7,9]) == 11\n    assert c([2,4,6]) == 8\ncheck(suite_ari)")
SUITE_FIB = _t("suite_fib",
    "def check(c):\n    assert c([1,1,2]) == 3\n    assert c([2,3,5]) == 8\ncheck(suite_fib)",
    "def check(c):\n    assert c([1,2,3]) == 5\n    assert c([3,5,8]) == 13\ncheck(suite_fib)")
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
    anti = GenerateurAnticipation()

    prims = [("carre", "def carre(*args, **kwargs):\n    return args[0]*args[0]\n"),
             ("cube", "def cube(*args, **kwargs):\n    return args[0]**3\n")]
    r.append(_check("MUR : ni `adjacence` ni `map-repli` ne mintent le terme suivant `suite_ari`",
                    _resout(GenerateurAdjacence(), SUITE_ARI) is None
                    and _resout(GenerateurMapRepli(prims), SUITE_ARI) is None))

    r.append(_check("GÉNÉRAL ×2 : `suite_ari` (arithmétique) ET `suite_fib` (Fibonacci-like) mintés + held-out adverse",
                    _resout(anti, SUITE_ARI) is not None and _resout(anti, SUITE_FIB) is not None))

    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (agrégat du passé, pas une projection)",
                    _resout(anti, SOMME_CARRES) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), anticipation=True)
        e, _, code, _ = resoudre(orch, SUITE_ARI, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (anticipation=True) résout `suite_ari` à l'étage `{e}`",
                    code is not None and e == "anticipation"))

    print()
    print("ANTICIPATION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
