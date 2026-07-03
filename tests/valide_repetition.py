"""
RÉPÉTITION COMPTÉE — appliquer une op binaire args[1] fois (compte = 2ᵉ entrée). Front d'après, thème 6.

`GenerateurRepetition` admet `acc=INIT; for _ in range(args[1]): acc=op(acc,args[0]); return acc` ;
(op,INIT) ∈ {(* ,1) puissance a^b, (+ ,0) produit répété a*b}. Le compte vient d'une 2ᵉ ENTRÉE (args[1]).

Critères de MORT :
  1. MUR ×2          : ni `multi-entrée` (arbres d'ops de profondeur bornée) ni `recurrence` (itère sur UN arg)
                       ne mintent `power` (b multiplications, b = valeur runtime).
  2. GÉNÉRAL ×2      : `power` (*,1) ET `produit_repete` (+,0) mintés + GÉNÉRALISENT (held-out adverse : b=0->INIT,
                       b=1, base négative où le signe compte, grand b).
  3. HONNÊTE         : ne résout PAS une tâche (a,b) hors-schéma (`somme` = a+b, pas de répétition).
  4. VIVANT (modèle) : l'orchestrateur (repetition=True) résout power à l'étage `repetition`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurMultiEntree, GenerateurOrchestre, GenerateurRecurrence,
                        GenerateurRepetition)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


OPS = [_d("mul", "args[0] * args[1]"), _d("add", "args[0] + args[1]"), _d("sub", "args[0] - args[1]")]


def _t(fn, tests, held):
    return Tache(id=f"re/{fn}", point_entree=fn, prompt=f'def {fn}(a, b):\n    """..."""',
                 tests=tests, tests_held_out=held)


# (* , 1) -> a^b ; held-out adverse : b=0 -> 1, b=1 -> a, base NÉGATIVE (signe), grand b, base 0.
POWER = _t("power",
    "def check(c):\n    assert c(2,3) == 8\n    assert c(5,0) == 1\ncheck(power)",
    "def check(c):\n    assert c(3,2) == 9\n    assert c(7,1) == 7\n    assert c(2,5) == 32\n    assert c(-2,3) == -8\n    assert c(-2,2) == 4\n    assert c(0,4) == 0\ncheck(power)")

# (+ , 0) -> a*b par addition répétée ; held-out : b=0 -> 0, b=1 -> a, négatif.
PRODUIT_REPETE = _t("produit_repete",
    "def check(c):\n    assert c(3,4) == 12\n    assert c(5,0) == 0\ncheck(produit_repete)",
    "def check(c):\n    assert c(7,1) == 7\n    assert c(-2,3) == -6\n    assert c(6,3) == 18\ncheck(produit_repete)")

# tâche (a,b) hors-schéma : pas de répétition (juste a+b). La brique ne doit PAS la résoudre.
SOMME = _t("somme",
    "def check(c):\n    assert c(2,3) == 5\n    assert c(10,1) == 11\ncheck(somme)",
    "def check(c):\n    assert c(4,4) == 8\ncheck(somme)")


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
    re_gen = GenerateurRepetition()

    me = GenerateurMultiEntree(OPS)
    rc = GenerateurRecurrence(OPS)
    resultats.append(_check(
        "MUR ×2 : ni `multi-entrée` (arbres bornés) ni `recurrence` (1 arg) ne mintent power (b mult., b runtime)",
        _resout_gen(me, POWER) is None and _resout_gen(rc, POWER) is None))

    g1 = _resout_gen(re_gen, POWER)
    g2 = _resout_gen(re_gen, PRODUIT_REPETE)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `power` (*,1) ET `produit_repete` (+,0) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : la brique ne résout PAS une tâche (a,b) hors-schéma (`somme` = a+b, sans répétition)",
        _resout_gen(re_gen, SOMME) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), repetition=True)
        etage, _, code, _ = resoudre(orch, POWER, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (repetition=True) résout power à l'étage `{etage}`",
        code is not None and etage == "repetition"))

    print()
    if all(resultats):
        print(f"RÉPÉTITION VALIDÉE — {len(resultats)}/{len(resultats)}. Op appliquée args[1] fois (compte = 2ᵉ entrée) : "
              f"power ET produit_repete, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
