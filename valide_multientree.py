"""
COMPOSITION MULTI-ENTRÉE — lever le mur de l'arité ≥ 2 (joindre plusieurs arguments).

La carte du plafond (`valide_plateau`) a isolé une cause de mécanisme : tout générateur n'opérait que sur
`args[0]`, donc les tâches à PLUSIEURS arguments restaient hors de portée. `GenerateurMultiEntree` bâtit des
arbres d'OPS binaires confirmées (du registre, comme le pli) sur les arguments BRUTS `args[0..m-1]`.

On exige (A/B falsifiable) :
  1. MUR        : ni composition, ni jointure, ni pli ne résolvent un arg-2/arg-3 (ils restent sur args[0]).
  2. ARG 2      : multi-entrée résout `somme_deux(a,b) = a+b` et `max_deux(a,b) = max(a,b)` (ops du registre).
  3. ARG 3      : multi-entrée résout `clamp(x,lo,hi) = max2(lo, min2(x, hi))` (arbre d'ops, profondeur 2).
  4. HONNÊTETÉ  : sans l'op `min2`, plus de clamp (emploie le confirmé, n'invente pas).
  5. ESCALADE   : via l'orchestrateur, clamp est résolu à l'étage `multi-entrée`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import (TYPES_RICHES, GenerateurCompose, GenerateurJointure,
                        GenerateurMultiEntree, GenerateurOrchestre, GenerateurPli)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held=""):
    return Tache(id=f"me/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
MIN2 = ("min2", "def min2(*args, **kwargs):\n    return args[0] if args[0] < args[1] else args[1]\n")
MAX2 = ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n")
OPS = [ADD, MIN2, MAX2]
PRIMS = [("premier", "def premier(*args, **kwargs):\n    return args[0][0]\n")]

# held-out ADVERSE (leçon « tests durs ») : b<0 tue le faux passeur max(a, a+b) qui coïncidait sur b>=0.
SOMME_DEUX = _t("somme_deux", "a, b",
                "def check(c):\n    assert c(2,3) == 5\n    assert c(0,0) == 0\n    assert c(-1,4) == 3\ncheck(somme_deux)",
                "def check(c):\n    assert c(5,-3) == 2\n    assert c(3,-10) == -7\n    assert c(-5,-5) == -10\ncheck(somme_deux)")
MAX_DEUX = _t("max_deux", "a, b",
              "def check(c):\n    assert c(2,3) == 3\n    assert c(5,1) == 5\n    assert c(4,4) == 4\ncheck(max_deux)",
              "def check(c):\n    assert c(-5,-3) == -3\n    assert c(0,-7) == 0\n    assert c(-2,-2) == -2\ncheck(max_deux)")
CLAMP = _t("clamp", "x, lo, hi",
           "def check(c):\n    assert c(5,0,10) == 5\n    assert c(-3,0,10) == 0\n    assert c(20,0,10) == 10\ncheck(clamp)",
           "def check(c):\n    assert c(-3,-10,10) == -3\n    assert c(15,0,5) == 5\n    assert c(7,7,7) == 7\ncheck(clamp)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=2000):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code   # held-out exigé quand présent -> pas de faux passeur par coïncidence
    return None


def _resout_escalade(orch, tache, k=2000):
    for nom_etage, cands in orch.etages(tache.prompt, k):
        for code in cands:
            if juge(code, tache.tests, LIM).passe:
                return nom_etage
    return None


def main() -> int:
    resultats = []

    # 1. MUR : composition / jointure / pli (sur args[0]) ne résolvent pas clamp.
    mur = (_resout(GenerateurCompose(PRIMS), CLAMP) is None
           and _resout(GenerateurJointure(PRIMS, OPS), CLAMP) is None
           and _resout(GenerateurPli(OPS), CLAMP) is None)
    resultats.append(_check("MUR : ni composition, ni jointure, ni pli ne résolvent clamp (tous sur args[0])", mur))

    # 2. ARG 2.
    me = GenerateurMultiEntree(OPS)
    arg2 = _resout(me, SOMME_DEUX) is not None and _resout(me, MAX_DEUX) is not None
    resultats.append(_check("ARG 2 : multi-entrée résout somme_deux=add(a,b) ET max_deux=max2(a,b)", arg2))

    # 3. ARG 3 (arbre d'ops, profondeur 2).
    g_clamp = _resout(me, CLAMP)
    if g_clamp:
        print(f"    clamp -> {g_clamp.strip().splitlines()[-1].strip()}")
    resultats.append(_check("ARG 3 : multi-entrée résout clamp = max2(lo, min2(x, hi))", g_clamp is not None))

    # 4. HONNÊTETÉ : sans min2, plus de clamp.
    resultats.append(_check("HONNÊTETÉ : sans l'op `min2`, multi-entrée ne résout PLUS clamp (emploie le confirmé)",
                            _resout(GenerateurMultiEntree([ADD, MAX2]), CLAMP) is None))

    # 5. ESCALADE.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=PRIMS, ops=OPS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES))
        etage = _resout_escalade(orch, CLAMP)
    resultats.append(_check(f"ESCALADE : l'orchestrateur résout clamp à l'étage `{etage}`", etage == "multi-entrée"))

    print()
    if all(resultats):
        print(f"MULTI-ENTRÉE VALIDÉE — {len(resultats)}/{len(resultats)}. Le mur de l'arité ≥ 2 (mesuré par le "
              f"stress/plafond) TOMBE : le moteur joint plusieurs arguments par des arbres d'ops confirmées "
              f"(arité 2 et 3), sans modèle externe, jugé par le réel. 2e mur de mécanisme levé.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
