"""
DOMAINE ENSEMBLISTE — algèbre de deux ensembles (2026-06-17, élargir les domaines vérifiables). `GenerateurEnsembles`
= intersection/union/différence/sym + prédicats (sous-ensemble, disjoints).

Critères de MORT (4) :
  1. MUR        : `dedup` (dédoublonne UNE liste) ne minte pas `intersection` (algèbre à DEUX listes).
  2. GÉNÉRAL ×2 : `intersection` (sorted(set&set)) ET `sous_ensemble` (set<=set) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `somme_carres` (agrégat scalaire, pas ensembliste).
  4. VIVANT    : l'orchestrateur (ensembles=True) résout `intersection` à l'étage `ensembles`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurDedup, GenerateurEnsembles, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"ens/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


INTER = _t("intersection", "a, b",
    "def check(c):\n    assert c([1,2,3],[2,3,4]) == [2,3]\n    assert c([1,2],[3,4]) == []\ncheck(intersection)",
    "def check(c):\n    assert c([1,1,2],[2,2,3]) == [2]\n    assert c([5],[5,6]) == [5]\ncheck(intersection)")
SOUS = _t("sous_ensemble", "a, b",
    "def check(c):\n    assert c([1,2],[1,2,3]) == True\n    assert c([1,4],[1,2,3]) == False\ncheck(sous_ensemble)",
    "def check(c):\n    assert c([],[1]) == True\n    assert c([1,2,3],[1,2]) == False\ncheck(sous_ensemble)")
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
    ens = GenerateurEnsembles()

    r.append(_check("MUR : `dedup` (une liste) ne minte pas `intersection` (algèbre à DEUX listes)",
                    _resout(GenerateurDedup(), INTER) is None))

    r.append(_check("GÉNÉRAL ×2 : `intersection` (set&set) ET `sous_ensemble` (set<=set) mintés + held-out adverse",
                    _resout(ens, INTER) is not None and _resout(ens, SOUS) is not None))

    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (agrégat scalaire, pas ensembliste)",
                    _resout(ens, SOMME_CARRES) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), ensembles=True)
        e, _, code, _ = resoudre(orch, INTER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (ensembles=True) résout `intersection` à l'étage `{e}`",
                    code is not None and e == "ensembles"))

    print()
    print("ENSEMBLES VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
