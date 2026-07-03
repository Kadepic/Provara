"""
TRANSFORMATION DE DICTIONNAIRE — réécrire un dict EXISTANT (front d'après, thème 8).

`GenerateurDictTransform` : `{KEY: VAL for k,v in args[0].items()}` (KEY ∈ {k,v}, VAL ∈ {k,v,v+v,v+1}).
invert_dict = {v:k} ; double_valeurs = {k:v+v}.

Critères de MORT :
  1. MUR ×2          : ni `dict-accu` ni `group-by` (qui CONSTRUISENT un dict depuis une liste/paires) ne mintent
                       invert_dict (transformer un dict DONNÉ).
  2. GÉNÉRAL ×2      : `invert_dict` ({v:k}) ET `double_valeurs` ({k:v+v}) mintés + GÉNÉRALISENT au held-out
                       adverse (vide -> {}, valeurs négatives/zéro, plusieurs clés).
  3. HONNÊTE         : ne résout PAS `somme_valeurs` = sum(d.values()) (réduction, pas une transformation dict->dict).
  4. VIVANT (modèle) : l'orchestrateur (dict_transform=True) résout invert_dict à l'étage `dict-transform`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurDictAccumulateur, GenerateurDictTransform, GenerateurGroupBy,
                        GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"dt/{fn}", point_entree=fn, prompt=f'def {fn}(d):\n    """..."""',
                 tests=tests, tests_held_out=held)


# {v: k} ; held-out adverse : vide -> {}, plusieurs clés, valeurs distinctes.
INVERT = _t("invert_dict",
    "def check(c):\n    assert c({'a':1,'b':2}) == {1:'a',2:'b'}\n    assert c({'x':5}) == {5:'x'}\ncheck(invert_dict)",
    "def check(c):\n    assert c({}) == {}\n    assert c({'a':1,'b':2,'c':3}) == {1:'a',2:'b',3:'c'}\ncheck(invert_dict)")

# {k: v+v} ; held-out adverse : vide, zéro, négatif.
DOUBLE_VAL = _t("double_valeurs",
    "def check(c):\n    assert c({'a':1,'b':2}) == {'a':2,'b':4}\n    assert c({'x':5}) == {'x':10}\ncheck(double_valeurs)",
    "def check(c):\n    assert c({}) == {}\n    assert c({'a':0}) == {'a':0}\n    assert c({'a':3,'b':-1}) == {'a':6,'b':-2}\ncheck(double_valeurs)")

# tâche dict hors-famille : réduire en un scalaire. La brique (dict->dict) ne doit PAS la résoudre.
SOMME_VAL = _t("somme_valeurs",
    "def check(c):\n    assert c({'a':1,'b':2}) == 3\n    assert c({'x':5}) == 5\ncheck(somme_valeurs)",
    "def check(c):\n    assert c({'a':10,'b':20,'c':30}) == 60\ncheck(somme_valeurs)")


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
    dt = GenerateurDictTransform()

    resultats.append(_check(
        "MUR ×2 : ni `dict-accu` ni `group-by` (construisent un dict depuis une liste) ne mintent invert_dict",
        _resout_gen(GenerateurDictAccumulateur(), INVERT) is None and _resout_gen(GenerateurGroupBy(), INVERT) is None))

    g1 = _resout_gen(dt, INVERT)
    g2 = _resout_gen(dt, DOUBLE_VAL)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `invert_dict` ({v:k}) ET `double_valeurs` ({k:v+v}) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : ne résout PAS `somme_valeurs` = sum(d.values()) (réduction, pas une transformation dict->dict)",
        _resout_gen(dt, SOMME_VAL) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), dict_transform=True)
        etage, _, code, _ = resoudre(orch, INVERT, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (dict_transform=True) résout invert_dict à l'étage `{etage}`",
        code is not None and etage == "dict-transform"))

    print()
    if all(resultats):
        print(f"DICT-TRANSFORM VALIDÉE — {len(resultats)}/{len(resultats)}. Réécriture d'un dict existant : "
              f"invert_dict ET double_valeurs, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
