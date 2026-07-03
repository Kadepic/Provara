"""
FUSION VERTICALE — 1er étage : fusion d'EXPRESSIONS (composer deux sous-compétences).

Le mur mesuré (`valide_carte.py`) : la recombinaison est d'ARITÉ UN (un trou) ; elle ne sait
pas COMBINER deux variations. La fusion la dépasse en composant deux succès confirmés qui
PARTAGENT un cadre d'itération : l'ÉLÉMENT de l'un + le FILTRE de l'autre.

Mise en scène : le store connaît deux succès sur D'AUTRES tâches, même cadre `sum(... for x in args[0] ...)` —
  A) somme_carres    -> sum(x * x for x in args[0])         (apporte l'ÉLÉMENT « x * x »)
  B) compte_positifs -> sum(1 for x in args[0] if x > 0)    (apporte le FILTRE « x > 0 »)

Cible C = somme_carres_positifs -> sum(x * x for x in args[0] if x > 0). On exige :

  1. RECOMBINAISON IMPUISSANTE : G5 (arité un) ne résout PAS C (le mur de composition, re-confirmé).
  2. FUSION RÉSOUT : en composant l'élément de A et le filtre de B sur le cadre partagé.
  3. HONNÊTETÉ : sans B (donc sans le filtre « x > 0 »), la fusion ne peut PLUS — elle compose
     du confirmé, elle n'invente pas.
  4. FRONTIÈRE MESURÉE (pour réévaluer l'étage suivant) : la fusion d'expressions ne franchit
     PAS le mur MULTI-ÉTAPES — factorielle (boucle à état) reste hors de portée. C'est la donnée
     qui dira si/quand passer aux primitives appelables (fusion verticale 2e étage).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import GenerateurFusion, GenerateurRecombinant, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held=""):
    return Tache(id=f"fus/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


A = _t("somme_carres", "def check(c):\n    assert c([1,2,3]) == 14\n    assert c([]) == 0\ncheck(somme_carres)")
A_SOL = "def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n"
B = _t("compte_positifs", "def check(c):\n    assert c([1,-2,3]) == 2\n    assert c([]) == 0\ncheck(compte_positifs)")
B_SOL = "def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n"

# Held-out ADVERSE : sum(x*x for x in xs if x>0).
#   [-5,5]->25 (négatif ignoré, pas 50) ; [3,-3,4]->25 ; []->0 ; [0,1,-1]->1 (0 exclu) ;
#   [10]->100 (singleton grand) ; [2,2,2]->12 (doublons).
# Tue : sum sans filtre (50 sur [-5,5]), count_positifs (1 sur [-5,5]), min(x)+1, somme brute, etc.
CIBLE = _t("somme_carres_positifs",
           "def check(c):\n    assert c([1,-2,3]) == 10\n    assert c([-1,-2]) == 0\n    assert c([2]) == 4\ncheck(somme_carres_positifs)",
           "def check(c):\n    assert c([-5,5]) == 25\n    assert c([3,-3,4]) == 25\n    assert c([]) == 0\n    assert c([0,1,-1]) == 1\n    assert c([10]) == 100\n    assert c([2,2,2]) == 12\ncheck(somme_carres_positifs)")
# Mur multi-étapes (frontière de l'étage 1) : factorielle exige une boucle à état.
FACT = _t("factorielle", "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _seme(store, tache, sol):
    v = juge(sol, tache.tests, LIM)
    assert v.passe, f"pré-condition : {tache.id}"
    store.ajoute(tache, sol, v)


def _resout(generateur, tache, n=200):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seme(store, A, A_SOL)
        _seme(store, B, B_SOL)
        print(f"Store : 2 succès, même cadre sum(... for x in args[0] ...) — A apporte l'élément, B le filtre.\n")

        # 1. Recombinaison (arité un) ne résout pas la composition.
        g5 = GenerateurRecombinant(store, types=TYPES_RICHES)
        resultats.append(_check("recombinaison (arité un) NE résout PAS somme_carres_positifs (le mur)",
                                _resout(g5, CIBLE) is None))

        # 2. Fusion résout en composant élément(A) + filtre(B).
        fus = GenerateurFusion(store)
        gagnant = _resout(fus, CIBLE)
        if gagnant:
            print(f"    fusion -> {gagnant.strip().splitlines()[-1].strip()}\n")
        resultats.append(_check("FUSION résout somme_carres_positifs (élément de A + filtre de B, cadre partagé)",
                                gagnant is not None))

        # 4. Frontière : la fusion d'expressions ne franchit PAS le multi-étapes.
        resultats.append(_check("FRONTIÈRE : la fusion d'expressions ne résout PAS factorielle (multi-étapes)",
                                _resout(fus, FACT) is None))

    # 3. Honnêteté : sans B (pas de filtre x>0), la fusion ne peut plus.
    with tempfile.TemporaryDirectory() as d:
        store_sansB = Store(Path(d) / "s2.jsonl")
        _seme(store_sansB, A, A_SOL)   # seulement A (élément, aucun filtre)
        fusB = GenerateurFusion(store_sansB)
        resultats.append(_check("sans B (donc sans le filtre « x > 0 »), la fusion ne résout PLUS (compose, n'invente pas)",
                                _resout(fusB, CIBLE) is None))

    print()
    if all(resultats):
        print(f"FUSION D'EXPRESSIONS VALIDÉE — {len(resultats)}/{len(resultats)}. On COMPOSE deux sous-compétences "
              f"confirmées (élément + filtre, cadre partagé) -> on franchit le mur de composition que la recombinaison "
              f"ne pouvait pas. Frontière mesurée : le multi-étapes (factorielle) reste pour l'étage suivant. "
              f"On réévalue B sur cette donnée — sans précipitation.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
