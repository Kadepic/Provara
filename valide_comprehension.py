"""
Validation de la COMPRÉHENSION (1/2) — abstraire par compression.

Le store contient 6 succès sur 6 tâches. Trois « comptent selon un prédicat »,
deux « vérifient que tous satisfont un prédicat », un est unique. On exige :

  1. COMPRESSION : les 6 succès se ramènent à 2 ABSTRACTIONS (concepts) + 1 singleton.
     « compter selon {C} » couvre 3 cas ; « tous satisfont {C} » couvre 2 cas.
  2. UN PRINCIPE, PLUSIEURS CAS : l'abstraction de comptage relie 3 tâches DISTINCTES
     (pairs, positifs, impairs) — le même concept les explique. C'est ça, comprendre.
  3. JUGÉE PAR LE RÉEL : chaque abstraction, régénérée, RE-PASSE le juge sur tous ses
     cas (compression lossless). Pas « plausible » : confirmée.
  4. HONNÊTETÉ : le squelette vu une seule fois N'EST PAS un concept (pas de
     généralisation à partir d'un seul exemple).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import abstrais, confirme
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(id, fn, tests):
    return Tache(id=id, point_entree=fn,
                 prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# 6 tâches + solutions (forme args[0], pour que les squelettes coïncident).
SEEDS = [
    (_t("c/pairs", "compte_pairs",
        "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([]) == 0\ncheck(compte_pairs)"),
     "def compte_pairs(*args, **kwargs):\n    return sum(1 for x in args[0] if x % 2 == 0)\n"),
    (_t("c/positifs", "compte_positifs",
        "def check(c):\n    assert c([1,-2,3]) == 2\n    assert c([]) == 0\ncheck(compte_positifs)"),
     "def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n"),
    (_t("c/impairs", "compte_impairs",
        "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([]) == 0\ncheck(compte_impairs)"),
     "def compte_impairs(*args, **kwargs):\n    return sum(1 for x in args[0] if x % 2 == 1)\n"),
    (_t("t/pairs", "tous_pairs",
        "def check(c):\n    assert c([2,4]) is True\n    assert c([1,2]) is False\n    assert c([]) is True\ncheck(tous_pairs)"),
     "def tous_pairs(*args, **kwargs):\n    return all(x % 2 == 0 for x in args[0])\n"),
    (_t("t/positifs", "tous_positifs",
        "def check(c):\n    assert c([1,2]) is True\n    assert c([-1,2]) is False\n    assert c([]) is True\ncheck(tous_positifs)"),
     "def tous_positifs(*args, **kwargs):\n    return all(x > 0 for x in args[0])\n"),
    (_t("u/grand", "a_un_grand",
        "def check(c):\n    assert c([1,200]) is True\n    assert c([1,2]) is False\n    assert c([]) is False\ncheck(a_un_grand)"),
     "def a_un_grand(*args, **kwargs):\n    return any(x > 100 for x in args[0])\n"),
]
TACHES = {t.id: t for t, _ in SEEDS}


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for tache, sol in SEEDS:
            v = juge(sol, tache.tests, LIM)
            assert v.passe, f"pré-condition : {tache.id}"
            store.ajoute(tache, sol, v)

        abstractions, singletons = abstrais(store)
        abstractions.sort(key=lambda a: -a.couverture)

        print(f"{len(store)} succès -> {len(abstractions)} abstraction(s) + {len(singletons)} singleton(s) :\n")
        for a in abstractions:
            print(f"    concept  {a.squelette}")
            print(f"      couvre {a.couverture} cas : {list(a.sens)}\n")
        for sk in singletons:
            print(f"    singleton (pas un concept) : {sk}")
        print()

        # 1. Compression : 6 succès -> 2 abstractions + 1 singleton.
        resultats.append(_check("compression : 6 succès -> 2 abstractions", len(abstractions) == 2))
        resultats.append(_check("couvertures = {3, 2}",
                                sorted(a.couverture for a in abstractions) == [2, 3]))
        resultats.append(_check("1 singleton (le squelette 'any')", len(singletons) == 1))

        # 2. Un principe, plusieurs cas : l'abstraction de comptage relie 3 tâches distinctes.
        compte = next(a for a in abstractions if a.couverture == 3)
        taches_reliees = {tid for _, tid in compte.instances}
        resultats.append(_check("un principe explique 3 tâches DISTINCTES (pairs/positifs/impairs)",
                                len(taches_reliees) == 3))

        # 3. Jugée par le réel : chaque abstraction est confirmée (lossless).
        resultats.append(_check("abstraction 'compter selon {C}' confirmée par le juge",
                                confirme(compte, TACHES, LIM)))
        tous = next(a for a in abstractions if a.couverture == 2)
        resultats.append(_check("abstraction 'tous satisfont {C}' confirmée par le juge",
                                confirme(tous, TACHES, LIM)))

        # 4. Générativité : le concept REGÉNÈRE une solution qui marche.
        regen = compte.genere("compte_pairs", "x % 2 == 0")
        resultats.append(_check("le concept régénère une solution valide (générativité)",
                                juge(regen, TACHES["c/pairs"].tests, LIM).passe))

    print()
    if all(resultats):
        print(f"COMPRÉHENSION (1/2) VALIDÉE — {len(resultats)}/{len(resultats)}. Le système passe de "
              f"« je garde N solutions » à « j'ai saisi les principes qui les engendrent » — confirmé par le réel.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
