"""
PRÉDICAT STRUCTUREL — « x invariant sous une primitive » : `x == prim(x)` (famille B de la carte du plafond).

La carte a montré HORS-PORTÉE `is_palindrome` (x == reverse(x)) et `is_sorted` (xs == sorted(xs)) : le branchement
teste des prédicats DONNÉS, il ne compare pas une entrée à sa propre structure transformée. `GenerateurInvariant`
admet UN schéma figé `return args[0] == prim(args[0])` (prim confirmée). Élégance : un schéma, DEUX classes —
palindrome = invariant sous `inverse_chaine`, is_sorted = invariant sous `trie`.

Tests durcis au HELD-OUT (réflexe « tests trop simples »).

Critères de MORT :
  1. MUR (branchement)  : le branchement (prédicats donnés) ne minte PAS is_palindrome.
  2. INVARIANT (×2)     : `is_palindrome` (sous inverse_chaine) ET `is_sorted` (sous trie) mintés + GÉNÉRALISENT.
  3. HONNÊTE            : sans la primitive `inverse_chaine`, is_palindrome n'est PAS atteint.
  4. VIVANT (modèle)    : l'orchestrateur (invariant=True) résout is_palindrome à l'étage `invariant`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurBranche, GenerateurInvariant, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

INVERSE = ("inverse_chaine", "def inverse_chaine(*args, **kwargs):\n    return args[0][::-1]\n")
TRIE = ("trie", "def trie(*args, **kwargs):\n    return sorted(args[0])\n")
INCR = ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")
EST_POS = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")


def _t(fn, sig, tests, held):
    return Tache(id=f"inv/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


PALINDROME = _t("is_palindrome", "s",
    "def check(c):\n    assert c('aba') is True\n    assert c('ab') is False\n    assert c('') is True\ncheck(is_palindrome)",
    "def check(c):\n    assert c('abcba') is True\n    assert c('abc') is False\n    assert c('xx') is True\ncheck(is_palindrome)")
IS_SORTED = _t("is_sorted", "xs",
    "def check(c):\n    assert c([1,2,3]) is True\n    assert c([3,1]) is False\n    assert c([1]) is True\ncheck(is_sorted)",
    "def check(c):\n    assert c([1,2,2,3]) is True\n    assert c([2,1,3]) is False\n    assert c([]) is True\ncheck(is_sorted)")


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
    inv = GenerateurInvariant([INVERSE, TRIE, INCR])

    # 1. MUR : le branchement (prédicats donnés) ne minte pas is_palindrome.
    resultats.append(_check("MUR : le branchement (prédicats donnés) ne minte pas is_palindrome",
                            _resout_gen(GenerateurBranche([EST_POS]), PALINDROME) is None))

    # 2. INVARIANT ×2 : palindrome (sous inverse_chaine) et is_sorted (sous trie), généralisent.
    g1 = _resout_gen(inv, PALINDROME)
    g2 = _resout_gen(inv, IS_SORTED)
    if g1:
        print(f"    is_palindrome -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    is_sorted     -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("INVARIANT : `is_palindrome` (sous inverse_chaine) ET `is_sorted` (sous trie) "
                            "mintés + généralisent (un schéma, deux murs)", g1 is not None and g2 is not None))

    # 3. HONNÊTE : sans inverse_chaine, palindrome hors-portée.
    resultats.append(_check("HONNÊTE : sans la primitive `inverse_chaine`, is_palindrome n'est PAS atteint",
                            _resout_gen(GenerateurInvariant([TRIE, INCR]), PALINDROME) is None))

    # 4. VIVANT : l'orchestrateur (invariant=True) résout is_palindrome à l'étage invariant.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=[INVERSE, TRIE, INCR],
                                   predicteur=Predicteur(store, types=TYPES_RICHES), invariant=True)
        etage, _, code, _ = resoudre(orch, PALINDROME, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (invariant=True) résout is_palindrome à l'étage `{etage}`",
        code is not None and etage == "invariant"))

    print()
    if all(resultats):
        print(f"INVARIANT VALIDÉ — {len(resultats)}/{len(resultats)}. Les prédicats STRUCTURELS sont amorcés : "
              f"« x est-il un point fixe de prim ? » (x == prim(x)) — un schéma figé qui débloque DEUX classes d'un "
              f"coup, is_palindrome (sous inverse_chaine) et is_sorted (sous trie), jugées held-out, honnêtes, "
              f"utilisées par le modèle (étage invariant). Famille B amorcée.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Le prédicat structurel ne franchit pas (encore) : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
