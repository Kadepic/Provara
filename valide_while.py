"""
CONTRÔLE GÉNÉRALISÉ (2) — boucle WHILE pilotée par une CONDITION (le `while`, classe gcd).

2e barreau de la famille A (carte du plafond). La récurrence et la boucle bornée itèrent sur un COMPTE ou une
SÉQUENCE ; gcd & co. itèrent TANT QU'une condition tient. C'est le terrain le plus explosif (non-terminaison),
cadré DEUX fois : un schéma figé + le JUGE lui-même (une boucle qui ne termine pas dépasse le timeout du sandbox
-> écartée par la RÉALITÉ). Schéma : `a,b=args[0],args[1]; while b: a,b=b,op(a,b); return a|b`.

Tests durcis au HELD-OUT (réflexe « tests trop simples ») : seule une solution qui GÉNÉRALISE est acceptée.

Critères de MORT :
  1. MUR (compté)   : récurrence (compte) ET boucle bornée (séquence) ne mintent PAS gcd (condition, pas compte).
  2. WHILE (gcd)    : le while minte gcd (op=mod) ET ça GÉNÉRALISE (held-out).
  3. SÛRETÉ         : une op DIVERGENTE (add : a,b=b,a+b ne termine jamais) est ÉCARTÉE par le juge (timeout),
                      pas par nous -> l'explosivité du while est cadrée par la réalité.
  4. VIVANT (modèle): l'orchestrateur (boucle_while=True) résout gcd à l'étage `while`, held-out compris.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurBoucle, GenerateurOrchestre, GenerateurRecurrence,
                        GenerateurWhile)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

MOD = ("mod", "def mod(*args, **kwargs):\n    return args[0] % args[1]\n")
SUB = ("sub", "def sub(*args, **kwargs):\n    return args[0] - args[1]\n")
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
EST_POS = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")


def _t(fn, sig, tests, held):
    return Tache(id=f"wh/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


GCD = _t("gcd", "a, b",
    "def check(c):\n    assert c(12,8) == 4\n    assert c(7,3) == 1\n    assert c(10,5) == 5\ncheck(gcd)",
    "def check(c):\n    assert c(48,18) == 6\n    assert c(100,75) == 25\n    assert c(9,6) == 3\ncheck(gcd)")


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
    wh = GenerateurWhile([MOD, SUB, ADD])

    # 1. MUR : récurrence (compte) et boucle bornée (séquence) ne mintent pas gcd.
    mur = (_resout_gen(GenerateurRecurrence([MOD, SUB, ADD]), GCD) is None
           and _resout_gen(GenerateurBoucle([MOD, SUB, ADD], [EST_POS]), GCD) is None)
    resultats.append(_check("MUR : récurrence (compte) ET boucle bornée (séquence) ne mintent pas gcd", mur))

    # 2. WHILE : minte gcd (op=mod) + généralise.
    g = _resout_gen(wh, GCD)
    if g:
        print(f"    gcd -> {[l.strip() for l in g.splitlines() if 'a, b' in l or 'return' in l]}")
    resultats.append(_check("WHILE (gcd) : gcd minté (op=mod) ET généralise (held-out)", g is not None))

    # 3. SÛRETÉ : une op divergente (add seule) -> aucune gcd (le juge écarte par timeout, pas nous).
    resultats.append(_check("SÛRETÉ : op divergente (`add` seule, ne termine jamais) -> aucune gcd "
                            "(écartée par le juge/timeout, pas par nous)",
                            _resout_gen(GenerateurWhile([ADD]), GCD) is None))

    # 4. VIVANT : l'orchestrateur (boucle_while=True) résout gcd à l'étage while.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, ops=[MOD, SUB, ADD], predicteur=Predicteur(store, types=TYPES_RICHES),
                                   boucle_while=True)
        etage, _, code, _ = resoudre(orch, GCD, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (boucle_while=True) résout gcd à l'étage `{etage}` (held-out compris)",
        code is not None and etage == "while"))

    print()
    if all(resultats):
        print(f"WHILE VALIDÉ — {len(resultats)}/{len(resultats)}. Le contrôle piloté par CONDITION est franchi (gcd) — "
              f"ce que les boucles comptées ne peuvent pas. Schéma figé + le JUGE qui écarte les non-terminantes "
              f"(timeout = la réalité cadre l'explosivité, pas nous) ; jugé held-out, honnête, le modèle l'utilise "
              f"(étage `while`). Famille A (contrôle généralisé) : les DEUX barreaux — récurrence multi-état ET while "
              f"— sont posés. Le modèle fait désormais des algorithmes à état ET à condition.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Le while ne franchit pas (encore) la condition : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
