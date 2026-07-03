"""
DOMAINE BINAIRE / BITS — opérations bit-à-bit (2026-06-17, élargir les domaines vérifiables). `GenerateurBits` =
binaire (`& | ^ << >>`) + unaire (popcount, puissance-de-2). Nouveau domaine : aucun étage ne fait d'arithmétique
binaire.

Critères de MORT (4) :
  1. MUR        : `multi-entrée` (compose les ops arithmétiques du registre : mul/add/sub/mod/max2/min2) ne minte
                  PAS `bit_xor` (`^` n'est pas une op du registre).
  2. GÉNÉRAL ×2 : `bit_xor` (binaire `^`) ET `popcount` (unaire) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `somme_carres` (arithmétique décimale, pas binaire).
  4. VIVANT    : l'orchestrateur (bits=True) résout `bit_xor` à l'étage `bits`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurBits, GenerateurMultiEntree, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

OPS = [("mul", "def mul(*args, **kwargs):\n    return args[0]*args[1]\n"),
       ("add", "def add(*args, **kwargs):\n    return args[0]+args[1]\n"),
       ("sub", "def sub(*args, **kwargs):\n    return args[0]-args[1]\n"),
       ("mod", "def mod(*args, **kwargs):\n    return args[0]%args[1]\n")]


def _t(fn, sig, tests, held):
    return Tache(id=f"bits/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


BIT_XOR = _t("bit_xor", "a, b",
    "def check(c):\n    assert c(5,3) == 6\n    assert c(12,10) == 6\ncheck(bit_xor)",
    "def check(c):\n    assert c(7,1) == 6\n    assert c(255,128) == 127\ncheck(bit_xor)")
POPCOUNT = _t("popcount", "n",
    "def check(c):\n    assert c(7) == 3\n    assert c(8) == 1\ncheck(popcount)",
    "def check(c):\n    assert c(255) == 8\n    assert c(0) == 0\ncheck(popcount)")
SOMME_CARRES = _t("somme_carres", "xs",
    "def check(c):\n    assert c([1,2,3]) == 14\ncheck(somme_carres)",
    "def check(c):\n    assert c([2,3]) == 13\ncheck(somme_carres)")


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def _resout(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    r = []
    bits = GenerateurBits()

    r.append(_check("MUR : `multi-entrée` (ops arithmétiques du registre) ne minte pas `bit_xor` (`^` absent)",
                    _resout(GenerateurMultiEntree(OPS), BIT_XOR) is None))

    r.append(_check("GÉNÉRAL ×2 : `bit_xor` (binaire `^`) ET `popcount` (unaire) mintés + held-out adverse",
                    _resout(bits, BIT_XOR) is not None and _resout(bits, POPCOUNT) is not None))

    r.append(_check("HONNÊTE : ne résout pas `somme_carres` (arithmétique décimale, pas binaire)",
                    _resout(bits, SOMME_CARRES) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), bits=True)
        e, _, code, _ = resoudre(orch, BIT_XOR, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (bits=True) résout `bit_xor` à l'étage `{e}`",
                    code is not None and e == "bits"))

    print()
    print("BITS / BINAIRE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
