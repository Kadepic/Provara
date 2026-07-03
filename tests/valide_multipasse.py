"""
MULTI-PASSE — filtrer par un AGRÉGAT du TOUT (thème II du prochain front : au_dessus_moyenne).

L'escalade (`mesure_plafond2`) a confirmé HORS-PORTÉE `au_dessus_moyenne` = compter les éléments > moyenne. La
fusion filtre par un prédicat SIMPLE (x > 0) ; elle ne peut pas filtrer par une mesure de la liste ENTIÈRE. C'est
DEUX passes : agréger (moyenne/max/min) puis filtrer chaque élément par rapport à l'agrégat. `GenerateurMultiPasse`
admet `REDUC(x for x in xs if x CMP AGG(xs))`. au_dessus_moyenne = sum(1 for x in xs if x > sum(xs)/len(xs)).

Tests durcis au HELD-OUT (cas qui tuent les coïncidences : moyenne entière, tous égaux…).

Critères de MORT :
  1. MUR (fusion)       : la fusion (filtre simple) ne minte pas au_dessus_moyenne.
  2. MULTI-PASSE (×2)   : `au_dessus_moyenne` (compter) ET `somme_au_dessus_moyenne` (sommer) mintés + GÉNÉRALISENT.
  3. HONNÊTE           : sans l'agrégat moyenne (que max/min), au_dessus_moyenne n'est PAS atteint.
  4. VIVANT (modèle)    : l'orchestrateur (multipasse=True) résout au_dessus_moyenne à l'étage `multipasse`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMultiPasse, GenerateurOrchestre, GenerateurRecombinant
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"mp2/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


AU_DESSUS = _t("au_dessus_moyenne",
    "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([10,0,0]) == 1\n    assert c([5,5,5,5]) == 0\ncheck(au_dessus_moyenne)",
    "def check(c):\n    assert c([1,2,3,10]) == 1\n    assert c([0,0,0,4]) == 1\n    assert c([2,4,6]) == 1\ncheck(au_dessus_moyenne)")
SOMME_AU_DESSUS = _t("somme_au_dessus_moyenne",
    "def check(c):\n    assert c([1,2,3,4]) == 7\n    assert c([10,0,0]) == 10\n    assert c([5,5]) == 0\ncheck(somme_au_dessus_moyenne)",
    "def check(c):\n    assert c([1,2,3,10]) == 10\n    assert c([2,4,6]) == 6\ncheck(somme_au_dessus_moyenne)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_gen(gen, tache, n=400):
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and juge(code, tache.tests_held_out, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []
    mp = GenerateurMultiPasse()

    # 1. MUR : la recombinaison (filtre simple miné du store) ne minte pas au_dessus_moyenne.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for fn, expr, tst in [("compte_positifs", "sum(1 for x in args[0] if x > 0)", "def check(c):\n    assert c([1,-1,2]) == 2\ncheck(compte_positifs)"),
                              ("somme_carres", "sum(x * x for x in args[0])", "def check(c):\n    assert c([1,2]) == 5\ncheck(somme_carres)")]:
            src = f"def {fn}(*args, **kwargs):\n    return {expr}\n"
            store.ajoute(Tache(id=fn, point_entree=fn, prompt="", tests=tst), src, juge(src, tst, LIM))
        mur = _resout_gen(GenerateurRecombinant(store, types=TYPES_RICHES), AU_DESSUS) is None
    resultats.append(_check("MUR : la recombinaison (filtre simple) ne minte pas au_dessus_moyenne", mur))

    # 2. MULTI-PASSE ×2.
    g1 = _resout_gen(mp, AU_DESSUS)
    g2 = _resout_gen(mp, SOMME_AU_DESSUS)
    if g1:
        print(f"    au_dessus_moyenne       -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    somme_au_dessus_moyenne -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("MULTI-PASSE : `au_dessus_moyenne` (compter) ET `somme_au_dessus_moyenne` (sommer) "
                            "mintés + généralisent", g1 is not None and g2 is not None))

    # 3. HONNÊTE : sans l'agrégat moyenne, hors-portée.
    resultats.append(_check("HONNÊTE : sans l'agrégat moyenne (que max/min), au_dessus_moyenne n'est PAS atteint",
                            _resout_gen(GenerateurMultiPasse(aggs=("max(args[0])", "min(args[0])")), AU_DESSUS) is None))

    # 4. VIVANT : l'orchestrateur (multipasse=True) résout au_dessus_moyenne à l'étage multipasse.
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), multipasse=True)
        etage, _, code, _ = resoudre(orch, AU_DESSUS, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (multipasse=True) résout au_dessus_moyenne à l'étage `{etage}`",
        code is not None and etage == "multipasse"))

    print()
    if all(resultats):
        print(f"MULTI-PASSE VALIDÉ — {len(resultats)}/{len(resultats)}. Filtrer par un agrégat du TOUT (2 passes) : "
              f"au_dessus_moyenne ET somme_au_dessus_moyenne, held-out durci, honnête, utilisé par le modèle "
              f"(étage multipasse). Thème II (multi-passe / état riche) amorcé ; restent run-length + générer-et-tester.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
