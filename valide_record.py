"""
RECORD À COMPLÉTUDE GRADUABLE — 1ʳᵉ brique du FRONT GÉNÉRATIF (2026-06-17, vision Yohan « sélectionner ce qu'on
veut : bonne réponse OU complète »). `GenerateurRecord` émet les préfixes d'un vocabulaire ordonné -> le moteur
produit EXACTEMENT la complétude demandée par la spec, chaque niveau étant un record CORRECT (pas une coïncidence :
1er terrain où le gradient de richesse est génuine).

Critères de MORT (4) :
  1. MUR                  : ni `dict-accu` ni `group-by` (dicts CLÉS-DONNÉES : fréquences/groupes) ne mintent un
                           record CLÉS-FIXES (`resume`).
  2. SÉLECTION-COMPLÉTUDE : `record` minte `resume` aux 4 complétudes (1->4 champs), CHACUNE exacte + held-out adverse
                           -> on sélectionne ce qu'on veut, et chaque réponse est correcte (gradient génuine).
  3. HONNÊTE              : ne résout pas `word_count` (dict clés-DONNÉES, hors-famille record).
  4. VIVANT              : l'orchestrateur (record=True) résout `resume` à l'étage `record`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurDictAccumulateur, GenerateurGroupBy,
                        GenerateurOrchestre, GenerateurRecord)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"rec/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests, tests_held_out=held)


# Specs à complétude CROISSANTE (exact dict). Held-out = MÊME complétude, valeurs DIFFÉRENTES (généralisation).
RESUME = {
    1: _t("resume", "def check(c):\n    assert c([1,2,3]) == {'somme': 6}\ncheck(resume)",
          "def check(c):\n    assert c([5,5]) == {'somme': 10}\n    assert c([7]) == {'somme': 7}\ncheck(resume)"),
    2: _t("resume", "def check(c):\n    assert c([1,2,3]) == {'somme': 6, 'n': 3}\ncheck(resume)",
          "def check(c):\n    assert c([4,6]) == {'somme': 10, 'n': 2}\n    assert c([9]) == {'somme': 9, 'n': 1}\ncheck(resume)"),
    3: _t("resume", "def check(c):\n    assert c([1,2,3]) == {'somme': 6, 'n': 3, 'max': 3}\ncheck(resume)",
          "def check(c):\n    assert c([4,1,4]) == {'somme': 9, 'n': 3, 'max': 4}\ncheck(resume)"),
    4: _t("resume", "def check(c):\n    assert c([1,2,3]) == {'somme': 6, 'n': 3, 'max': 3, 'min': 1}\ncheck(resume)",
          "def check(c):\n    assert c([4,1,4]) == {'somme': 9, 'n': 3, 'max': 4, 'min': 1}\ncheck(resume)"),
}
WORDCOUNT = _t("word_count", "def check(c):\n    assert c(['a','b','a']) == {'a': 2, 'b': 1}\ncheck(word_count)",
               "def check(c):\n    assert c(['z','z']) == {'z': 2}\ncheck(word_count)")


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
    rec = GenerateurRecord()

    r.append(_check("MUR : ni `dict-accu` ni `group-by` (dicts clés-DONNÉES) ne mintent le record clés-fixes `resume`",
                    _resout(GenerateurDictAccumulateur(), RESUME[4]) is None
                    and _resout(GenerateurGroupBy(), RESUME[4]) is None))

    selection = all(_resout(rec, RESUME[L]) is not None for L in (1, 2, 3, 4))
    r.append(_check("SÉLECTION-COMPLÉTUDE : `record` minte `resume` aux 4 complétudes (1->4 champs), chacune exacte "
                    "+ held-out -> on choisit ce qu'on veut, chaque réponse correcte", selection))

    r.append(_check("HONNÊTE : ne résout pas `word_count` (dict clés-DONNÉES, hors-famille record)",
                    _resout(rec, WORDCOUNT) is None))

    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), record=True)
        e, _, code, _ = resoudre(orch, RESUME[4], LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (record=True) résout `resume` (4 champs) à l'étage `{e}`",
                    code is not None and e == "record"))

    print()
    print("RECORD GÉNÉRATIF VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
