"""
LOGIQUE POSITIONNELLE — agrégats positions paires vs impaires (famille D : alternating_sum).

La carte a montré HORS-PORTÉE `alternating_sum` = x0 - x1 + x2 - ... Rien ne dépendait de la PARITÉ de position.
`GenerateurPositionnel` admet `op(AGG(xs[::2]), AGG(xs[1::2]))` (positions paires vs impaires). op confirmée.
alternating_sum = sum(xs[::2]) - sum(xs[1::2]).

Tests durcis au HELD-OUT (cas de longueur paire ET impaire, valeurs qui tuent les coïncidences).

Critères de MORT :
  1. MUR (pli/jointure) : le pli ne minte pas alternating_sum (pas de notion de parité de position).
  2. POSITIONNEL        : `alternating_sum` (sum(paires) - sum(impaires)) minté + GÉNÉRALISE.
  3. HONNÊTE            : sans l'op `sub`, alternating_sum n'est PAS atteint.
  4. VIVANT (modèle)    : l'orchestrateur (positionnel=True) résout alternating_sum à l'étage `positionnel`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurOrchestre, GenerateurPli, GenerateurPositionnel
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

SUB = ("sub", "def sub(*args, **kwargs):\n    return args[0] - args[1]\n")
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")


def _t(fn, tests, held):
    return Tache(id=f"po/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


ALT_SUM = _t("alternating_sum",
    "def check(c):\n    assert c([1,2,3]) == 2\n    assert c([5]) == 5\n    assert c([1,1,1,1]) == 0\n    assert c([10,1]) == 9\ncheck(alternating_sum)",
    "def check(c):\n    assert c([2,3,4]) == 3\n    assert c([1,2,3,4]) == -2\n    assert c([]) == 0\ncheck(alternating_sum)")


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
    po = GenerateurPositionnel([SUB, ADD, MUL])

    resultats.append(_check("MUR : le pli (replie toute la séquence) ne minte pas alternating_sum (pas de parité)",
                            _resout_gen(GenerateurPli([ADD, SUB, MUL]), ALT_SUM) is None))

    g = _resout_gen(po, ALT_SUM)
    if g:
        print(f"    alternating_sum -> {g.strip().splitlines()[-1].strip()}")
    resultats.append(_check("POSITIONNEL : `alternating_sum` (sum(paires) - sum(impaires)) minté + généralise",
                            g is not None))

    resultats.append(_check("HONNÊTE : sans l'op `sub`, alternating_sum n'est PAS atteint",
                            _resout_gen(GenerateurPositionnel([ADD, MUL]), ALT_SUM) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, ops=[SUB, ADD, MUL],
                                   predicteur=Predicteur(store, types=TYPES_RICHES), positionnel=True)
        etage, _, code, _ = resoudre(orch, ALT_SUM, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (positionnel=True) résout alternating_sum à l'étage `{etage}`",
        code is not None and etage == "positionnel"))

    print()
    if all(resultats):
        print(f"POSITIONNEL VALIDÉ — {len(resultats)}/{len(resultats)}. La logique dépendante de la PARITÉ de position "
              f"est posée : alternating_sum (positions paires - impaires), held-out durci, honnête, utilisé par le "
              f"modèle. Famille D continue (count_vowels + positionnel ; reste reverse_words).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
