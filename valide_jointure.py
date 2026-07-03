"""
FUSION VERTICALE — CAP 2 : composition d'ARITÉ 2 (joindre deux sous-résultats).

Le stress (`valide_compounding_stress.py`) a MESURÉ le mur : la composition unaire `p2(p1(x))` ne
sait pas COMBINER deux extractions. `GenerateurJointure` le franchit en réutilisant le registre
vivant (décision Yohan) : `g(x) = op(p1(x), p2(x))` avec `op` une opération binaire CONFIRMÉE
(comme le pli) et `p1`, `p2` des primitives confirmées. C'est la symétrie du pli (UNE op sur DEUX
projections du même argument, au lieu d'UNE op repliée sur une séquence).

Primitives confirmées : premier (xs[0]), dernier (xs[-1]).
Ops confirmées        : mul (a*b), max2 (max).

On exige (chaque critère est falsifiable) :
  1. MUR : ni le séquençage (composition unaire) ni le pli ne résolvent `xs[0]*xs[-1]`
     (le pipeline est unaire ; le pli replie l'op sur TOUTE la séquence, pas sur deux points).
  2. JOINTURE RÉSOUT : `GenerateurJointure` produit `mul(premier(x), dernier(x))`. Confirmé par le juge.
  3. AUTRE OP, MÊME MÉCANISME : avec `max2`, il résout `max(xs[0], xs[-1])` — l'op vient du registre,
     pas d'un câblage par tâche.
  4. HONNÊTETÉ : sans l'op `mul` (registre vidé), la jointure ne résout PLUS `xs[0]*xs[-1]`
     (elle joint du confirmé, elle n'invente pas).
  5. ESCALADE : via l'orchestrateur (façade complète), `produit_premier_dernier` est résolu à
     l'étage `jointure` — le mur mesuré par le stress TOMBE, sans câblage par tâche.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import (TYPES_RICHES, GenerateurCompose, GenerateurJointure,
                        GenerateurOrchestre, GenerateurPli)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests):
    return Tache(id=f"joint/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


PRIMS = [
    ("premier", "def premier(*args, **kwargs):\n    return args[0][0]\n"),
    ("dernier", "def dernier(*args, **kwargs):\n    return args[0][-1]\n"),
]
OPS = [
    ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n"),
    ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n"),
]

PRODUIT_PD = _t("produit_premier_dernier",
                "def check(c):\n    assert c([2,3,4]) == 8\n    assert c([5,1]) == 5\n    assert c([3]) == 9\ncheck(produit_premier_dernier)")
MAX_PD = _t("max_premier_dernier",
            "def check(c):\n    assert c([2,3,4]) == 4\n    assert c([5,1]) == 5\n    assert c([9]) == 9\ncheck(max_premier_dernier)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def _resout_escalade(orch, tache, k=400):
    for nom_etage, cands in orch.etages(tache.prompt, k):
        for code in cands:
            if juge(code, tache.tests, LIM).passe:
                return nom_etage
    return None


def main() -> int:
    resultats = []

    # 1. Le mur : composition unaire ET pli échouent sur xs[0]*xs[-1].
    ni_compose = _resout(GenerateurCompose(PRIMS), PRODUIT_PD) is None
    ni_pli = _resout(GenerateurPli(OPS), PRODUIT_PD) is None
    resultats.append(_check("MUR : ni la composition unaire ni le pli ne résolvent xs[0]*xs[-1]",
                            ni_compose and ni_pli))

    # 2. La jointure résout par op(p1(x), p2(x)).
    gagnant = _resout(GenerateurJointure(PRIMS, OPS), PRODUIT_PD)
    if gagnant:
        print(f"    jointure -> {gagnant.strip().splitlines()[-1].strip()}\n")
    resultats.append(_check("JOINTURE : mul(premier(x), dernier(x)) résout xs[0]*xs[-1]",
                            gagnant is not None))

    # 3. Autre op du registre, même mécanisme.
    resultats.append(_check("AUTRE OP : max2(premier(x), dernier(x)) résout max(xs[0], xs[-1]) (op du registre)",
                            _resout(GenerateurJointure(PRIMS, OPS), MAX_PD) is not None))

    # 4. Honnêteté : sans l'op mul, plus de jointure pour le produit.
    sans_mul = [(n, s) for n, s in OPS if n != "mul"]
    resultats.append(_check("HONNÊTETÉ : sans l'op `mul`, la jointure ne résout PLUS le produit (joint du confirmé, n'invente pas)",
                            _resout(GenerateurJointure(PRIMS, sans_mul), PRODUIT_PD) is None))

    # 5. Escalade : l'orchestrateur résout à l'étage `jointure` (le mur du stress tombe).
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=PRIMS, ops=OPS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES))
        etage = _resout_escalade(orch, PRODUIT_PD)
    resultats.append(_check(f"ESCALADE : l'orchestrateur résout produit_premier_dernier à l'étage `{etage}`",
                            etage == "jointure"))

    print()
    if all(resultats):
        print(f"COMPOSITION D'ARITÉ 2 VALIDÉE — {len(resultats)}/{len(resultats)}. Le mur mesuré par le stress "
              f"TOMBE : en réutilisant une op du registre vivant, le moteur JOINT deux sous-résultats "
              f"(op(p1(x), p2(x))) — symétrie du pli, sans modèle externe ni câblage par tâche. Cap 2, 1re brique.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
