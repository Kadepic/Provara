"""
COMPRÉHENSION GÉNÉRALE — transform + filtre(agrégat) + reduce en UNE passe (le front « réel » restant).

Le composite type : « somme des CUBES AU-DESSUS de la moyenne » = sum(cube(x) for x in xs if x > sum(xs)/len(xs)).
Aucune brique ne le couvrait d'un seul tenant : `map-repli` transforme+replie mais SANS filtre ; `multipasse`
filtre+replie mais SANS transform. `GenerateurComprehensionGenerale` admet le schéma unifié
`REDUC(f(x) for x in args[0] [if x CMP AGG(args[0])])` (f ∈ {id} ∪ prims, REDUC ∈ {sum,max,min,list,count},
filtre optionnel par un agrégat du TOUT). Il SUBSUME map-repli (sans filtre) ET multipasse (f=identité) → futur
candidat à la déduplication (passe d'excellence).

Tests DURS au HELD-OUT (cas qui tuent les coïncidences : négatifs où le SIGNE du cube compte, tous-égaux -> 0/[],
singleton, moyenne flottante non entière, zéros). Deux tâches qui varient REDUC, f, CMP et AGG -> schéma général.

Critères de MORT :
  1. MUR (×2)          : map-repli (sans filtre) ET multipasse (sans transform) échouent TOUS DEUX sur le composite.
  2. GÉNÉRALE (×2)     : `somme_cubes_au_dessus_moyenne` (sum∘cube, filtre>moyenne) ET `liste_carres_au_dessus_min`
                         (list∘carre, filtre>min) mintés + GÉNÉRALISENT (held-out adverse).
  3. HONNÊTE           : sans la primitive `cube`, le composite n'est PAS atteint (ne conjure pas l'atome).
  4. VIVANT (modèle)   : l'orchestrateur (comprehension_generale=True) le résout à l'étage `comprehension-generale`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurMapRepli,
                        GenerateurMultiPasse, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")
CUBE = ("cube", "def cube(*args, **kwargs):\n    return args[0] ** 3\n")
DOUBLE = ("double", "def double(*args, **kwargs):\n    return args[0] + args[0]\n")
INCR = ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")

PRIMS = [CARRE, CUBE, DOUBLE, INCR]


def _t(fn, tests, held):
    return Tache(id=f"cg/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


# 1) sum(cube(x) for x in xs if x > moyenne) — REDUC=sum, f=cube, CMP=>, AGG=moyenne (flottante).
SOMME_CUBES_SUP_MOY = _t("somme_cubes_au_dessus_moyenne",
    "def check(c):\n"
    "    assert c([1, 2, 3, 4]) == 91\n"      # moyenne 2.5 -> 3,4 -> 27+64
    "    assert c([2, 2, 2]) == 0\n"          # tous égaux -> aucun > moyenne
    "    assert c([1, 5]) == 125\n"           # moyenne 3 -> 5 -> 125
    "check(somme_cubes_au_dessus_moyenne)",
    "def check(c):\n"
    "    assert c([-3, -1, -2]) == -1\n"      # moyenne -2 -> -1 -> (-1)**3 (SIGNE du cube)
    "    assert c([-2, -2, 4]) == 64\n"       # moyenne 0 -> 4 -> 64
    "    assert c([5]) == 0\n"                # singleton -> x > x faux
    "    assert c([0, 0, 0, 8]) == 512\n"     # moyenne 2 -> 8 -> 512
    "    assert c([3, 3, 1]) == 54\n"         # moyenne 7/3 -> 3,3 -> 27+27
    "check(somme_cubes_au_dessus_moyenne)")

# 2) [carre(x) for x in xs if x > min(xs)] — REDUC=list, f=carre, CMP=>, AGG=min (axes tous différents de 1).
LISTE_CARRES_SUP_MIN = _t("liste_carres_au_dessus_min",
    "def check(c):\n"
    "    assert c([1, 2, 3]) == [4, 9]\n"
    "    assert c([5, 5, 2]) == [25, 25]\n"
    "    assert c([3, 1, 4, 1]) == [9, 16]\n"  # ordre préservé, min répété ignoré
    "check(liste_carres_au_dessus_min)",
    "def check(c):\n"
    "    assert c([2, 2, 2]) == []\n"          # tous = min -> rien
    "    assert c([-2, -1, -3]) == [4, 1]\n"   # négatifs, min=-3 -> -2,-1
    "    assert c([10]) == []\n"               # singleton
    "    assert c([0, 5, 0]) == [25]\n"
    "check(liste_carres_au_dessus_min)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_gen(gen, tache, n=600):
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and juge(code, tache.tests_held_out, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []
    cg = GenerateurComprehensionGenerale(PRIMS)

    # 1. MUR ×2 : map-repli (transforme+replie SANS filtre) ET multipasse (filtre+replie SANS transform)
    #    échouent tous deux sur le composite « cube + filtre moyenne + somme » -> il faut les TROIS ensemble.
    mur_maprepli = _resout_gen(GenerateurMapRepli(PRIMS), SOMME_CUBES_SUP_MOY) is None
    mur_multipasse = _resout_gen(GenerateurMultiPasse(), SOMME_CUBES_SUP_MOY) is None
    resultats.append(_check("MUR : map-repli (sans filtre) ET multipasse (sans transform) échouent tous deux "
                            "sur sum(cube(x) for x in xs if x > moyenne)", mur_maprepli and mur_multipasse))

    # 2. GÉNÉRALE ×2 : deux composites qui varient REDUC/f/CMP/AGG -> schéma général, pas hardcodé.
    g1 = _resout_gen(cg, SOMME_CUBES_SUP_MOY)
    g2 = _resout_gen(cg, LISTE_CARRES_SUP_MIN)
    if g1:
        print(f"    somme_cubes_au_dessus_moyenne -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    liste_carres_au_dessus_min    -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("GÉNÉRALE : `somme_cubes_au_dessus_moyenne` (sum∘cube, >moyenne) ET "
                            "`liste_carres_au_dessus_min` (list∘carre, >min) mintés + généralisent (held-out adverse)",
                            g1 is not None and g2 is not None))

    # 3. HONNÊTE : sans la primitive cube (que carre/double/incr), le composite des cubes est hors-portée.
    resultats.append(_check("HONNÊTE : sans la primitive `cube`, somme_cubes_au_dessus_moyenne n'est PAS atteint "
                            "(ne conjure pas l'atome)",
                            _resout_gen(GenerateurComprehensionGenerale([CARRE, DOUBLE, INCR]), SOMME_CUBES_SUP_MOY) is None))

    # 4. VIVANT : l'orchestrateur (comprehension_generale=True) le résout à l'étage comprehension-generale.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, primitives=PRIMS,
                                   predicteur=Predicteur(store, types=TYPES_RICHES),
                                   comprehension_generale=True)
        etage, _, code, _ = resoudre(orch, SOMME_CUBES_SUP_MOY, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (comprehension_generale=True) résout le composite à l'étage `{etage}`",
        code is not None and etage == "comprehension-generale"))

    print()
    if all(resultats):
        print(f"COMPRÉHENSION GÉNÉRALE VALIDÉE — {len(resultats)}/{len(resultats)}. transform + filtre(agrégat du TOUT) "
              f"+ reduce en UNE passe : sum(cube(x) for x in xs if x > moyenne) et [carre(x) ... if x > min], "
              f"ce que ni map-repli (sans filtre) ni multipasse (sans transform) ne pouvaient seuls — held-out adverse, "
              f"honnête, utilisé par le modèle (étage comprehension-generale). Subsume map-repli + multipasse "
              f"-> déduplication à évaluer (excellence).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
