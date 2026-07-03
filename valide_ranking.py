"""
CLASSEMENT / PRIORISATION — ordonner par critère dérivé (2026-06-17, brique cognitive). `GenerateurRanking` =
`sorted(args[0], key=lambda _x: f(_x)[, reverse])`. Distinct d'`optimisation` (un meilleur) : la liste ORDONNÉE.

Critères de MORT (4) :
  1. DISTINCTION (le mur) : le tri par VALEUR brute (`sorted(xs)`) ÉCHOUE `trie_par_longueur` (l'ordre diffère) ->
                            il FAUT le critère dérivé.
  2. GÉNÉRAL ×2 : `trie_par_longueur` (par len, asc) ET `trie_par_abs_desc` (par |x|, desc) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `somme_carres` (agrégat scalaire, pas un classement).
  4. VIVANT    : l'orchestrateur (ranking=True) résout `trie_par_longueur` à l'étage `ranking`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurOrchestre, GenerateurRanking
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"rank/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


LONG = _t("trie_par_longueur", "mots",
    "def check(c):\n    assert c(['bbb','a','cc']) == ['a','cc','bbb']\n    assert c(['xy','x']) == ['x','xy']\ncheck(trie_par_longueur)",
    "def check(c):\n    assert c(['xyz','x','xy']) == ['x','xy','xyz']\n    assert c(['aa','b','ccc']) == ['b','aa','ccc']\ncheck(trie_par_longueur)")
ABSDESC = _t("trie_par_abs_desc", "xs",
    "def check(c):\n    assert c([1,-5,3]) == [-5,3,1]\n    assert c([2,-1]) == [2,-1]\ncheck(trie_par_abs_desc)",
    "def check(c):\n    assert c([-9,4,1]) == [-9,4,1]\n    assert c([3,-7]) == [-7,3]\ncheck(trie_par_abs_desc)")
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
    rank = GenerateurRanking()

    # 1. DISTINCTION : le tri par VALEUR brute échoue (l'ordre par len diffère de l'ordre par valeur).
    par_valeur = "def trie_par_longueur(*args, **kwargs):\n    return sorted(args[0])\n"
    r.append(_check("DISTINCTION : le tri par VALEUR (`sorted(xs)`) ÉCHOUE `trie_par_longueur` -> critère dérivé requis",
                    not juge(par_valeur, LONG.tests, LIM).passe and _resout(rank, LONG) is not None))

    r.append(_check("GÉNÉRAL ×2 : `trie_par_longueur` (len, asc) ET `trie_par_abs_desc` (|x|, desc) mintés + held-out",
                    _resout(rank, LONG) is not None and _resout(rank, ABSDESC) is not None))

    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (agrégat scalaire, pas un classement)",
                    _resout(rank, SOMME_CARRES) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), ranking=True)
        e, _, code, _ = resoudre(orch, LONG, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (ranking=True) résout `trie_par_longueur` à l'étage `{e}`",
                    code is not None and e == "ranking"))

    print()
    print("RANKING/PRIORISATION VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
