"""
INDEXATION ORDONNÉE — accès piloté par une 2ᵉ entrée (front d'après, thème 3).

`GenerateurIndexOrdonne` : RANG `sorted(args[0])[IDX]` (IDX ∈ {args[1]-1, -args[1], args[1]}) -> kth_largest =
sorted(xs)[-k] ; RECHERCHE dichotomique de args[1] dans la liste triée -> index ou -1 (binary_search).

Critères de MORT :
  1. MUR ×2          : `composition` (primitives UNAIRES, index figé) ne minte NI kth_largest NI binary_search
                       (l'index/la cible est une 2ᵉ entrée RUNTIME).
  2. GÉNÉRAL ×2      : `kth_largest` (rang) ET `binary_search` (dichotomie) mintés + GÉNÉRALISENT au held-out
                       adverse (k=1/k=n, doublons, absent -> -1, bornes lo/hi, singleton).
  3. HONNÊTE         : ne résout PAS `element_brut` = xs[k] (indexation SANS tri ; hors-famille).
  4. VIVANT (modèle) : l'orchestrateur (index_ordonne=True) résout kth_largest à l'étage `index-ordonne`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurCompose, GenerateurIndexOrdonne, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


# primitives unaires que la composition pourrait enchaîner (dont trie + accès bouts) — preuve qu'elle ne peut
# tout de même PAS indexer par un k runtime.
PRIMS = [_d("trie", "sorted(args[0])"), _d("premier", "args[0][0]"), _d("dernier", "args[0][-1]"),
         _d("avant_dernier", "args[0][-2]")]


def _t(fn, tests, held):
    return Tache(id=f"ix/{fn}", point_entree=fn, prompt=f'def {fn}(xs, k):\n    """..."""',
                 tests=tests, tests_held_out=held)


# sorted(xs)[-k] ; held-out adverse : k=1 (max), k=n (min), doublons, singleton.
KTH_LARGEST = _t("kth_largest",
    "def check(c):\n    assert c([3,1,2],1) == 3\n    assert c([3,1,2],2) == 2\ncheck(kth_largest)",
    "def check(c):\n    assert c([5,4,3,2,1],1) == 5\n    assert c([5,4,3,2,1],5) == 1\n    assert c([10,10,20],1) == 20\n    assert c([7],1) == 7\n    assert c([1,2,3],3) == 1\ncheck(kth_largest)")

# dichotomie -> index ou -1 ; held-out adverse : 1er/dernier, absent -> -1, singleton présent/absent.
BINARY_SEARCH = _t("binary_search",
    "def check(c):\n    assert c([1,3,5,7],5) == 2\n    assert c([1,3,5],4) == -1\ncheck(binary_search)",
    "def check(c):\n    assert c([1,2,3,4,5],1) == 0\n    assert c([1,2,3,4,5],5) == 4\n    assert c([2,4,6],6) == 2\n    assert c([2,4,6],1) == -1\n    assert c([10],10) == 0\n    assert c([10],99) == -1\ncheck(binary_search)")

# tâche (xs,k) hors-famille : indexer SANS trier. La brique (qui trie / dichotomie) ne doit PAS la résoudre.
ELEMENT_BRUT = _t("element_brut",
    "def check(c):\n    assert c([3,1,2],0) == 3\n    assert c([3,1,2],2) == 2\ncheck(element_brut)",
    "def check(c):\n    assert c([9,8,7],1) == 8\ncheck(element_brut)")


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
    ix = GenerateurIndexOrdonne()

    co = GenerateurCompose(PRIMS, profondeur=2)
    resultats.append(_check(
        "MUR ×2 : `composition` (unaires, index figé) ne minte NI kth_largest NI binary_search (k runtime)",
        _resout_gen(co, KTH_LARGEST) is None and _resout_gen(co, BINARY_SEARCH) is None))

    g1 = _resout_gen(ix, KTH_LARGEST)
    g2 = _resout_gen(ix, BINARY_SEARCH)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `kth_largest` (rang) ET `binary_search` (dichotomie) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : ne résout PAS `element_brut` = xs[k] (indexation SANS tri, hors-famille)",
        _resout_gen(ix, ELEMENT_BRUT) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), index_ordonne=True)
        etage, _, code, _ = resoudre(orch, KTH_LARGEST, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (index_ordonne=True) résout kth_largest à l'étage `{etage}`",
        code is not None and etage == "index-ordonne"))

    print()
    if all(resultats):
        print(f"INDEXATION ORDONNÉE VALIDÉE — {len(resultats)}/{len(resultats)}. Accès piloté par une 2ᵉ entrée "
              f"(rang + dichotomie) : kth_largest ET binary_search, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
