"""
Validation de la BRIQUE 8 (le curateur).

Quatre exigences :
  1. AUTO-VALIDATION : chacun des exercices curés passe ses tests + survit au fuzz
     -> le curateur (moi) est tenu honnête par le juge, comme le modèle.
  2. REJET d'une tâche dont la RÉFÉRENCE échoue ses propres tests (curateur fautif).
  3. REJET d'une tâche dont la référence CRASHE au fuzz (référence fragile).
  4. GRADUATION : on sert le facile d'abord, on monte de palier quand la
     généralisation dépasse le seuil, le lot est cumulatif, on s'arrête en haut.
"""

from __future__ import annotations

from curateur import CurateurGradue, valide_tache
from exercices import CATALOGUE
from juge import Limites
from taches import Tache

LIM = Limites(temps_s=4, cpu_s=3)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


# --- Tâches volontairement bancales (pour prouver le rejet) ------------------

# Référence FAUSSE : prétend doubler, renvoie x+1 -> échoue ses propres tests.
TACHE_FAUSSE = Tache(
    id="casse/reference_fausse", difficulte=1, point_entree="double",
    prompt="def double(x: int) -> int:\n    \"\"\"Double x.\"\"\"",
    tests="def check(c):\n    assert c(2) == 4\n    assert c(5) == 10\ncheck(double)",
    solution_ref="def double(x: int) -> int:\n    return x + 1",
)

# Référence FRAGILE : passe les tests (listes non vides) mais crashe sur [] au fuzz.
TACHE_FRAGILE = Tache(
    id="casse/reference_fragile", difficulte=1, point_entree="premier",
    prompt="from typing import List\ndef premier(xs: List[int]) -> int:\n    \"\"\"Premier élément.\"\"\"",
    tests="def check(c):\n    assert c([5, 6]) == 5\ncheck(premier)",
    solution_ref="from typing import List\ndef premier(xs: List[int]) -> int:\n    return xs[0]",
    tests_held_out="def check(c):\n    assert c([9]) == 9\ncheck(premier)",
    gen_entrees="def _gen(rng):\n    return ([rng.randint(0, 9) for _ in range(rng.randint(0, 3))],)",
)


def main() -> int:
    resultats = []

    # 1. Tous les exercices curés s'auto-valident.
    print("1. Auto-validation des exercices curés :")
    for t in CATALOGUE:
        r = valide_tache(t, limites=LIM)
        resultats.append(_check(f"{t.id} (diff {t.difficulte}) valide", r.valide))
        if not r.valide:
            print(f"        raisons : {r.raisons}")

    # 2 & 3. Les tâches bancales sont rejetées, avec la bonne raison.
    print("\n2-3. Rejet des tâches bancales :")
    rf = valide_tache(TACHE_FAUSSE, limites=LIM)
    resultats.append(_check("référence fausse -> rejetée", not rf.valide))
    resultats.append(_check("  raison = échoue ses tests visibles",
                            any("tests visibles" in r for r in rf.raisons)))
    rg = valide_tache(TACHE_FRAGILE, limites=LIM)
    resultats.append(_check("référence fragile -> rejetée", not rg.valide))
    resultats.append(_check("  raison = ne survit pas à son générateur",
                            any("générateur" in r for r in rg.raisons)))

    # 4. Graduation du curriculum.
    print("\n4. Graduation (le facile d'abord, on monte avec la généralisation) :")
    cur = CurateurGradue(CATALOGUE + [TACHE_FAUSSE, TACHE_FRAGILE], seuil=0.7, limites=LIM)
    resultats.append(_check("4 valides retenues, 2 rejetées",
                            len(cur.valides) == 4 and len(cur.rejetees) == 2))
    resultats.append(_check("démarre au niveau 1, lot = 1 tâche", cur.niveau == 1 and len(cur.lot()) == 1))
    resultats.append(_check("généralisation faible -> ne monte pas", cur.progresse(0.5) is False))
    monte = cur.progresse(0.8)
    resultats.append(_check("généralisation forte -> monte au niveau 2", monte and cur.niveau == 2))
    resultats.append(_check("lot cumulatif (niveau 2 -> 2 tâches)", len(cur.lot()) == 2))
    cur.progresse(0.9); cur.progresse(0.9)
    resultats.append(_check("atteint le dernier palier (4 tâches)", cur.niveau == 4 and len(cur.lot()) == 4))
    resultats.append(_check("au sommet -> ne monte plus, fini()", (cur.progresse(0.9) is False) and cur.fini()))

    print()
    if all(resultats):
        print(f"BRIQUE 8 VALIDÉE — {len(resultats)}/{len(resultats)}. "
              f"Matière externe, auto-validée, graduée. Le juge garde modèle ET curateur honnêtes.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
