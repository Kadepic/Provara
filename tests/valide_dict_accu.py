"""
DICT comme ACCUMULATEUR — bâtir un dictionnaire clé -> mesure (thème I : word_count).

L'escalade a confirmé HORS-PORTÉE `word_count` (dict des occurrences). Le moteur produit des scalaires/listes,
pas des dicts. `GenerateurDictAccumulateur` admet `{k: REDUC(k) for k in set(args[0])}`. word_count =
{w: mots.count(w) for w in set(mots)}.

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (fusion-collections) : la fusion set/dict (élément du store) ne minte pas word_count.
  2. DICT-ACCU (×2)           : `word_count` (count) ET `premiere_position` (index) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle)          : l'orchestrateur (dict_accu=True) résout word_count à l'étage `dict-accu`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurDictAccumulateur, GenerateurFusion, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"da/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


WORD_COUNT = _t("word_count",
    "def check(c):\n    assert c(['a','b','a']) == {'a':2,'b':1}\n    assert c(['x']) == {'x':1}\n    assert c(['z','z','z']) == {'z':3}\ncheck(word_count)",
    "def check(c):\n    assert c(['a','a','b','b']) == {'a':2,'b':2}\n    assert c([]) == {}\ncheck(word_count)")
PREM_POS = _t("premiere_position",
    "def check(c):\n    assert c(['a','b','a']) == {'a':0,'b':1}\n    assert c(['x','y']) == {'x':0,'y':1}\ncheck(premiere_position)",
    "def check(c):\n    assert c(['p','q','p','r']) == {'p':0,'q':1,'r':3}\ncheck(premiere_position)")


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
    da = GenerateurDictAccumulateur()

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        # un succès dict-comp au store (élément simple) -> la fusion peut en tirer, mais pas le count.
        src = "def carres_dict(*args, **kwargs):\n    return {x: x * x for x in args[0]}\n"
        tst = "def check(c):\n    assert c([1,2]) == {1:1, 2:4}\ncheck(carres_dict)"
        store.ajoute(Tache(id="cd", point_entree="carres_dict", prompt="", tests=tst), src, juge(src, tst, LIM))
        mur = _resout_gen(GenerateurFusion(store), WORD_COUNT) is None
    resultats.append(_check("MUR : la fusion set/dict (élément du store) ne minte pas word_count (valeur = count du tout)",
                            mur))

    g1 = _resout_gen(da, WORD_COUNT)
    g2 = _resout_gen(da, PREM_POS)
    if g1:
        print(f"    word_count        -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    premiere_position -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("DICT-ACCU : `word_count` (count) ET `premiere_position` (index) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), dict_accu=True)
        etage, _, code, _ = resoudre(orch, WORD_COUNT, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (dict_accu=True) résout word_count à l'étage `{etage}`",
        code is not None and etage == "dict-accu"))

    print()
    if all(resultats):
        print(f"DICT-ACCUMULATEUR VALIDÉ — {len(resultats)}/{len(resultats)}. Bâtir un dict clé->mesure : word_count "
              f"ET premiere_position, held-out, honnête, utilisé par le modèle. Thème I avance (imbriqué + dict ; "
              f"reste group-by).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
