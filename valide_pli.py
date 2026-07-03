"""
FUSION VERTICALE — 2e étage, variante 2b : COMBINATEURS d'ordre supérieur (le stateful pur).

Le séquençage (2a) franchit les pipelines, pas l'ÉTAT. Ici on REPLIE une opération binaire
CONFIRMÉE sur une séquence via deux combinateurs universels (`reduce`, `accumulate`). On vise
EXACTEMENT les deux murs structurels qu'avait isolés `valide_mur.py` :

  factorielle  = reduce(mul, range(1, n+1), 1)        (état : produit cumulé)
  max_courant  = list(accumulate(xs, max2))           (état : maximum glissant)

Opérations binaires confirmées (succès sur d'AUTRES tâches, à 2 arguments) :
  mul(a, b)  -> a * b
  max2(a, b) -> le plus grand des deux

On exige :
  1. LE MUR (rappel) : ni recombinaison, ni fusion d'expressions, ni séquençage (2a) ne résolvent
     factorielle — l'expression unique et la nidification d'unaires ne portent pas l'état.
  2. LE PLI FRANCHIT : `reduce(mul, range(1,n+1), 1)` résout factorielle ; `list(accumulate(xs, max2))`
     résout max_courant. Confirmé par le juge — les DEUX murs structurels mesurés tombent.
  3. HONNÊTETÉ : sans l'opération `mul`, le pli ne résout PLUS factorielle (il replie du confirmé,
     il n'invente pas l'opération).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import (GenerateurCompose, GenerateurFusion, GenerateurPli,
                        GenerateurRecombinant, TYPES_RICHES)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests):
    return Tache(id=f"pli/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


OPS = {
    "mul":  ("def mul(*args, **kwargs):\n    return args[0] * args[1]\n",
             "def check(c):\n    assert c(3,4) == 12\n    assert c(0,5) == 0\ncheck(mul)"),
    "max2": ("def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n",
             "def check(c):\n    assert c(3,4) == 4\n    assert c(5,1) == 5\ncheck(max2)"),
}

FACTORIELLE = _t("factorielle",
                 "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)")
MAX_COURANT = _t("max_courant",
                 "def check(c):\n    assert c([3,1,4,1,5]) == [3,3,4,4,5]\n    assert c([1]) == [1]\n    assert c([2,2]) == [2,2]\ncheck(max_courant)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _prevalide():
    for nom, (src, tests) in OPS.items():
        assert juge(src, tests, LIM).passe, f"opération {nom} doit passer"


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def main() -> int:
    _prevalide()
    resultats = []
    ops = [(nom, src) for nom, (src, _) in OPS.items()]

    # 1. Le mur : recombinaison, fusion d'expressions, séquençage (2a) — aucun ne porte l'état.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for nom, (src, tests) in OPS.items():
            store.ajoute(_t(nom, tests), src, juge(src, tests, LIM))
        ni_recomb = _resout(GenerateurRecombinant(store, types=TYPES_RICHES), FACTORIELLE) is None
        ni_fusion = _resout(GenerateurFusion(store), FACTORIELLE) is None
        ni_compose = _resout(GenerateurCompose(ops), FACTORIELLE) is None
    resultats.append(_check("LE MUR : recombinaison, fusion d'expressions ET séquençage (2a) échouent sur factorielle",
                            ni_recomb and ni_fusion and ni_compose))

    # 2. Le pli franchit les DEUX murs structurels mesurés.
    pli = GenerateurPli(ops)
    fact = _resout(pli, FACTORIELLE)
    mxc = _resout(pli, MAX_COURANT)
    if fact:
        print(f"    factorielle -> {fact.strip().splitlines()[-1].strip()}")
    if mxc:
        print(f"    max_courant -> {mxc.strip().splitlines()[-1].strip()}\n")
    resultats.append(_check("LE PLI : reduce(mul, range(1,n+1), 1) résout factorielle (état : produit cumulé)",
                            fact is not None))
    resultats.append(_check("LE PLI : list(accumulate(xs, max2)) résout max_courant (état : maximum glissant)",
                            mxc is not None))

    # 3. Honnêteté : sans l'opération `mul`, plus de factorielle.
    sans_mul = [(nom, src) for nom, src in ops if nom != "mul"]
    resultats.append(_check("HONNÊTETÉ : sans l'opération `mul`, le pli ne résout PLUS factorielle (replie, n'invente pas)",
                            _resout(GenerateurPli(sans_mul), FACTORIELLE) is None))

    print()
    if all(resultats):
        print(f"FUSION VERTICALE (combinateurs) VALIDÉE — {len(resultats)}/{len(resultats)}. En repliant une opération "
              f"confirmée par des combinateurs universels, on porte l'ÉTAT — les deux murs structurels mesurés "
              f"(factorielle, max courant) tombent. Reste maison, jugé par le réel, sans modèle externe.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
