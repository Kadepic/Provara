"""
JOINTURE PROFONDE — joindre deux sous-résultats PROFONDS par une op (fin de la famille C de la carte).

La carte a montré HORS-PORTÉE `produit_carres_bouts` = mul(carre(premier(xs)), carre(dernier(xs))) et
`max_minus_min` = max(xs) - min(xs) : la jointure simple ne joint que des PRIMITIVES (op(p1(x), p2(x))).
`GenerateurJointureProfonde` joint deux côtés PLUS PROFONDS : un AGRÉGAT (max/min/sum) ou un PIPELINE de
1-2 primitives. Un schéma : `op(G(xs), D(xs))`.

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (jointure)        : la jointure simple ne minte pas produit_carres_bouts ni max_minus_min.
  2. PROFONDE (pipelines)  : `produit_carres_bouts` (deux pipelines profonds) minté + GÉNÉRALISE.
  3. PROFONDE (agrégats)   : `max_minus_min` (deux agrégats de liste) minté + GÉNÉRALISE.
  4. HONNÊTE               : sans `premier`, produit_carres_bouts hors-portée (ne conjure pas la brique).
  5. VIVANT (modèle)       : l'orchestrateur (jointure_profonde=True) résout les deux à l'étage `jointure-profonde`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurJointure, GenerateurJointureProfonde, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")
PREMIER = ("premier", "def premier(*args, **kwargs):\n    return args[0][0]\n")
DERNIER = ("dernier", "def dernier(*args, **kwargs):\n    return args[0][-1]\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")
SUB = ("sub", "def sub(*args, **kwargs):\n    return args[0] - args[1]\n")

PRIMS = [CARRE, PREMIER, DERNIER]
OPS = [MUL, SUB]


def _t(fn, tests, held):
    return Tache(id=f"jp/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


PRODUIT_BOUTS = _t("produit_carres_bouts",
    "def check(c):\n    assert c([2,3]) == 36\n    assert c([1,4]) == 16\n    assert c([3,3]) == 81\ncheck(produit_carres_bouts)",
    "def check(c):\n    assert c([2,5]) == 100\n    assert c([1,1,1,4]) == 16\ncheck(produit_carres_bouts)")
MAX_MIN = _t("max_minus_min",
    "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,5]) == 0\n    assert c([1,9]) == 8\ncheck(max_minus_min)",
    "def check(c):\n    assert c([0,10,5]) == 10\n    assert c([7]) == 0\ncheck(max_minus_min)")


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
    jp = GenerateurJointureProfonde(PRIMS, OPS)

    # 1. MUR : la jointure simple ne joint que des primitives.
    js = GenerateurJointure(PRIMS, OPS)
    resultats.append(_check("MUR : la jointure SIMPLE ne minte ni produit_carres_bouts ni max_minus_min",
                            _resout_gen(js, PRODUIT_BOUTS) is None and _resout_gen(js, MAX_MIN) is None))

    # 2. PROFONDE (pipelines) : produit_carres_bouts.
    g1 = _resout_gen(jp, PRODUIT_BOUTS)
    if g1:
        print(f"    produit_carres_bouts -> {g1.strip().splitlines()[-1].strip()}")
    resultats.append(_check("PROFONDE (pipelines) : `produit_carres_bouts` (carre∘premier × carre∘dernier) "
                            "minté + généralise", g1 is not None))

    # 3. PROFONDE (agrégats) : max_minus_min.
    g2 = _resout_gen(jp, MAX_MIN)
    if g2:
        print(f"    max_minus_min        -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("PROFONDE (agrégats) : `max_minus_min` (max(xs) - min(xs)) minté + généralise",
                            g2 is not None))

    # 4. HONNÊTE : sans la transform `carre`, produit_carres_bouts hors-portée (positions intégrées, mais pas le transform).
    resultats.append(_check("HONNÊTE : sans la primitive `carre` (le transform), produit_carres_bouts n'est PAS atteint",
                            _resout_gen(GenerateurJointureProfonde([PREMIER, DERNIER], OPS), PRODUIT_BOUTS) is None))

    # 5. VIVANT : l'orchestrateur (jointure_profonde=True) résout les deux à l'étage jointure-profonde.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=PRIMS, ops=OPS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES), jointure_profonde=True)
        e1, _, c1, _ = resoudre(orch, PRODUIT_BOUTS, LIM)
        e2, _, c2, _ = resoudre(orch, MAX_MIN, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur résout les deux à l'étage `{e1}`/`{e2}` (jointure-profonde)",
        c1 is not None and c2 is not None and e1 == "jointure-profonde" and e2 == "jointure-profonde"))

    print()
    if all(resultats):
        print(f"JOINTURE PROFONDE VALIDÉE — {len(resultats)}/{len(resultats)}. Joindre deux sous-résultats PROFONDS "
              f"(deux pipelines OU deux agrégats) par une op : produit_carres_bouts ET max_minus_min, jugés held-out, "
              f"honnêtes, utilisés par le modèle. **Famille C COMPLÈTE** (map-reduce + jointure profonde).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La jointure profonde ne franchit pas (encore) : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
