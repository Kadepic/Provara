"""
VAGUE 39 — ensembles / nombres (2026-06-20, nuit, 1.5 Go). gap_probe_vague39 = 8 tâches : 2 vrais trous bâtis
(distribute_candies via `statistiques` = min(distinct, n//2) ; intersect_multiset via `ensembles` = intersection
MULTISET avec multiplicité) + 6 déjà couvertes réelles (majority_element->means-end, nth_ugly_number->tableaux,
peak_index_in_mountain_array->adjacence, valid_perfect_square & ugly_number->diviseurs, sqrt_int->math-avance).
Held-out ADVERSE frais, pré-vérifiés par référence.

Critères de MORT (4) :
  1. BÂTIS : distribute_candies via `statistiques` ; intersect_multiset via `ensembles`.
  2. NOMBRES : valid_perfect_square + ugly_number via `diviseurs` ; sqrt_int via `math-avance`.
  3. GÉNÉRIQUES RÉELS : majority_element via `means-end` ; nth_ugly_number via `tableaux` ; peak_index via `adjacence`.
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

        # ---- 1. BÂTIS ------------------------------------------------------------------------------------------
        dc = ia.demande("distribute_candies", "candyType",
                        [(([1, 1, 2, 2, 3, 3],), 3), (([1, 1, 2, 3],), 2)],
                        [(([1, 1, 1, 1, 1, 1],), 1), (([1, 2],), 1), (([1, 2, 3, 4],), 2),
                         (([7, 7, 8, 8, 9, 9, 10, 10],), 4), (([],), 0)])
        im = ia.demande("intersect_multiset", "nums1, nums2",
                        [(([1, 2, 2, 1], [2, 2]), [2, 2]), (([4, 9, 5], [9, 4, 9, 8, 4]), [4, 9])],
                        [(([1, 1, 1], [1, 1]), [1, 1]), (([5, 5, 6], [6, 6, 5]), [5, 6]),
                         (([1, 2, 3], [4, 5, 6]), []), (([2, 2, 2], [2]), [2])])
        r.append(_check(f"BÂTIS distribute->`{dc.etage}`(==statistiques) intersect_multi->`{im.etage}`(==ensembles)",
                        resolu(dc) and resolu(im)))

        # ---- 2. NOMBRES ----------------------------------------------------------------------------------------
        vp = ia.demande("valid_perfect_square", "num", [((16,), True), ((14,), False)],
                        [((4,), True), ((9,), True), ((2,), False), ((100,), True), ((99,), False), ((1,), True)])
        ug = ia.demande("ugly_number", "n", [((6,), True), ((14,), False)],
                        [((8,), True), ((1,), True), ((30,), True), ((7,), False), ((0,), False), ((25,), True)])
        sq = ia.demande("sqrt_int", "x", [((4,), 2), ((8,), 2)],
                        [((0,), 0), ((1,), 1), ((16,), 4), ((99,), 9), ((100,), 10), ((15,), 3)])
        r.append(_check(f"NOMBRES valid_perfect->`{vp.etage}`(==diviseurs) ugly->`{ug.etage}`(==diviseurs) sqrt->`{sq.etage}`(==math-avance)",
                        resolu(vp) and resolu(ug) and resolu(sq)))

        # ---- 3. GÉNÉRIQUES RÉELS -------------------------------------------------------------------------------
        mj = ia.demande("majority_element", "nums", [(([3, 2, 3],), 3), (([2, 2, 1, 1, 1, 2, 2],), 2)],
                        [(([1],), 1), (([5, 5, 5, 1, 1],), 5), (([0, 0, 0],), 0), (([7, 7, 7, 7, 1, 2],), 7)])
        nu = ia.demande("nth_ugly_number", "n", [((10,), 12), ((1,), 1)],
                        [((7,), 8), ((11,), 15), ((15,), 24), ((5,), 5)])
        pk = ia.demande("peak_index_in_mountain_array", "arr", [(([0, 1, 0],), 1), (([0, 2, 1, 0],), 1)],
                        [(([3, 4, 5, 1],), 2), (([0, 1, 2, 3, 4, 5, 4, 3],), 5), (([1, 3, 2],), 1), (([0, 10, 5, 2],), 1)])
        # nth_ugly_number -> étage DÉDIÉ `dp-int` (campagne <100, ex-`tableaux`).
        r.append(_check(f"GÉNÉRIQUES majority->`{mj.etage}`(==means-end) nth_ugly->`{nu.etage}`(==dp-int) peak->`{pk.etage}`(==adjacence)",
                        resolu(mj) and resolu(nu) and resolu(pk)))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v39", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 39 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
