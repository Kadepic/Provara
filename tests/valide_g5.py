"""
Validation de G5 — RECOMBINAISON (l'autonomie : construire une logique neuve).

Mise en scène : le store ne contient QUE deux succès, sur deux AUTRES tâches —
  A) tous_pairs        -> all(x % 2 == 0 for x in args[0])   (fragment : « x % 2 == 0 »)
  B) compte_positifs   -> sum(1 for x in args[0] if x > 0)   (squelette : « sum(1 ... if {C}) »)

La tâche cible C = compte_pairs n'est PAS dans le store. Sa solution est pourtant
un MÉLANGE : le squelette de B + la condition de A. On exige :

  1. G1 (réutilisation) NE résout PAS C — elle n'est pas au store, rien à réutiliser ;
  2. G5 (recombinaison) RÉSOUT C — en combinant des fragments minés sur A et B ;
  3. HONNÊTETÉ : sans A au store (donc sans « x % 2 == 0 »), G5 ne peut PLUS résoudre
     C — il recombine du connu, il n'invente pas.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from exercices import COMPTE_PAIRS as C
from generateur import GenerateurRecombinant, GenerateurReutilisateur
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

A = Tache(id="seed/tous_pairs", point_entree="tous_pairs",
          prompt='def tous_pairs(xs):\n    """True si tous les éléments sont pairs."""',
          tests="def check(c):\n    assert c([2, 4, 6]) is True\n    assert c([1, 2]) is False\n"
                "    assert c([]) is True\ncheck(tous_pairs)")
A_SOL = "def tous_pairs(*args, **kwargs):\n    return all(x % 2 == 0 for x in args[0])\n"

B = Tache(id="seed/compte_positifs", point_entree="compte_positifs",
          prompt='def compte_positifs(xs):\n    """Compte les éléments strictement positifs."""',
          tests="def check(c):\n    assert c([1, -2, 3]) == 2\n    assert c([]) == 0\n"
                "    assert c([-1, -2]) == 0\ncheck(compte_positifs)")
B_SOL = "def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n"


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _seme(store, tache, sol):
    v = juge(sol, tache.tests, LIM)
    assert v.passe, f"pré-condition : {tache.id} doit passer"
    store.ajoute(tache, sol, v)


def resout(generateur, tache, n=60):
    """Renvoie le 1er candidat qui passe visible ET held-out, sinon None."""
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and \
           (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seme(store, A, A_SOL)
        _seme(store, B, B_SOL)
        print(f"Store : 2 succès sur d'AUTRES tâches ({A.id}, {B.id}). Cible = {C.id} (absente).\n")

        # 1. G1 ne peut pas : compte_pairs n'est pas au store.
        g1 = GenerateurReutilisateur(store)
        resultats.append(_check("G1 (réutilisation) ne résout PAS compte_pairs (absente du store)",
                                resout(g1, C) is None))

        # 2. G5 recombine A + B -> résout compte_pairs.
        g5 = GenerateurRecombinant(store)
        gagnant = resout(g5, C)
        if gagnant:
            print(f"    G5 a recombiné -> {gagnant.strip().splitlines()[-1].strip()}\n")
        resultats.append(_check("G5 (recombinaison) RÉSOUT compte_pairs en mélangeant A et B",
                                gagnant is not None))

    # 3. Honnêteté : sans A (donc sans « x % 2 == 0 »), G5 ne peut plus.
    with tempfile.TemporaryDirectory() as d:
        store_sansA = Store(Path(d) / "s2.jsonl")
        _seme(store_sansA, B, B_SOL)   # seulement B
        g5b = GenerateurRecombinant(store_sansA)
        resultats.append(_check("sans le fragment d'A, G5 ne résout PLUS compte_pairs (il recombine, n'invente pas)",
                                resout(g5b, C) is None))

    print()
    if all(resultats):
        print(f"G5 VALIDÉ — {len(resultats)}/{len(resultats)}. La logique d'une tâche NEUVE émerge en "
              f"recombinant des fragments d'anciens succès. Premier pas vers « il construit sa logique seul ».")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
