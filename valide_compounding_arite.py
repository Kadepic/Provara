"""
COMPOUNDING de l'ARITÉ 2 — un composé d'arité-2 nourrit le présent (cap 2, suite).

`valide_jointure` a prouvé que l'étage `jointure` franchit l'arité 2 (`op(p1(x), p2(x))`).
`valide_compounding` a prouvé que le passé nourrit le présent pour les tours UNAIRES. Ici on
boucle les deux : une JOINTURE confirmée devient une brique (la rétroaction la verse comme
primitive — elle est unaire-appelable `g(xs)`), et une tâche PLUS PROFONDE devient atteignable
*parce que* cette jointure a été déposée.

Curriculum gradué :
  produit_premier_dernier (1) -> JOINTURE      : xs[0]*xs[-1]  (op mul du registre)  -> déposé
  produit_pd_plus_un       (2) -> COMPOSITION   : (xs[0]*xs[-1]) + 1 = incremente ∘ produit_premier_dernier
                                  *** HORS DE PORTÉE AU SEED *** — ni composition unaire, ni jointure,
                                  ni pli ne font « produit, puis +1 » d'un coup. Atteignable UNIQUEMENT
                                  si le palier 1 a déposé `produit_premier_dernier` comme brique.

Seeds : primitives premier, dernier, incremente ; ops mul, max2 (store vide : ces étages
n'utilisent que le registre appelable).

Expérience A/B (seul le levier `retroaction` diffère) :
  1. CONTRÔLE     — sans rétroaction, produit_pd_plus_un reste HORS DE PORTÉE.
  2. COMPOUNDING  — avec rétroaction, il est RÉSOLU (la jointure déposée le porte).
  3. GÉNÉRALISATION — chaque succès gardé passe le held-out.
  4. ESCALADE     — la jointure est résolue à `jointure`, le composé profond à `composition`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import franchies, montee
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held, ref_corps, diff):
    prompt = f'def {fn}(xs):\n    """..."""'
    ref = f"def {fn}(*args, **kwargs):\n{ref_corps}\n"
    return Tache(id=f"arite/{fn}", point_entree=fn, prompt=prompt, tests=tests,
                 tests_held_out=held, solution_ref=ref, difficulte=diff)


TACHES = [
    _t("produit_premier_dernier",
       "def check(c):\n    assert c([2,3,4]) == 8\n    assert c([5,1]) == 5\n    assert c([3]) == 9\ncheck(produit_premier_dernier)",
       "def check(c):\n    assert c([10,2,5]) == 50\n    assert c([4,4]) == 16\n    assert c([7]) == 49\ncheck(produit_premier_dernier)",
       "    return args[0][0] * args[0][-1]", 1),
    _t("produit_pd_plus_un",
       "def check(c):\n    assert c([2,3,4]) == 9\n    assert c([5,1]) == 6\n    assert c([3]) == 10\ncheck(produit_pd_plus_un)",
       "def check(c):\n    assert c([10,2,5]) == 51\n    assert c([4,4]) == 17\n    assert c([7]) == 50\ncheck(produit_pd_plus_un)",
       "    return args[0][0] * args[0][-1] + 1", 2),
]
CIBLE = "produit_pd_plus_un"

PRIMITIVES = [
    ("premier", "def premier(*args, **kwargs):\n    return args[0][0]\n"),
    ("dernier", "def dernier(*args, **kwargs):\n    return args[0][-1]\n"),
    ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n"),
]
OPS = [
    ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n"),
    ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] > args[1] else args[1]\n"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _montee(d, suffixe, retroaction):
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    orch = GenerateurOrchestre(store, primitives=list(PRIMITIVES), ops=list(OPS),
                               predicteur=Predicteur(store, types=TYPES_RICHES))
    curateur = CurateurGradue(TACHES, seuil=0.0, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=retroaction)


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        print("CONTRÔLE — sans rétroaction (la jointure n'est pas déposée) :")
        j_sans = _montee(d, "sans", retroaction=False)
        for p in j_sans:
            print(p.resume())
        f_sans = franchies(j_sans)

        print("\nTRAITEMENT — avec rétroaction (la jointure confirmée devient une brique) :")
        j_avec = _montee(d, "avec", retroaction=True)
        for p in j_avec:
            print(p.resume())
        f_avec = franchies(j_avec)
        # Étage de PREMIÈRE résolution (la suivante est de la réutilisation, étage trivial).
        etages: dict[str, str] = {}
        for p in j_avec:
            if p.confirme and p.point_entree not in etages:
                etages[p.point_entree] = p.etage

    print()
    resultats.append(_check(
        f"CONTRÔLE : sans rétroaction, `{CIBLE}` reste HORS DE PORTÉE",
        CIBLE not in f_sans))
    resultats.append(_check(
        f"COMPOUNDING : avec rétroaction, `{CIBLE}` est RÉSOLU (la jointure déposée le porte)",
        CIBLE in f_avec))
    resultats.append(_check(
        f"COUVERTURE ↑ : rétroaction résout plus ({len(f_avec)}) que le contrôle ({len(f_sans)})",
        len(f_avec) > len(f_sans)))
    resultats.append(_check(
        f"ESCALADE : produit_premier_dernier à `{etages.get('produit_premier_dernier')}`, "
        f"{CIBLE} à `{etages.get(CIBLE)}` (jointure déposée -> composition profonde)",
        etages.get("produit_premier_dernier") == "jointure" and etages.get(CIBLE) == "composition"))

    print()
    if all(resultats):
        print(f"COMPOUNDING DE L'ARITÉ 2 VALIDÉ — {len(resultats)}/{len(resultats)}. Une jointure confirmée "
              f"(arité 2) devient une brique qui rend atteignable une tâche plus profonde — le compounding "
              f"traverse le nouvel étage sans code dédié (le versement de primitives suffit). Cap 2 boucle "
              f"sur le compounding, jugé par le réel, sans modèle externe.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. C'est un RÉSULTAT : la jointure ne compounde pas (encore).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
