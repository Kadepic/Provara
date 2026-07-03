"""
APPROFONDIR LA CARTE — quels murs sont MOUS (se ferment par seeding), lequel est le VRAI.

On ne se précipite pas vers la fusion verticale : on PROUVE d'abord, par la mesure, que
c'est bien elle qu'il faut. Trois faits, chacun falsifiable :

  A. La PORTÉE GRANDIT avec le store : plus de succès confirmés -> plus d'expressions
     atteignables par recombinaison. La maîtrise s'étend toute seule, sans mécanisme neuf.

  B. Le mur de VOCABULAIRE se ferme par SEEDING : une tâche hors-portée le devient dès
     qu'on sème un SIBLING qui apporte le fragment manquant — SANS jamais semer la tâche
     elle-même (c'est de la recombinaison cross-tâche, pas de la mémorisation). Mur MOU.

  C. Le mur de COMPOSITION ne se ferme PAS par seeding des PIÈCES : une tâche qui exige de
     COMBINER deux sous-compétences reste hors-portée même quand les deux pièces sont au
     store. La recombinaison du maison est d'ARITÉ UN (un squelette, un trou, un sens) :
     elle ne sait pas composer deux variations. Aucun fragment ne répare ça -> il faut un
     MÉCANISME : la fusion verticale (composer des succès confirmés en primitives). Le VRAI mur.

Critère de mort : si la portée ne grandit pas (A), si le sibling ne débloque pas la tâche
(B), ou si les pièces suffisent à composer sans mécanisme (C), un présupposé tombe.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import TYPES_RICHES, GenerateurRecombinant
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests):
    return Tache(id=f"carte/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# Succès confirmés (chacun apporte un/des fragment(s) au store).
SOLS = {
    "somme_carres":    ("def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n",
                        "def check(c):\n    assert c([1,2,3]) == 14\n    assert c([]) == 0\ncheck(somme_carres)"),
    "max_plus_un":     ("def max_plus_un(*args, **kwargs):\n    return max(x + 1 for x in args[0])\n",
                        "def check(c):\n    assert c([1,2,3]) == 4\n    assert c([0]) == 1\ncheck(max_plus_un)"),
    "compte_positifs": ("def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n",
                        "def check(c):\n    assert c([1,-2,3]) == 2\n    assert c([]) == 0\ncheck(compte_positifs)"),
    "max_cubes":       ("def max_cubes(*args, **kwargs):\n    return max(x ** 3 for x in args[0])\n",
                        "def check(c):\n    assert c([1,2]) == 8\n    assert c([3]) == 27\ncheck(max_cubes)"),
}

# Tâches CIBLES (jamais semées) — on teste seulement si elles tombent dans la portée.
CUBE_TOTAL = _t("cube_total",
                "def check(c):\n    assert c([1,2,3]) == 36\n    assert c([2]) == 8\ncheck(cube_total)")
CARRES_POSITIFS = _t("somme_carres_positifs",
                     "def check(c):\n    assert c([1,-2,3]) == 10\n    assert c([-1,-2]) == 0\n    assert c([2]) == 4\ncheck(somme_carres_positifs)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _seme(store, fn):
    sol, tests = SOLS[fn]
    t = _t(fn, tests)
    v = juge(sol, tests, LIM)
    assert v.passe, f"pré-condition : {fn}"
    store.ajoute(t, sol, v)


def _taille_portee(store):
    """Nombre d'expressions DISTINCTES atteignables par recombinaison (portée énumérée)."""
    sq, sens = GenerateurRecombinant(store, types=TYPES_RICHES)._pool()
    return len({s.replace("{C}", se) for s in sq for se in sens})


def _dans_portee(store, tache, n=2000):
    """La tâche tombe-t-elle dans la portée ? (un candidat énumérable passe le juge)."""
    g = GenerateurRecombinant(store, types=TYPES_RICHES)
    for code in g.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return True
    return False


def main() -> int:
    resultats = []

    # === A. La portée grandit avec le store ===
    print("A. La PORTÉE grandit à mesure qu'on confirme des succès :\n")
    tailles = []
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "a.jsonl")
        ordre = ["somme_carres", "max_plus_un", "compte_positifs", "max_cubes"]
        for i, fn in enumerate(ordre, 1):
            _seme(store, fn)
            taille = _taille_portee(store)
            tailles.append(taille)
            print(f"    {i} succès (+{fn:<16}) -> portée = {taille} expressions atteignables")
    print()
    croissante = all(tailles[i] <= tailles[i + 1] for i in range(len(tailles) - 1))
    resultats.append(_check(f"la portée grandit avec le store ({tailles[0]} -> {tailles[-1]}, non décroissante)",
                            croissante and tailles[-1] > tailles[0]))

    # === B. Le mur de VOCABULAIRE se ferme par seeding d'un sibling ===
    print("\nB. Le mur de VOCABULAIRE se ferme par seeding (sans semer la cible) :\n")
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "b.jsonl")
        _seme(store, "somme_carres")
        avant = _dans_portee(store, CUBE_TOTAL)
        print(f"    cube_total (= sum(x**3 ...)) AVANT  : {'DANS' if avant else 'HORS'} la portée")
        _seme(store, "max_cubes")   # sibling : apporte le fragment « x ** 3 »
        apres = _dans_portee(store, CUBE_TOTAL)
        print(f"    cube_total APRÈS seeding max_cubes  : {'DANS' if apres else 'HORS'} la portée "
              f"(recombiné : sum de somme_carres + « x**3 » de max_cubes)\n")
    resultats.append(_check("mur de VOCABULAIRE : HORS puis DANS après un sibling (mur MOU, fermé par seeding)",
                            (not avant) and apres))

    # === C. Le mur de COMPOSITION ne se ferme PAS par seeding des pièces ===
    print("\nC. Le mur de COMPOSITION résiste au seeding des pièces :\n")
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "c.jsonl")
        _seme(store, "somme_carres")      # pièce 1 : « x * x » (les carrés)
        _seme(store, "compte_positifs")   # pièce 2 : « if x > 0 » (le filtre positifs)
        compo = _dans_portee(store, CARRES_POSITIFS)
        print(f"    somme_carres_positifs (= sum(x*x for x in xs if x>0))")
        print(f"      les DEUX pièces (carrés + filtre positifs) sont au store -> {'DANS' if compo else 'HORS'} la portée")
        print(f"      raison : recombinaison d'arité UN (un seul trou) — elle ne sait pas COMBINER")
        print(f"      les deux variations. Aucun fragment ne répare ça : il faut COMPOSER.\n")
    resultats.append(_check("mur de COMPOSITION : reste HORS malgré les 2 pièces (le VRAI mur -> fusion verticale)",
                            not compo))

    print()
    if all(resultats):
        print(f"CARTE APPROFONDIE — {len(resultats)}/{len(resultats)}. Mesuré, pas supposé : la portée grandit "
              f"avec le store ; le mur de vocabulaire est MOU (le seeding le ferme) ; le mur de COMPOSITION "
              f"résiste au seeding des pièces -> c'est lui le vrai mur, et il appelle un MÉCANISME : la fusion "
              f"verticale (composer des succès confirmés en primitives). On y va sans se précipiter — c'est prouvé.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
