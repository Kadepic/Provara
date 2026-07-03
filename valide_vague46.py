"""
VAGUE 46 — RECHERCHE AVANCÉE / FENÊTRE / THÉORIE DES NOMBRES (2026-06-22 nuit, autonomie).
gap_probe_vague46 = 8 tâches : 1 VRAI TROU bâti + 7 confirmées (re-testées À FROID, held-out durci).

Bâti cette vague :
  • `search_rotated` -> `index-ordonne` (dichotomie en tableau trié PIVOTÉ ; vérifié EXHAUSTIVEMENT sur toutes
    les rotations × cibles présentes/absentes avant câblage).
Confirmées À FROID : count_primes (`diviseurs`), fast_pow (`repetition`), happy_number (`diviseurs`),
integer_sqrt (`math-avance`), max_sliding_window (`fenetre`), single_number_iii (`tableaux`, HELD DURCI car
1505 cand. = suspect), reverse_integer (`chiffres`).

Critères de MORT (4) :
  1. THÉORIE DES NOMBRES : count_primes + fast_pow + happy_number + integer_sqrt résolus & généralisent.
  2. RECHERCHE BINAIRE : search_rotated via `index-ordonne`.
  3. FENÊTRE/FRÉQUENCE : max_sliding_window via `fenetre` ; single_number_iii (held durci) ; reverse_integer.
  4. HORS HONNÊTE : incohérent -> HORS.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from valide_commun import resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        # ---- 1. THÉORIE DES NOMBRES --------------------------------------------------------------------------
        cp = ia.demande("count_primes", "n", [((10,), 4), ((20,), 8)],
                        [((2,), 0), ((0,), 0), ((3,), 1), ((100,), 25), ((30,), 10)])
        fp = ia.demande("fast_pow", "base, exp", [((2, 10), 1024), ((5, 3), 125)],
                        [((3, 0), 1), ((2, 0), 1), ((7, 2), 49), ((10, 5), 100000), ((2, 16), 65536)])
        hn = ia.demande("happy_number", "n", [((19,), True), ((2,), False)],
                        [((1,), True), ((7,), True), ((4,), False), ((23,), True)])
        isq = ia.demande("integer_sqrt", "n", [((8,), 2), ((16,), 4)],
                         [((1,), 1), ((0,), 0), ((99,), 9), ((2,), 1), ((144,), 12)])
        r.append(_check(f"NOMBRES count_primes->`{cp.etage}` fast_pow->`{fp.etage}` happy->`{hn.etage}` isqrt->`{isq.etage}`",
                        all(x.ok and x.generalise for x in (cp, fp, hn, isq))))

        # ---- 2. RECHERCHE BINAIRE (tableau pivoté) ----------------------------------------------------------
        sr = ia.demande("search_rotated", "nums, target",
                        [(([4, 5, 6, 7, 0, 1, 2], 0), 4), (([4, 5, 6, 7, 0, 1, 2], 3), -1)],
                        [(([1], 1), 0), (([5, 1, 3], 5), 0), (([6, 7, 8, 1, 2, 3], 8), 2),
                         (([3, 4, 5, 1, 2], 1), 3), (([7, 8, 1, 2, 3, 4, 5, 6], 6), 7)])
        r.append(_check(f"RECHERCHE BINAIRE search_rotated->`{sr.etage}` (==index-ordonne)",
                        resolu(sr)))

        # ---- 3. FENÊTRE / FRÉQUENCE (single_number_iii HELD DURCI) ------------------------------------------
        msw = ia.demande("max_sliding_window", "nums, k",
                         [(([1, 3, -1, -3, 5, 3, 6, 7], 3), [3, 3, 5, 5, 6, 7]), (([1, 2, 3, 4], 2), [2, 3, 4])],
                         [(([1], 1), [1]), (([9, 8, 7], 2), [9, 8]), (([4, 2, 12, 11, -5], 2), [4, 12, 12, 11])])
        sn = ia.demande("single_number_iii", "nums",
                        [(([1, 2, 1, 3, 2, 5],), [3, 5]), (([1, 1, 2, 3],), [2, 3])],
                        [(([0, 7],), [0, 7]), (([4, 1, 2, 1, 2, 5],), [4, 5]), (([10, 10, 3, 7],), [3, 7]),
                         (([-1, -1, 8, 9],), [8, 9]), (([6, 6, 6, 2],), [2]), (([1, 1, 2, 2, 3, 4],), [3, 4])])
        ri = ia.demande("reverse_integer", "n", [((123,), 321), ((-123,), -321)],
                        [((120,), 21), ((0,), 0), ((5,), 5), ((-90,), -9), ((1000,), 1)])
        r.append(_check(f"FENÊTRE/FRÉQ max_sliding->`{msw.etage}`(==fenetre) single_iii->`{sn.etage}` reverse_int->`{ri.etage}`",
                        resolu(msw) and resolu(sn) and resolu(ri)))

        # ---- 4. HORS HONNÊTE -------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v46", "n", [((1,), 42)], [((2,), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 46 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
