"""
COMPTAGE PAR APPARTENANCE — `sum(c in LIT for c in s)` (famille D : count_vowels).

La carte a montré HORS-PORTÉE `count_vowels` = nombre de voyelles. Le substrat énumérait l'appartenance en
`any`/`all` (booléen global) ; on ajoute la forme de COMPTAGE `sum(c in {lit} for c in args[0])` — somme des
booléens = nombre de caractères dans le littéral. count_vowels = `sum(c in 'aeiou' for c in s)`.

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (map-repli)  : le map-repli (sum(prim(x))) ne minte pas count_vowels (pas d'atome voyelle par caractère).
  2. COMPTAGE         : le substrat minte `count_vowels` (forme sum-appartenance) + GÉNÉRALISE.
  3. HONNÊTE          : sans le littéral `'aeiou'`, count_vowels n'est PAS atteint.
  4. VIVANT (modèle)  : l'orchestrateur (substrat=True) résout count_vowels à l'étage `substrat`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMapRepli, GenerateurOrchestre, GenerateurSubstrat
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"cm/{fn}", point_entree=fn, prompt=f'def {fn}(s):\n    """..."""',
                 tests=tests, tests_held_out=held)


COUNT_VOWELS = _t("count_vowels",
    "def check(c):\n    assert c('chat') == 1\n    assert c('aeiou') == 5\n    assert c('xyz') == 0\ncheck(count_vowels)",
    "def check(c):\n    assert c('hello') == 2\n    assert c('sky') == 0\n    assert c('aaa') == 3\ncheck(count_vowels)")

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")


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

    # 1. MUR : le map-repli ne minte pas count_vowels (pas d'atome voyelle par caractère).
    resultats.append(_check("MUR : le map-repli (sum(prim(x))) ne minte pas count_vowels",
                            _resout_gen(GenerateurMapRepli([CARRE]), COUNT_VOWELS) is None))

    # 2. COMPTAGE : le substrat (forme sum-appartenance) minte count_vowels + généralise.
    g = _resout_gen(GenerateurSubstrat(), COUNT_VOWELS)
    if g:
        print(f"    count_vowels -> {g.strip().splitlines()[-1].strip()}")
    resultats.append(_check("COMPTAGE : le substrat minte `count_vowels` (sum(c in 'aeiou' for c in s)) + généralise",
                            g is not None))

    # 3. HONNÊTE : sans le littéral 'aeiou', count_vowels hors-portée.
    resultats.append(_check("HONNÊTE : sans le littéral `'aeiou'`, count_vowels n'est PAS atteint",
                            _resout_gen(GenerateurSubstrat(litteraux=("'0123456789'",)), COUNT_VOWELS) is None))

    # 4. VIVANT : l'orchestrateur (substrat=True) résout count_vowels à l'étage substrat.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), substrat=True)
        etage, _, code, _ = resoudre(orch, COUNT_VOWELS, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (substrat=True) résout count_vowels à l'étage `{etage}`",
        code is not None and etage == "substrat"))

    print()
    if all(resultats):
        print(f"COMPTAGE PAR APPARTENANCE VALIDÉ — {len(resultats)}/{len(resultats)}. `count_vowels` débloqué via la "
              f"forme sum-appartenance du substrat, jugé held-out, honnête, utilisé par le modèle. Famille D amorcée.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Le comptage par appartenance ne franchit pas (encore) : RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
