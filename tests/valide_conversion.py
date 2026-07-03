"""
CONVERSION DE BASE (2026-06-17, faculté « retranscription ») — déc↔bin↔hex. `GenerateurConversion`.

Critères de MORT (4) :
  1. MUR        : `bits` (bit-à-bit entier->entier) ne minte pas `vers_binaire` (entier->chaîne).
  2. GÉNÉRAL ×2 : `vers_binaire` (déc->bin) ET `depuis_binaire` (bin->déc) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `somme_carres`.
  4. VIVANT    : l'orchestrateur (conversion=True) résout `vers_binaire` à l'étage `conversion`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurBits, GenerateurConversion, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"conv/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


VBIN = _t("vers_binaire", "n",
    "def check(c):\n    assert c(5) == '101'\n    assert c(8) == '1000'\ncheck(vers_binaire)",
    "def check(c):\n    assert c(0) == '0'\n    assert c(255) == '11111111'\ncheck(vers_binaire)")
DBIN = _t("depuis_binaire", "s",
    "def check(c):\n    assert c('101') == 5\n    assert c('1000') == 8\ncheck(depuis_binaire)",
    "def check(c):\n    assert c('0') == 0\n    assert c('11111111') == 255\ncheck(depuis_binaire)")
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
    cv = GenerateurConversion()
    r.append(_check("MUR : `bits` (entier->entier) ne minte pas `vers_binaire` (entier->chaîne)",
                    _resout(GenerateurBits(), VBIN) is None))
    r.append(_check("GÉNÉRAL ×2 : `vers_binaire` ET `depuis_binaire` mintés + held-out adverse",
                    _resout(cv, VBIN) is not None and _resout(cv, DBIN) is not None))
    r.append(_check("HONNÊTE : ne résout pas `somme_carres`", _resout(cv, SOMME_CARRES) is None))
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), conversion=True)
        e, _, code, _ = resoudre(orch, VBIN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (conversion=True) résout `vers_binaire` à l'étage `{e}`",
                    code is not None and e == "conversion"))
    print()
    print("CONVERSION VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
