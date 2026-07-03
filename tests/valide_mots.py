"""
PARSING CHAÎNE — découper / transformer / rejoindre les MOTS (famille D : reverse_words).

La carte a montré HORS-PORTÉE `reverse_words` = inverser l'ordre des mots. Le substrat fait des méthodes unaires
(`.upper()`) ; il ne découpe pas. `GenerateurMots` admet `SEP.join(transform(args[0].split()))` (reverse / sorted).
reverse_words = ' '.join(s.split()[::-1]).

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (substrat)  : le substrat (méthodes unaires) ne minte pas reverse_words.
  2. MOTS (×2)       : `reverse_words` (mots inversés) ET `sort_words` (mots triés) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle) : l'orchestrateur (mots=True) résout reverse_words à l'étage `mots`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMots, GenerateurOrchestre, GenerateurSubstrat
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"mo/{fn}", point_entree=fn, prompt=f'def {fn}(s):\n    """..."""',
                 tests=tests, tests_held_out=held)


REVERSE_WORDS = _t("reverse_words",
    "def check(c):\n    assert c('a b c') == 'c b a'\n    assert c('hi yo') == 'yo hi'\n    assert c('x') == 'x'\ncheck(reverse_words)",
    "def check(c):\n    assert c('one two three') == 'three two one'\n    assert c('w x y z') == 'z y x w'\ncheck(reverse_words)")
SORT_WORDS = _t("sort_words",
    "def check(c):\n    assert c('c a b') == 'a b c'\n    assert c('hi') == 'hi'\ncheck(sort_words)",
    "def check(c):\n    assert c('z y x') == 'x y z'\n    assert c('b a') == 'a b'\ncheck(sort_words)")


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
    mots = GenerateurMots()

    resultats.append(_check("MUR : le substrat (méthodes unaires) ne minte pas reverse_words",
                            _resout_gen(GenerateurSubstrat(), REVERSE_WORDS) is None))

    g1 = _resout_gen(mots, REVERSE_WORDS)
    g2 = _resout_gen(mots, SORT_WORDS)
    if g1:
        print(f"    reverse_words -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    sort_words    -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("MOTS : `reverse_words` (inversés) ET `sort_words` (triés) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), mots=True)
        etage, _, code, _ = resoudre(orch, REVERSE_WORDS, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (mots=True) résout reverse_words à l'étage `{etage}`",
        code is not None and etage == "mots"))

    print()
    if all(resultats):
        print(f"MOTS VALIDÉ — {len(resultats)}/{len(resultats)}. Découper / transformer / rejoindre les mots : "
              f"reverse_words ET sort_words, held-out, honnête, utilisé par le modèle. **Famille D complète** "
              f"(count_vowels + positionnel + mots). Les 4 familles de la carte du plafond sont MOPPÉES.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
