"""
GROUP-BY — grouper des paires par clé et agréger (thème I : max_par_cle).

L'escalade a confirmé HORS-PORTÉE `max_par_cle`. `GenerateurGroupBy` admet
`{k: AGG(p[1] for p in args[0] if p[0] == k) for k in set(p[0] for p in args[0])}`.

Tests durcis au HELD-OUT.

Critères de MORT :
  1. MUR (dict-accu) : le dict-accumulateur (clé->mesure simple) ne minte pas max_par_cle (groupe de valeurs).
  2. GROUP-BY (×2)   : `max_par_cle` (max) ET `somme_par_cle` (sum) mintés + GÉNÉRALISENT.
  3. VIVANT (modèle) : l'orchestrateur (group_by=True) résout max_par_cle à l'étage `group-by`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurDictAccumulateur, GenerateurGroupBy, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"gb/{fn}", point_entree=fn, prompt=f'def {fn}(paires):\n    """..."""',
                 tests=tests, tests_held_out=held)


MAX_PAR_CLE = _t("max_par_cle",
    "def check(c):\n    assert c([('a',1),('b',5),('a',3)]) == {'a':3,'b':5}\n    assert c([('x',2)]) == {'x':2}\ncheck(max_par_cle)",
    "def check(c):\n    assert c([('a',1),('a',2),('b',9)]) == {'a':2,'b':9}\n    assert c([('p',7),('q',7)]) == {'p':7,'q':7}\ncheck(max_par_cle)")
SOMME_PAR_CLE = _t("somme_par_cle",
    "def check(c):\n    assert c([('a',1),('b',5),('a',3)]) == {'a':4,'b':5}\n    assert c([('x',2)]) == {'x':2}\ncheck(somme_par_cle)",
    "def check(c):\n    assert c([('a',1),('a',2),('a',3)]) == {'a':6}\n    assert c([('m',4),('n',1)]) == {'m':4,'n':1}\ncheck(somme_par_cle)")


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
    gb = GenerateurGroupBy()

    resultats.append(_check("MUR : le dict-accumulateur (clé->mesure simple) ne minte pas max_par_cle",
                            _resout_gen(GenerateurDictAccumulateur(), MAX_PAR_CLE) is None))

    g1 = _resout_gen(gb, MAX_PAR_CLE)
    g2 = _resout_gen(gb, SOMME_PAR_CLE)
    if g1:
        print(f"    max_par_cle   -> {g1.strip().splitlines()[-1].strip()}")
    if g2:
        print(f"    somme_par_cle -> {g2.strip().splitlines()[-1].strip()}")
    resultats.append(_check("GROUP-BY : `max_par_cle` (max) ET `somme_par_cle` (sum) mintés + généralisent",
                            g1 is not None and g2 is not None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), group_by=True)
        etage, _, code, _ = resoudre(orch, MAX_PAR_CLE, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (group_by=True) résout max_par_cle à l'étage `{etage}`",
        code is not None and etage == "group-by"))

    print()
    if all(resultats):
        print(f"GROUP-BY VALIDÉ — {len(resultats)}/{len(resultats)}. Grouper par clé + agréger : max_par_cle ET "
              f"somme_par_cle, held-out, honnête, utilisé par le modèle. **Thème I (structures de données) COMPLET** "
              f"(imbriqué + dict-accu + group-by). Les deux thèmes du prochain front sont entamés/couverts.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
