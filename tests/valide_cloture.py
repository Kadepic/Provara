"""
CLÔTURE — un mécanisme compose sur un atome INVENTÉ (invention -> registre -> composition).

`valide_invention_compounding` a fermé invention -> COMPOSITION (atome minté versé en primitive, nidifié).
Ici on ferme invention -> MÉCANISME op-consommateur : le moteur INVENTE une OP (`sub`, en mutant `add`),
la VERSE au registre des ops, et l'étage MULTI-ENTRÉE compose dessus — `ecart3(a,b,c) = a-b-c =
sub(sub(a,b), c)` — une tâche qu'AUCUNE des deux couches seule ne franchit :

  - l'INVENTION seule ne fait pas `ecart3` : c'est de l'arité 3, aucun atome à muter ne la donne ;
  - la MULTI-ENTRÉE seule ne fait pas `ecart3` : sans op de soustraction, `{add}` ne produit pas `a-b-c`.

Il faut les DEUX : inventer `sub`, puis composer dessus. C'est la boucle refermée — le moteur fabrique la
brique qui lui manque, et s'en sert pour franchir un mur. Jugé par le réel (held-out), sans modèle externe.

Critères de MORT :
  1. INVENTION : `sub` est minté (mutation de `add`) et GÉNÉRALISE (held-out).
  2. MUR       : sans `sub`, l'orchestrateur ne résout pas `ecart3` (multi-entrée sur {add} seul échoue).
  3. INVENTION SEULE INSUFFISANTE : muter un atome ne donne pas `ecart3` (arité 3) — il faut composer.
  4. CLÔTURE   : `sub` inventé versé en OP -> `ecart3` résolu à l'étage `multi-entrée` (sub(sub(a,b),c)).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import TYPES_RICHES, GenerateurInvention, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")


def _t(fn, sig, tests, held=""):
    return Tache(id=f"cl/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


SUB = _t("sub", "a, b",
         "def check(c):\n    assert c(5,3) == 2\n    assert c(0,0) == 0\n    assert c(10,4) == 6\ncheck(sub)",
         "def check(c):\n    assert c(7,1) == 6\n    assert c(-2,3) == -5\n    assert c(9,9) == 0\ncheck(sub)")
ECART3 = _t("ecart3", "a, b, c",
            "def check(c):\n    assert c(10,3,2) == 5\n    assert c(0,0,0) == 0\n    assert c(5,1,1) == 3\ncheck(ecart3)",
            "def check(c):\n    assert c(20,5,5) == 10\n    assert c(7,2,0) == 5\n    assert c(-1,-1,-1) == 1\ncheck(ecart3)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=600):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def _resout_escalade(orch, tache, k=600):
    for nom_etage, cands in orch.etages(tache.prompt, k):
        for code in cands:
            if juge(code, tache.tests, LIM).passe:
                return nom_etage
    return None


def main() -> int:
    resultats = []

    # 1. INVENTION : minter `sub` en mutant `add`, et vérifier qu'il généralise.
    sub_code = _resout(GenerateurInvention([ADD]), SUB)
    sub_ok = sub_code is not None and juge(sub_code, SUB.tests_held_out, LIM).passe
    if sub_code:
        print(f"    sub minté -> {sub_code.strip().splitlines()[-1].strip()}")
    resultats.append(_check("INVENTION : `sub` minté (mutation de `add`) et il GÉNÉRALISE (held-out)", sub_ok))

    # 3. INVENTION SEULE INSUFFISANTE : muter un atome ne donne pas ecart3 (arité 3).
    resultats.append(_check("INVENTION SEULE INSUFFISANTE : la mutation ne minte pas ecart3 (arité 3, il faut composer)",
                            _resout(GenerateurInvention([ADD]), ECART3) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        pred = Predicteur(store, types=TYPES_RICHES)

        # 2. MUR : orchestrateur SANS l'op inventée -> ecart3 hors-portée.
        orch_sans = GenerateurOrchestre(store, ops=[ADD], predicteur=pred)
        resultats.append(_check("MUR : sans `sub`, l'orchestrateur ne résout pas ecart3 (multi-entrée sur {add} seul)",
                                _resout_escalade(orch_sans, ECART3) is None))

        # 4. CLÔTURE : verser le `sub` INVENTÉ en OP, puis composer dessus (multi-entrée).
        orch_avec = GenerateurOrchestre(store, ops=[ADD], predicteur=pred)
        if sub_code:
            orch_avec.verse_op("sub", sub_code)        # l'op INVENTÉE rejoint le registre des ops
        etage = _resout_escalade(orch_avec, ECART3)
        resultats.append(_check(f"CLÔTURE : `sub` inventé versé en op -> ecart3 résolu à l'étage `{etage}` "
                                f"(sub(sub(a,b), c))", etage == "multi-entrée"))

    print()
    if all(resultats):
        print(f"BOUCLE INVENTION->MÉCANISME FERMÉE — {len(resultats)}/{len(resultats)}. Le moteur INVENTE l'op qui lui "
              f"manque (`sub`), la verse au registre, et un étage de MÉCANISME (multi-entrée) compose dessus pour "
              f"franchir une tâche qu'aucune couche seule ne pouvait. La dernière cause du plafond (ATOME absent) se "
              f"ferme EN INTERNE : inventer la brique, puis s'en servir. Jugé par le réel, sans modèle externe.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La boucle ne se ferme pas (encore) : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
