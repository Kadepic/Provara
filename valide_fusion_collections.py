"""
ÉLARGIR L'ÉTAGE 1 — la fusion d'expressions aux compréhensions ENSEMBLE et DICT (vocabulaire).

L'étage 1 (`GenerateurFusion`) composait l'ÉLÉMENT d'un succès avec le FILTRE d'un autre, sur un cadre
PARTAGÉ — mais seulement pour deux formes : agrégée `AGG(elt for v in it [if f])` et liste `[elt for ...]`.
Les compréhensions d'ENSEMBLE `{elt for ...}` et de DICT `{k: v for ...}` n'étaient PAS du vocabulaire :
leur cadre n'était pas miné, donc la fusion ne pouvait pas les composer. (Mesuré avant de coder : `join`,
`upper`, `set`, `sorted(set(...))` sont déjà des `Call` -> déjà recombinables ; le VRAI trou = les
compréhensions set/dict.)

On élargit `_pieces_comprehension`/`_reconstruit_cadre` (deux formes en plus), **togglable** (`collections=`,
le levier de l'A/B) — SANS toucher au moteur de fusion lui-même. L'A/B isole exactement l'élargissement.

Critères de MORT (sur deux domaines, ensemble + dict) :
  1. MUR (set)      : sans le vocabulaire, la fusion n'atteint PAS `{x*x for x in xs if x%2==0}`
                      (élément `x*x` d'un succès + filtre `x%2==0` d'un autre, cadre ENSEMBLE partagé).
  2. ÉLARGI (set)   : avec le vocabulaire, elle l'atteint ET ça GÉNÉRALISE (held-out).
  3. MUR (dict)     : sans, n'atteint PAS `{x: x*x for x in xs if x%2==0}`.
  4. ÉLARGI (dict)  : avec, l'atteint ET généralise.
  5. HONNÊTETÉ      : sans la pièce FILTRE au store (retirée), même élargie la fusion n'atteint PAS la cible
                      — elle COMPOSE des pièces confirmées de cadre compatible, elle ne conjure rien.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import GenerateurFusion
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"fc/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


def _seed(fn, expr):
    return (fn, f"def {fn}(*args, **kwargs):\n    return {expr}\n")


# --- Pièces confirmées : un succès apporte l'ÉLÉMENT, l'autre le FILTRE, même cadre -------------
# Cadre ENSEMBLE {... for x in args[0]} : carrés (élément x*x) + pairs (filtre x%2==0).
SET_ELEMENT = _seed("carres_uniques", "{x * x for x in args[0]}")
SET_FILTRE  = _seed("pairs_uniques",  "{x for x in args[0] if x % 2 == 0}")
# Cadre DICT {... for x in args[0]} : carrés (élément x: x*x) + pairs (filtre x%2==0).
DICT_ELEMENT = _seed("dict_carres", "{x: x * x for x in args[0]}")
DICT_FILTRE  = _seed("dict_pairs",  "{x: x for x in args[0] if x % 2 == 0}")

# --- Cibles : la fusion des deux pièces (que ni l'une ni l'autre seule ne résout) ---------------
SET_CIBLE = _t("carres_pairs_set",
    "def check(c):\n    assert c([1,2,3,4]) == {4, 16}\n    assert c([1,3]) == set()\ncheck(carres_pairs_set)",
    "def check(c):\n    assert c([2,4,6]) == {4, 16, 36}\n    assert c([2,2,4]) == {4, 16}\n    assert c([]) == set()\ncheck(carres_pairs_set)")
DICT_CIBLE = _t("carres_pairs_dict",
    "def check(c):\n    assert c([1,2,3,4]) == {2: 4, 4: 16}\n    assert c([1,3]) == {}\ncheck(carres_pairs_dict)",
    "def check(c):\n    assert c([2,6]) == {2: 4, 6: 36}\n    assert c([3]) == {}\n    assert c([]) == {}\ncheck(carres_pairs_dict)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _store(d, suffixe, pieces):
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    for fn, src in pieces:
        v = juge(src, f"def check(c):\n    assert True\ncheck({fn})", LIM)
        assert v.passe, f"seed {fn}"
        store.ajoute(_t(fn, "", ""), src, v)
    return store


def _resout(store, tache, collections):
    fus = GenerateurFusion(store, collections=collections)
    for code in fus.propose(tache.prompt, 400):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def _generalise(code, tache):
    return code is not None and juge(code, tache.tests_held_out, LIM).passe


def main() -> int:
    resultats = []
    with tempfile.TemporaryDirectory() as d:
        store_set = _store(d, "set", [SET_ELEMENT, SET_FILTRE])
        store_dict = _store(d, "dict", [DICT_ELEMENT, DICT_FILTRE])
        store_set_amputé = _store(d, "setamp", [SET_ELEMENT])   # sans la pièce FILTRE

        # 1. MUR (set) : sans le vocabulaire collections, hors-portée.
        resultats.append(_check(
            "MUR (set) : sans le vocabulaire set/dict, la fusion n'atteint PAS `{x*x for x in xs if x%2==0}`",
            _resout(store_set, SET_CIBLE, collections=False) is None))

        # 2. ÉLARGI (set) : avec, atteint + généralise.
        g_set = _resout(store_set, SET_CIBLE, collections=True)
        if g_set:
            print(f"    fusionné (set) -> {g_set.strip().splitlines()[-1].strip()}")
        resultats.append(_check(
            "ÉLARGI (set) : avec le vocabulaire, la fusion atteint la cible ET passe le HELD-OUT",
            _generalise(g_set, SET_CIBLE)))

        # 3. MUR (dict) : sans, hors-portée.
        resultats.append(_check(
            "MUR (dict) : sans le vocabulaire, la fusion n'atteint PAS `{x: x*x for x in xs if x%2==0}`",
            _resout(store_dict, DICT_CIBLE, collections=False) is None))

        # 4. ÉLARGI (dict) : avec, atteint + généralise.
        g_dict = _resout(store_dict, DICT_CIBLE, collections=True)
        if g_dict:
            print(f"    fusionné (dict) -> {g_dict.strip().splitlines()[-1].strip()}")
        resultats.append(_check(
            "ÉLARGI (dict) : avec le vocabulaire, la fusion atteint la cible ET passe le HELD-OUT",
            _generalise(g_dict, DICT_CIBLE)))

        # 5. HONNÊTETÉ : sans la pièce filtre, même élargie elle ne conjure pas.
        resultats.append(_check(
            "HONNÊTETÉ : sans la pièce FILTRE au store, même élargie la fusion n'atteint PAS la cible "
            "(elle compose des pièces confirmées, elle ne conjure rien)",
            _resout(store_set_amputé, SET_CIBLE, collections=True) is None))

    print()
    if all(resultats):
        print(f"VOCABULAIRE ÉLARGI VALIDÉ — {len(resultats)}/{len(resultats)}. L'étage 1 (fusion d'expressions) "
              f"couvre maintenant les compréhensions d'ENSEMBLE et de DICT, pas seulement agrégée/liste : le moteur "
              f"compose l'élément d'un succès avec le filtre d'un autre sur un cadre set/dict partagé, et atteint des "
              f"tâches aujourd'hui hors-portée — sans qu'une ligne du moteur de fusion ne change (juste le vocabulaire, "
              f"togglable). Honnête : il ne compose que des pièces confirmées. (Bonus : ces nouveaux cadres créent "
              f"des concepts -> rapproche le réveil de l'abstraction parkée.)")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. L'élargissement ne franchit pas (encore) : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
