"""
ADJACENCE — agréger une relation entre éléments VOISINS (thème II : transitions, monotonie).

Rien ne comparait des éléments ADJACENTS. `GenerateurAdjacence` admet `AGG(args[0][i] REL args[0][i-1] for i in
1..len)` (AGG ∈ all/any/sum, REL ∈ comparaisons). Débloque `count_transitions` (sum(!=)) et `est_croissant`
(all(>)). Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (pli/fusion)   : le pli ne minte pas count_transitions (pas de notion de voisin).
  2. ADJACENCE (×2)     : `count_transitions` (sum !=) ET `est_croissant` (all >) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle)    : l'orchestrateur (adjacence=True) résout count_transitions à l'étage `adjacence`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurAdjacence, GenerateurOrchestre, GenerateurPli
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
MAX2 = ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n")


def _t(fn, tests, held):
    return Tache(id=f"ad/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


COUNT_TRANS = _t("count_transitions",
    "def check(c):\n    assert c([1,1,2,3,3]) == 2\n    assert c([1,1,1]) == 0\n    assert c([1,2,3]) == 2\n    assert c([5]) == 0\ncheck(count_transitions)",
    "def check(c):\n    assert c([1,2,2,3]) == 2\n    assert c([4,4]) == 0\n    assert c([1,2,1,2]) == 3\ncheck(count_transitions)")
EST_CROISSANT = _t("est_croissant",
    "def check(c):\n    assert c([1,2,3]) is True\n    assert c([1,1,2]) is False\n    assert c([3,2]) is False\n    assert c([5]) is True\ncheck(est_croissant)",
    "def check(c):\n    assert c([1,2,3,4]) is True\n    assert c([2,1]) is False\n    assert c([10,20,30]) is True\ncheck(est_croissant)")


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
    ad = GenerateurAdjacence()

    resultats.append(_check("MUR : le pli (replie la séquence, pas les voisins) ne minte pas count_transitions",
                            _resout_gen(GenerateurPli([ADD, MAX2]), COUNT_TRANS) is None))

    g1 = _resout_gen(ad, COUNT_TRANS)
    g2 = _resout_gen(ad, EST_CROISSANT)
    if g1:
        print(f"    count_transitions -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    est_croissant     -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("ADJACENCE : `count_transitions` (sum !=) ET `est_croissant` (all >) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), adjacence=True)
        etage, _, code, _ = resoudre(orch, COUNT_TRANS, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (adjacence=True) résout count_transitions à l'étage `{etage}`",
        code is not None and etage == "adjacence"))

    print()
    if all(resultats):
        print(f"ADJACENCE VALIDÉE — {len(resultats)}/{len(resultats)}. Agréger une relation entre VOISINS : "
              f"count_transitions ET est_croissant, held-out, honnête, utilisé par le modèle. Thème II avance "
              f"(multipasse + adjacence ; reste générer-et-tester / run-length à état).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
