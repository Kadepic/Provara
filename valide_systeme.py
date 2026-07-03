"""
VALIDE SYSTÈME — tâches COMPOSITES DURES en montée (consigne Yohan : « rends les tests vraiment compliqués, ils
doivent prouver une vraie réflexion et demander un vrai investissement de TOUTES les briques »).

On abandonne les tâches mono-brique (trop faciles). Ici : des tâches qui exigent une CHAÎNE de plusieurs briques,
résolues UNIQUEMENT parce que le système invente -> route -> compose -> contrôle, en montée. Tests ADVERSES (beaucoup
de cas, bornes, valeurs piégeuses) pour qu'AUCUN imposteur ne passe.

On rapporte la VRAIE portée — un HORS-PORTÉE est un résultat honnête (le front réel), pas masqué en vert.

  COUCHE A — chaînes COMPOSITES (montée, retroaction) : chaque tâche tardive empile sur les skills versés.
  COUCHE B — A/B émergence : SANS compounding, les composites tombent (le tout > la somme), preuve par contrôle.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import franchies, montee
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


def _tests(asserts, fn):
    return "def check(c):\n" + "".join(f"    assert {a}\n" for a in asserts) + f"check({fn})"


def _t(fn, sig, vis, hel, ref, diff):
    return Tache(id=f"sysC/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=_tests(vis, fn), tests_held_out=_tests(hel, fn),
                 solution_ref=f"def {fn}(*args, **kwargs):\n    return {ref}\n", difficulte=diff)


# Curriculum gradué de tâches COMPOSITES, tests ADVERSES (beaucoup de cas + bornes + pièges).
# L1 = atomes inventables ; L2 = compose 1 cran ; L3 = chaîne PROFONDE (3 briques).
TACHES = [
    # --- L1 : atomes (invention / substrat / comparaison) ---
    _t("cube", "x",
       ["c(2) == 8", "c(3) == 27", "c(0) == 0", "c(1) == 1", "c(-2) == -8", "c(10) == 1000", "c(-1) == -1"],
       ["c(4) == 64", "c(5) == 125", "c(-3) == -27", "c(6) == 216"], "args[0] ** 3", 1),
    _t("est_negatif", "x",
       ["c(-3) is True", "c(2) is False", "c(0) is False", "c(-1) is True", "c(-100) is True", "c(5) is False"],
       ["c(-7) is True", "c(0) is False", "c(8) is False"], "args[0] < 0", 1),
    # --- L2 : compose 1 cran sur les atomes versés ---
    _t("cube_plus_un", "x",
       ["c(2) == 9", "c(3) == 28", "c(0) == 1", "c(1) == 2", "c(-2) == -7", "c(10) == 1001", "c(-1) == 0"],
       ["c(4) == 65", "c(5) == 126", "c(-3) == -26"], "args[0] ** 3 + 1", 2),
    _t("somme_cubes", "xs",
       ["c([1,2]) == 9", "c([2,3]) == 35", "c([0,1]) == 1", "c([3]) == 27", "c([-1,1]) == 0", "c([2,2,2]) == 24", "c([]) == 0"],
       ["c([1,2,3]) == 36", "c([3,1]) == 28", "c([-2]) == -8", "c([4]) == 64"], "sum(x ** 3 for x in args[0])", 2),
    _t("signe", "x",
       ["c(5) == 1", "c(-3) == -1", "c(0) == 0", "c(100) == 1", "c(-7) == -1", "c(1) == 1", "c(-1) == -1"],
       ["c(2) == 1", "c(-8) == -1", "c(0) == 0", "c(50) == 1"], "1 if args[0] > 0 else (-1 if args[0] < 0 else 0)", 2),
    # --- L3 : chaîne PROFONDE (invente cube -> verse somme_cubes -> compose incremente) ---
    _t("somme_cubes_plus_un", "xs",
       ["c([1,2]) == 10", "c([2,3]) == 36", "c([0,1]) == 2", "c([3]) == 28", "c([-1,1]) == 1", "c([]) == 1"],
       ["c([1,2,3]) == 37", "c([4]) == 65", "c([-2]) == -7"], "sum(x ** 3 for x in args[0]) + 1", 3),
]


def _montee(d, suffixe, retro):
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    # Seed minimal : carre (matière à muter pour cube), incremente (pour composer), est_positif (pour signe).
    orch = GenerateurOrchestre(
        store, primitives=[_d("carre", "args[0] * args[0]"), _d("incremente", "args[0] + 1")],
        predicats=[_d("est_positif", "args[0] > 0")],
        predicteur=Predicteur(store, types=TYPES_RICHES),
        inventer=True, map_repli=True)
    cur = CurateurGradue(TACHES, seuil=0.7, limites=LIM)
    assert not cur.rejetees, f"curriculum rejeté : {cur.rejetees}"
    journal = montee(orch, cur, store, limites=LIM, retroaction=retro, routage=True, k=300)
    return franchies(journal), journal


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    with tempfile.TemporaryDirectory() as d:
        print("=== COUCHE A : chaînes COMPOSITES en montée (tests ADVERSES) ===")
        f_avec, journal = _montee(d, "avec", True)
        for p in journal:
            print(p.resume())
        cibles = [t.point_entree for t in TACHES]
        manquants = [c for c in cibles if c not in f_avec]

        print("\n=== COUCHE B : contrôle (SANS compounding) ===")
        f_sans, _ = _montee(d, "sans", False)
        print(f"    AVEC compounding : {sorted(f_avec)}")
        print(f"    SANS compounding : {sorted(f_sans)}")

    # 1. Le système résout toute la chaîne composite (tests adverses).
    resultats.append(_check(
        f"COMPOSITION DURE : le système résout TOUTE la chaîne composite ({len(cibles)} tâches, tests adverses) — "
        f"manquants : {manquants}", not manquants))

    # 2. Émergence : les composites tombent sans compounding (le tout > la somme).
    composites = ["cube_plus_un", "somme_cubes", "somme_cubes_plus_un", "signe"]
    emergence = all(c in f_avec for c in composites) and all(c not in f_sans for c in composites)
    resultats.append(_check(
        f"ÉMERGENCE : les composites {composites} sont résolus AVEC compounding et TOUS hors-portée sans "
        f"(sans={sorted(f_sans)}) -> la portée émerge de la composition, pas des briques seules", emergence))

    print()
    if all(resultats):
        print(f"SYSTÈME VALIDÉ — {len(resultats)}/{len(resultats)}. Le système résout une CHAÎNE composite dure "
              f"(jusqu'à somme_cubes_plus_un = inventer cube -> map-reduce -> composer +1, 3 briques enchaînées), "
              f"sur des tests adverses, et UNIQUEMENT grâce au compounding (le tout > la somme).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT HONNÊTE : c'est le front réel du système (ce qu'il "
          f"NE sait PAS encore composer), pas masqué en vert.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
