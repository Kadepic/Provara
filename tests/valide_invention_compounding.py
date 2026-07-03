"""
BOUCLE FERMÉE : invention -> compounding. Le moteur s'enrichit d'un atome NEUF, puis COMPOSE dessus.

`valide_invention` a prouvé qu'on MINTE un atome (cube = x*x*x). `valide_compounding*` a prouvé que le
passé nourrit le présent. Ici on les boucle : un atome MINTÉ devient une brique du registre, et une tâche
PLUS PROFONDE devient atteignable *parce que* l'atome inventé a été déposé — ce que ni la composition seule
(sans l'atome) ni l'invention seule (une seule mutation) ne peuvent.

Cible profonde : cube_plus_un(x) = x**3 + 1.
  - SANS l'atome inventé : hors-portée (x³+1 n'est pas composable depuis {carre, incremente, mul}).
  - L'invention SEULE ne le minte pas non plus (x³+1 = DEUX écarts au confirmé, hors d'une mutation simple).
  - Il faut : INVENTER `cube` (mutation de `carre`), le VERSER au registre, puis COMPOSER `incremente ∘ cube`.

A/B (seul diffère : l'atome minté est-il versé au registre ?) :
  1. INVENTION   : `cube` est minté et GÉNÉRALISE (held-out).
  2. MUR         : sans `cube` versé, l'orchestrateur ne résout PAS cube_plus_un.
  3. INVENTION SEULE NE SUFFIT PAS : muter le confirmé ne minte pas x³+1 d'un coup (c'est la COMPOSITION
                   sur l'inventé qui ferme, pas une invention « magique »).
  4. BOUCLE      : `cube` minté versé au registre -> cube_plus_un résolu à l'étage `composition`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import TYPES_RICHES, GenerateurInvention, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
from valide_invention import CARRE, CUBE, MUL

LIM = Limites(temps_s=3, cpu_s=2)
INCREMENTE = ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")


def _t(fn, arg, tests, held):
    return Tache(id=f"invc/{fn}", point_entree=fn, prompt=f'def {fn}({arg}):\n    """..."""',
                 tests=tests, tests_held_out=held)


CUBE_PLUS_UN = _t("cube_plus_un", "x",
                  "def check(c):\n    assert c(2) == 9\n    assert c(3) == 28\n    assert c(0) == 1\n    assert c(1) == 2\ncheck(cube_plus_un)",
                  "def check(c):\n    assert c(4) == 65\n    assert c(5) == 126\n    assert c(-2) == -7\ncheck(cube_plus_un)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def _resout_escalade(orch, tache, k=400):
    for nom_etage, cands in orch.etages(tache.prompt, k):
        for code in cands:
            if juge(code, tache.tests, LIM).passe:
                return nom_etage
    return None


def main() -> int:
    resultats = []

    # 1. INVENTION : minter `cube` (mutation de `carre`) et vérifier qu'il généralise.
    cube_code = _resout(GenerateurInvention([CARRE, MUL]), CUBE)
    cube_ok = cube_code is not None and juge(cube_code, CUBE.tests_held_out, LIM).passe
    if cube_code:
        print(f"    cube minté -> {cube_code.strip().splitlines()[-1].strip()}")
    resultats.append(_check("INVENTION : `cube` minté et il GÉNÉRALISE (held-out)", cube_ok))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        pred = Predicteur(store, types=TYPES_RICHES)

        # 2. MUR : orchestrateur SANS l'atome inventé -> cube_plus_un hors-portée.
        orch_sans = GenerateurOrchestre(store, primitives=[CARRE, INCREMENTE], ops=[MUL], predicteur=pred)
        mur = _resout_escalade(orch_sans, CUBE_PLUS_UN) is None
        resultats.append(_check("MUR : sans `cube` versé, l'orchestrateur ne résout pas cube_plus_un", mur))

        # 3. INVENTION SEULE ne minte pas x³+1 d'un coup (mutation simple du confirmé).
        inv_seule = _resout(GenerateurInvention([CARRE, INCREMENTE, MUL]), CUBE_PLUS_UN)
        resultats.append(_check("INVENTION SEULE INSUFFISANTE : muter le confirmé ne minte pas x³+1 (il faut composer)",
                                inv_seule is None))

        # 4. BOUCLE : verser le `cube` minté au registre, puis composer dessus.
        orch_avec = GenerateurOrchestre(store, primitives=[CARRE, INCREMENTE], ops=[MUL], predicteur=pred)
        if cube_code:
            orch_avec.verse_primitive("cube", cube_code)   # l'atome INVENTÉ rejoint le registre
        etage = _resout_escalade(orch_avec, CUBE_PLUS_UN)
        resultats.append(_check(f"BOUCLE : `cube` inventé versé -> cube_plus_un résolu à l'étage `{etage}` "
                                f"(incremente ∘ cube)", etage == "composition"))

    print()
    if all(resultats):
        print(f"BOUCLE INVENTION->COMPOUNDING FERMÉE — {len(resultats)}/{len(resultats)}. Le moteur INVENTE un "
              f"atome neuf (cube), le verse au registre, et COMPOSE dessus pour atteindre une tâche que ni la "
              f"composition seule ni l'invention seule ne pouvaient. Le passé qu'il s'est CRÉÉ nourrit le présent — "
              f"auto-enrichissement réel, interne, jugé par le réel.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La boucle ne se ferme pas (encore) : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
