"""
GÉNÉRER-ET-TESTER — le n-ième entier satisfaisant un prédicat (dernière niche du thème II : nieme_premier).

`GenerateurGenererTester` admet `count=0; k=1; while count<n: k+=1; if pred(k): count+=1; return k` (le while est
cadré par le juge/timeout). nieme_premier = pred=is_prime ; nieme_pair = pred=is_pair. Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (récurrence/while) : la récurrence/while comptés ne mintent pas nieme_premier (pas de générer-tester-compter).
  2. GÉNÉRER-TESTER (×2)    : `nieme_premier` (is_prime) ET `nieme_pair` (is_pair) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle)        : l'orchestrateur (generer_tester=True) résout nieme_premier à l'étage `generer-tester`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurGenererTester, GenerateurOrchestre, GenerateurRecurrence
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

IS_PRIME = ("is_prime", "def is_prime(*args, **kwargs):\n    return args[0] > 1 and all(args[0] % i != 0 for i in range(2, args[0]))\n")
IS_PAIR = ("is_pair", "def is_pair(*args, **kwargs):\n    return args[0] % 2 == 0\n")
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")


def _t(fn, tests, held):
    return Tache(id=f"gt/{fn}", point_entree=fn, prompt=f'def {fn}(n):\n    """..."""',
                 tests=tests, tests_held_out=held)


NIEME_PREMIER = _t("nieme_premier",
    "def check(c):\n    assert c(1) == 2\n    assert c(2) == 3\n    assert c(3) == 5\ncheck(nieme_premier)",
    "def check(c):\n    assert c(4) == 7\n    assert c(5) == 11\ncheck(nieme_premier)")
NIEME_PAIR = _t("nieme_pair",
    "def check(c):\n    assert c(1) == 2\n    assert c(2) == 4\n    assert c(3) == 6\ncheck(nieme_pair)",
    "def check(c):\n    assert c(5) == 10\n    assert c(10) == 20\ncheck(nieme_pair)")


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
    gt = GenerateurGenererTester([IS_PRIME, IS_PAIR])

    resultats.append(_check("MUR : la récurrence (compte) ne minte pas nieme_premier (pas de générer-tester)",
                            _resout_gen(GenerateurRecurrence([ADD]), NIEME_PREMIER) is None))

    g1 = _resout_gen(gt, NIEME_PREMIER)
    g2 = _resout_gen(gt, NIEME_PAIR)
    if g1:
        print(f"    nieme_premier  OK (générer-tester avec is_prime)")
    resultats.append(_check("GÉNÉRER-TESTER : `nieme_premier` (is_prime) ET `nieme_pair` (is_pair) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicats=[IS_PRIME, IS_PAIR],
                                   predicteur=Predicteur(store, types=TYPES_RICHES), generer_tester=True)
        etage, _, code, _ = resoudre(orch, NIEME_PREMIER, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (generer_tester=True) résout nieme_premier à l'étage `{etage}`",
        code is not None and etage == "generer-tester"))

    print()
    if all(resultats):
        print(f"GÉNÉRER-TESTER VALIDÉ — {len(resultats)}/{len(resultats)}. Le n-ième entier satisfaisant un prédicat "
              f"(crible/recherche) : nieme_premier ET nieme_pair, held-out, honnête, utilisé par le modèle. "
              f"**Le prochain front est MOPÉ à 100 %** (thèmes I + II complets).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
