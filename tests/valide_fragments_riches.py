"""
Validation des FRAGMENTS RICHES — élargir le vocabulaire, pas le moteur.

Point 1 du plan de reprise. Jusqu'ici l'extracteur ne minait que les CONDITIONS
(comparaisons / et-ou). La recombinaison (G5) et la compréhension ne voyaient donc
qu'une partie du monde. On enrichit le vocabulaire : `TYPES_RICHES` mine AUSSI les
opérations binaires (`x * x`) et les agrégations (`sum(...)`, `max(...)`).

Le point CLÉ — et ce qui le rend honnête : on ne touche PAS au moteur. C'est le MÊME
`GenerateurRecombinant`. Seul change le tuple `types` passé. La puissance vient du
vocabulaire, pas d'une astuce codée pour la tâche.

Mise en scène (calquée sur valide_g5) : le store contient DEUX succès sur D'AUTRES tâches —
  A) somme_carres -> sum(x * x for x in args[0])   (sens BinOp : « x * x »)
  B) max_plus_un  -> max(x + 1 for x in args[0])   (squelette : « max({C} for x in args[0]) »)

La cible C = max_carres -> max(x * x for x in args[0]) n'est PAS au store. Sa solution
est un MÉLANGE : le squelette d'agrégation de B + le sens binaire de A. On exige :

  1. COUVERTURE : le vocabulaire riche mine STRICTEMENT plus de fragments que les
     conditions seules (ici : 0 -> 4). C'est la racine — le critère falsifiable.
  2. CONDITIONS SEULES IMPUISSANTES : le MÊME G5, vocabulaire « conditions », ne résout
     PAS max_carres (il ne mine ni `x * x` ni `x + 1` : aucun fragment, aucun candidat).
  3. VOCABULAIRE RICHE RÉSOUT : le MÊME G5, vocabulaire `TYPES_RICHES`, RÉSOUT max_carres
     en croisant le squelette de B et le sens binaire de A.
  4. HONNÊTETÉ : sans A (donc sans « x * x » nulle part), même le riche ne peut plus —
     il recombine ce qu'il a miné, il n'invente pas.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import GenerateurRecombinant, TYPES_CONDITIONS, TYPES_RICHES, fragments_riches
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(id, fn, tests, held_out=""):
    return Tache(id=id, point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held_out)


# A : agrégation sum + sens binaire « x * x ».
A = _t("seed/somme_carres", "somme_carres",
       "def check(c):\n    assert c([1,2,3]) == 14\n    assert c([]) == 0\n    assert c([-2]) == 4\ncheck(somme_carres)")
A_SOL = "def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n"

# B : agrégation max + sens binaire « x + 1 ».
B = _t("seed/max_plus_un", "max_plus_un",
       "def check(c):\n    assert c([1,2,3]) == 4\n    assert c([0]) == 1\n    assert c([-5,2]) == 3\ncheck(max_plus_un)")
B_SOL = "def max_plus_un(*args, **kwargs):\n    return max(x + 1 for x in args[0])\n"

# Cible : croisement « squelette de B + sens de A » — jamais au store.
C = _t("cible/max_carres", "max_carres",
       "def check(c):\n    assert c([1,2,3]) == 9\n    assert c([-3,2]) == 9\n    assert c([4]) == 16\ncheck(max_carres)",
       held_out="def check(c):\n    assert c([-1,-5]) == 25\n    assert c([10]) == 100\n    assert c([0,3]) == 9\ncheck(max_carres)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _seme(store, tache, sol):
    v = juge(sol, tache.tests, LIM)
    assert v.passe, f"pré-condition : {tache.id} doit passer"
    store.ajoute(tache, sol, v)


def resout(generateur, tache, n=80):
    """1er candidat qui passe visible ET held-out, sinon None (cf. valide_g5)."""
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and \
           (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def _sens_minables(store, types):
    """Nombre de fragments-sens distincts que ce vocabulaire sait extraire du store."""
    sens = set()
    for s in store:
        _, frags = fragments_riches(s.solution, types)
        sens.update(frags)
    return sens


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seme(store, A, A_SOL)
        _seme(store, B, B_SOL)
        print(f"Store : 2 succès sur d'AUTRES tâches ({A.id}, {B.id}). Cible = {C.id} (absente).\n")

        # 1. Couverture : le vocabulaire riche mine strictement plus.
        pauvre = _sens_minables(store, TYPES_CONDITIONS)
        riche = _sens_minables(store, TYPES_RICHES)
        print(f"    fragments minables — conditions : {len(pauvre)} {sorted(pauvre)}")
        print(f"    fragments minables — riches     : {len(riche)} {sorted(riche)}\n")
        resultats.append(_check(f"couverture en hausse grâce aux types riches ({len(pauvre)} -> {len(riche)})",
                                len(riche) > len(pauvre)))

        # 2. MÊME moteur, vocabulaire « conditions » : impuissant sur max_carres.
        g5_pauvre = GenerateurRecombinant(store, types=TYPES_CONDITIONS)
        resultats.append(_check("conditions seules NE résolvent PAS max_carres (aucun fragment binaire miné)",
                                resout(g5_pauvre, C) is None))

        # 3. MÊME moteur, vocabulaire riche : résout max_carres en recombinant A et B.
        g5_riche = GenerateurRecombinant(store, types=TYPES_RICHES)
        gagnant = resout(g5_riche, C)
        if gagnant:
            print(f"    G5-riche a recombiné -> {gagnant.strip().splitlines()[-1].strip()}\n")
        resultats.append(_check("vocabulaire riche RÉSOUT max_carres (squelette de B + sens binaire de A)",
                                gagnant is not None))

    # 4. Honnêteté : sans A (donc sans « x * x »), même le riche ne peut plus.
    with tempfile.TemporaryDirectory() as d:
        store_sansA = Store(Path(d) / "s2.jsonl")
        _seme(store_sansA, B, B_SOL)   # seulement B
        g5b = GenerateurRecombinant(store_sansA, types=TYPES_RICHES)
        resultats.append(_check("sans A (donc sans « x * x »), le riche ne résout PLUS (il recombine, n'invente pas)",
                                resout(g5b, C) is None))

    print()
    if all(resultats):
        print(f"FRAGMENTS RICHES VALIDÉS — {len(resultats)}/{len(resultats)}. Élargir le VOCABULAIRE "
              f"(pas le moteur) débloque des recombinaisons hors de portée de la logique seule : "
              f"`max(x * x ...)` émerge en croisant une agrégation et une opération binaire apprises ailleurs.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
