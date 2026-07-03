"""
STRESS de JOINTURE PROFONDE — mettre la brique à l'épreuve (consigne Yohan : prouver les dires par des tests durs).

Ma claim après refonte était « couverture standalone inchangée ». À PROUVER. Ce test exige la couverture COMPLÈTE
de la classe « jointure positionnelle » : beaucoup d'agrégats-pairs, transforms SYMÉTRIQUES *et* ASYMÉTRIQUES sur
premier/dernier — tout au HELD-OUT — + une frontière honnête (jointure profonde NON positionnelle = déléguée au
compounding, hors-portée standalone, et c'est assumé).

Si la version symétrique-seule échoue sur l'asymétrique, c'est un RÉSULTAT : la refonte avait réduit la couverture,
et il faut la version positionnelle GÉNÉRALE (asymétrique incluse), toujours lean (O(prims²)).
"""

from __future__ import annotations

from generateur import GenerateurJointureProfonde
from juge import Limites, juge
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")
DOUBLE = ("double", "def double(*args, **kwargs):\n    return args[0] + args[0]\n")
INCR = ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
SUB = ("sub", "def sub(*args, **kwargs):\n    return args[0] - args[1]\n")
PRIMS = [CARRE, DOUBLE, INCR]
OPS = [MUL, ADD, SUB]


def _t(fn, tests, held):
    return Tache(id=f"jps/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests, tests_held_out=held)


# (description, tests, held-out, classe). 'identité' = pas de transform.
CAS = [
    # --- agrégats-pairs ---
    ("max-min (sub)", "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,5]) == 0\ncheck(f)", "def check(c):\n    assert c([0,10,5]) == 10\n    assert c([7]) == 0\ncheck(f)", "agrégat"),
    ("sum-min (sub)", "def check(c):\n    assert c([1,2,3]) == 5\n    assert c([4,4]) == 4\ncheck(f)", "def check(c):\n    assert c([0,0,5]) == 5\n    assert c([3,1]) == 3\ncheck(f)", "agrégat"),
    ("max-sum (sub)", "def check(c):\n    assert c([1,2,3]) == -3\n    assert c([5,0]) == 0\ncheck(f)", "def check(c):\n    assert c([2,2]) == -2\ncheck(f)", "agrégat"),
    # --- transforms SYMÉTRIQUES sur premier/dernier ---
    ("carre(first)*carre(last)", "def check(c):\n    assert c([2,3]) == 36\n    assert c([1,4]) == 16\ncheck(f)", "def check(c):\n    assert c([2,5]) == 100\n    assert c([1,1,1,4]) == 16\ncheck(f)", "symétrique"),
    ("double(first)+double(last)", "def check(c):\n    assert c([2,3]) == 10\n    assert c([5,1]) == 12\ncheck(f)", "def check(c):\n    assert c([0,4]) == 8\n    assert c([3,3]) == 12\ncheck(f)", "symétrique"),
    # --- transforms ASYMÉTRIQUES sur premier/dernier (le cas qui révèle la réduction) ---
    ("carre(first)*double(last)", "def check(c):\n    assert c([2,3]) == 24\n    assert c([1,5]) == 10\ncheck(f)", "def check(c):\n    assert c([3,1]) == 18\n    assert c([2,2,2,4]) == 32\ncheck(f)", "asymétrique"),
    ("incremente(first)+carre(last)", "def check(c):\n    assert c([2,3]) == 12\n    assert c([0,4]) == 17\ncheck(f)", "def check(c):\n    assert c([5,1]) == 7\ncheck(f)", "asymétrique"),
    ("first*carre(last)", "def check(c):\n    assert c([2,3]) == 18\n    assert c([5,2]) == 20\ncheck(f)", "def check(c):\n    assert c([3,4]) == 48\ncheck(f)", "asymétrique"),
]


def _resout(gen, tache, n=600):
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and juge(code, tache.tests_held_out, LIM).passe:
            return True
    return False


def main() -> int:
    gen = GenerateurJointureProfonde(PRIMS, OPS)
    par_classe = {}
    print(f"  {'cas':<32}{'classe':<14}{'résolu (held-out)'}")
    print("  " + "-" * 62)
    for desc, tst, held, classe in CAS:
        ok = _resout(gen, _t("f", tst, held))
        par_classe.setdefault(classe, []).append(ok)
        print(f"  {desc:<32}{classe:<14}{'OK' if ok else 'HORS-PORTÉE'}")

    print()
    total = sum(all(v) for v in par_classe.values())
    for classe, oks in par_classe.items():
        print(f"  classe {classe:<12} : {sum(oks)}/{len(oks)} couverts")
    couvert = all(all(v) for v in par_classe.values())
    print()
    if couvert:
        print(f"STRESS PASSÉ — toutes les classes (agrégat, symétrique, ASYMÉTRIQUE) couvertes au held-out. La jointure "
              f"positionnelle est COMPLÈTE (et lean). Claim prouvée.")
        return 0
    manquantes = [classe for classe, oks in par_classe.items() if not all(oks)]
    print(f"STRESS RÉVÈLE UNE RÉDUCTION — classes non couvertes : {manquantes}. La refonte symétrique-seule était trop "
          f"étroite. À corriger : version positionnelle GÉNÉRALE (transforms asymétriques f(first) op g(last)), "
          f"toujours O(prims²). C'est un RÉSULTAT — on ne se ment pas.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
