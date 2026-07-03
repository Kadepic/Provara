"""
DOMAINE LOGIQUE — quantificateurs de comptage (2026-06-17, élargir les domaines vérifiables). `GenerateurLogique`
= prédicats sur le COMPTE d'une liste de vérités (`exactement_un`, `majorité`, `parité`…). `all`/`any` sont déjà
`min`/`max` (couverts) ; un prédicat `sum(xs)==k` ne l'est pas.

Critères de MORT (4) :
  1. MUR        : `comprehension-generale` (replie en sum/count/max/min) ne minte PAS `exactement_un` (`sum==1`,
                  un PRÉDICAT sur le compte — il rend la somme, pas la comparaison).
  2. GÉNÉRAL ×2 : `exactement_un` (sum==1) ET `majorite` (2·sum>len) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `somme_carres` (agrégat numérique, pas un quantificateur).
  4. VIVANT    : l'orchestrateur (logique=True) résout `exactement_un` à l'étage `logique`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurLogique, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"log/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


EXUN = _t("exactement_un", "bools",
    "def check(c):\n    assert c([True,False,False]) == True\n    assert c([True,True,False]) == False\ncheck(exactement_un)",
    "def check(c):\n    assert c([False,False]) == False\n    assert c([True]) == True\n    assert c([True,True,True]) == False\n    assert c([False,True,True]) == False\ncheck(exactement_un)")
MAJ = _t("majorite", "bools",
    "def check(c):\n    assert c([True,True,False]) == True\n    assert c([True,False,False]) == False\ncheck(majorite)",
    "def check(c):\n    assert c([True,True,True,False]) == True\n    assert c([True,False]) == False\ncheck(majorite)")
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
    log = GenerateurLogique()

    r.append(_check("MUR : `comprehension-generale` (sum/count/max/min) ne minte pas `exactement_un` (prédicat sum==1)",
                    _resout(GenerateurComprehensionGenerale([]), EXUN) is None))

    r.append(_check("GÉNÉRAL ×2 : `exactement_un` (sum==1) ET `majorite` (2·sum>len) mintés + held-out adverse",
                    _resout(log, EXUN) is not None and _resout(log, MAJ) is not None))

    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (agrégat numérique, pas un quantificateur)",
                    _resout(log, SOMME_CARRES) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), logique=True)
        e, _, code, _ = resoudre(orch, EXUN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (logique=True) résout `exactement_un` à l'étage `{e}`",
                    code is not None and e == "logique"))

    print()
    print("LOGIQUE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
