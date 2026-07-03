"""
CONTRÔLE GÉNÉRALISÉ (1) — RÉCURRENCE à DEUX ÉTATS sur un compte (le pli/boucle n'ont qu'UN accumulateur).

La carte du plafond (`mesure_plafond.py`) a montré HORS-PORTÉE une classe entière : les algorithmes à ÉTAT
MULTIPLE (fibonacci, Lucas…). Le pli et la boucle bornée replient/accumulent UN seul état ; deux états couplés
leur échappent. On l'admet en UN SEUL schéma figé (suite du « un schéma à la fois ») — itération BORNÉE par un
compte (pas de `while`, pas de non-terminaison) : `a,b = i0,i1 ; for _ in range(n): a,b = b, op(a,b) ; return a|b`.

Tests durcis par le HELD-OUT (réflexe Yohan « tests trop simples ») : on n'accepte qu'une solution qui GÉNÉRALISE
(pas un (op,inits,ret) qui colle aux seuls cas visibles).

Critères de MORT (deux récurrences, mêmes schéma, inits différents -> généralité, pas du fibonacci-hardcodé) :
  1. MUR (état unique)  : le pli ET la boucle bornée ne mintent PAS fibonacci (un seul accumulateur).
  2. RÉCURRENCE (fib)   : la récurrence minte fibonacci ET ça GÉNÉRALISE (held-out).
  3. RÉCURRENCE (Lucas) : minte Lucas (mêmes op/schéma, inits (2,1)) ET généralise -> schéma GÉNÉRAL.
  4. HONNÊTE            : sans l'op `add` (que `mul`), fibonacci n'est PAS minté (ne conjure pas l'op).
  5. VIVANT (modèle)    : l'orchestrateur (recurrence=True) résout fibonacci à l'étage `recurrence`, held-out compris.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurBoucle, GenerateurOrchestre, GenerateurPli,
                        GenerateurRecurrence)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")
EST_POS = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")


def _t(fn, tests, held):
    return Tache(id=f"rec/{fn}", point_entree=fn, prompt=f'def {fn}(n):\n    """..."""',
                 tests=tests, tests_held_out=held)


FIB = _t("fibonacci",
    "def check(c):\n    assert c(6) == 8\n    assert c(1) == 1\n    assert c(0) == 0\ncheck(fibonacci)",
    "def check(c):\n    assert c(8) == 21\n    assert c(10) == 55\n    assert c(2) == 1\ncheck(fibonacci)")
LUCAS = _t("lucas",
    "def check(c):\n    assert c(0) == 2\n    assert c(1) == 1\n    assert c(4) == 7\ncheck(lucas)",
    "def check(c):\n    assert c(5) == 11\n    assert c(6) == 18\n    assert c(2) == 3\ncheck(lucas)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_gen(gen, tache, n=400):
    """Ne renvoie qu'une solution qui passe le visible ET le HELD-OUT (vraie récurrence, pas overfit)."""
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and juge(code, tache.tests_held_out, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []
    rec = GenerateurRecurrence([ADD, MUL])

    # 1. MUR : pli (replie 1 état) et boucle bornée ne mintent pas fibonacci.
    mur = (_resout_gen(GenerateurPli([ADD, MUL]), FIB) is None
           and _resout_gen(GenerateurBoucle([ADD, MUL], [EST_POS]), FIB) is None)
    resultats.append(_check("MUR : le pli ET la boucle bornée (état UNIQUE) ne mintent pas fibonacci", mur))

    # 2. RÉCURRENCE (fib) : minté + généralise.
    g_fib = _resout_gen(rec, FIB)
    if g_fib:
        print(f"    fibonacci -> {[l.strip() for l in g_fib.splitlines() if 'a, b' in l or 'return' in l]}")
    resultats.append(_check("RÉCURRENCE (fib) : fibonacci minté ET généralise (held-out)", g_fib is not None))

    # 3. RÉCURRENCE (Lucas) : même schéma, inits différents.
    resultats.append(_check("RÉCURRENCE (Lucas) : Lucas minté ET généralise (schéma GÉNÉRAL, pas fib-hardcodé)",
                            _resout_gen(rec, LUCAS) is not None))

    # 4. HONNÊTE : sans add, pas de fibonacci.
    resultats.append(_check("HONNÊTE : sans l'op `add` (que `mul`), fibonacci n'est PAS minté (ne conjure pas l'op)",
                            _resout_gen(GenerateurRecurrence([MUL]), FIB) is None))

    # 5. VIVANT : l'orchestrateur (recurrence=True) résout fibonacci à l'étage recurrence.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, ops=[ADD, MUL], predicteur=Predicteur(store, types=TYPES_RICHES),
                                   recurrence=True)
        etage, _, code, _ = resoudre(orch, FIB, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (recurrence=True) résout fibonacci à l'étage `{etage}` (held-out compris)",
        code is not None and etage == "recurrence"))

    print()
    if all(resultats):
        print(f"RÉCURRENCE VALIDÉE — {len(resultats)}/{len(resultats)}. Le contrôle généralisé est amorcé : un schéma "
              f"figé de récurrence à DEUX états sur un compte franchit une classe que le pli/boucle (état unique) ne "
              f"pouvaient pas — fibonacci, Lucas — jugé sur held-out (vraie récurrence, pas overfit), honnête (sans op, "
              f"rien), et le modèle l'utilise (étage `recurrence`). Premier barreau du contrôle à état multiple ; le "
              f"`while`/condition (gcd) sera le schéma suivant, séparé et borné.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La récurrence ne franchit pas (encore) l'état multiple : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
