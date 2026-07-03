"""
MAP-PUIS-REPLI — replier un agrégateur sur une séquence TRANSFORMÉE par une primitive (famille C de la carte).

La carte du plafond a montré HORS-PORTÉE `somme_cubes` = sum(cube(x) for x in xs) : le pli replie une op sur la
séquence BRUTE, la fusion prend un élément du STORE — aucun ne replie sur `f(x)` où f est une PRIMITIVE confirmée
(éventuellement INVENTÉE). `GenerateurMapRepli` l'admet : `AGG(prim(x) for x in args[0])` (AGG universel, prim
confirmée). C'est le pont map-reduce : transformer chaque élément par un atome, puis replier.

Tests durcis au HELD-OUT. Deux tâches (AGG et prim différents -> schéma général).

Critères de MORT :
  1. MUR (pli)      : le pli (replie la séquence BRUTE) ne minte PAS sum(cube(x)).
  2. MAP-REPLI (×2) : minte `somme_cubes` (sum∘cube) ET `max_carres` (max∘carre), tous deux GÉNÉRALISENT.
  3. HONNÊTE        : sans la primitive `cube`, `somme_cubes` n'est PAS atteint (ne conjure pas l'atome).
  4. VIVANT (modèle): l'orchestrateur (map_repli=True) résout `somme_cubes` à l'étage `map-repli`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMapRepli, GenerateurOrchestre, GenerateurPli
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")
CUBE = ("cube", "def cube(*args, **kwargs):\n    return args[0] ** 3\n")
INCR = ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")


def _t(fn, tests, held):
    return Tache(id=f"mr/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


SOMME_CUBES = _t("somme_cubes",
    "def check(c):\n    assert c([1,2]) == 9\n    assert c([2,3]) == 35\n    assert c([0,1]) == 1\ncheck(somme_cubes)",
    "def check(c):\n    assert c([1,2,3]) == 36\n    assert c([3]) == 27\ncheck(somme_cubes)")
MAX_CARRES = _t("max_carres",
    "def check(c):\n    assert c([1,3,2]) == 9\n    assert c([2,2]) == 4\n    assert c([5,1]) == 25\ncheck(max_carres)",
    "def check(c):\n    assert c([4,3]) == 16\n    assert c([6]) == 36\ncheck(max_carres)")


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
    mr = GenerateurMapRepli([CARRE, CUBE, INCR])

    # 1. MUR : le pli (replie la séquence brute) ne minte pas sum(cube(x)).
    resultats.append(_check("MUR : le pli (replie la séquence BRUTE) ne minte pas sum(cube(x))",
                            _resout_gen(GenerateurPli([ADD, MUL]), SOMME_CUBES) is None))

    # 2. MAP-REPLI ×2 : somme_cubes (sum∘cube) et max_carres (max∘carre), généralisent.
    g1 = _resout_gen(mr, SOMME_CUBES)
    if g1:
        print(f"    somme_cubes -> {g1.strip().splitlines()[-1].strip()}")
    g2 = _resout_gen(mr, MAX_CARRES)
    if g2:
        print(f"    max_carres  -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("MAP-REPLI : `somme_cubes` (sum∘cube) ET `max_carres` (max∘carre) mintés + généralisent "
                            "(schéma général : AGG et prim varient)", g1 is not None and g2 is not None))

    # 3. HONNÊTE : sans cube, somme_cubes hors-portée.
    resultats.append(_check("HONNÊTE : sans la primitive `cube`, `somme_cubes` n'est PAS atteint (ne conjure pas l'atome)",
                            _resout_gen(GenerateurMapRepli([CARRE, INCR]), SOMME_CUBES) is None))

    # 4. VIVANT : l'orchestrateur (map_repli=True) résout somme_cubes à l'étage map-repli.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=[CARRE, CUBE, INCR],
                                   predicteur=Predicteur(store, types=TYPES_RICHES), map_repli=True)
        etage, _, code, _ = resoudre(orch, SOMME_CUBES, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (map_repli=True) résout `somme_cubes` à l'étage `{etage}`",
        code is not None and etage == "map-repli"))

    print()
    if all(resultats):
        print(f"MAP-PUIS-REPLI VALIDÉ — {len(resultats)}/{len(resultats)}. Le pont map-reduce est posé : replier un "
              f"agrégateur sur une séquence TRANSFORMÉE par une primitive (éventuellement inventée) — sum(cube(x)), "
              f"max(carre(x)) — ce que pli/fusion ne pouvaient pas, jugé held-out, honnête, le modèle l'utilise "
              f"(étage map-repli). Famille C amorcée (map-reduce) ; restent jointure profonde / deux agrégats.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Le map-repli ne franchit pas (encore) : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
