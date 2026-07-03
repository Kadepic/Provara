"""
VAGUE 38 — matrice / grille / DP (2026-06-20, nuit, 1.5 Go). gap_probe_vague38 = 8 tâches : 4 vrais trous bâtis
(lucky_numbers_matrix, toeplitz_matrix, flip_and_invert_image via `matrice` ; min_cost_climbing_stairs via `tableaux`)
+ 4 déjà couvertes réelles (richest_customer_wealth->matrice-reduce, count_battleships->tableaux,
get_pascal_row->comptage-combinatoire, climb_stairs->recurrence). Held-out ADVERSE frais, pré-vérifiés.

Critères de MORT (4) :
  1. MATRICE-1 : lucky_numbers_matrix + toeplitz_matrix + flip_and_invert_image via `matrice`.
  2. REDUCE/TABLEAUX : richest_customer_wealth via `matrice-reduce` ; count_battleships + min_cost_climbing via `tableaux`.
  3. COMBI/RÉCUR : get_pascal_row via `comptage-combinatoire` ; climb_stairs via `recurrence`.
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

        ln = ia.demande("lucky_numbers_matrix", "matrix", [(([[3, 7, 8], [9, 11, 13], [15, 16, 17]],), [15]),
                                                           (([[1, 10, 4, 2], [9, 3, 8, 7], [15, 16, 17, 12]],), [12])],
                        [(([[7, 8], [1, 2]],), [7]), (([[3, 6], [7, 1], [5, 2]],), []), (([[5]],), [5]),
                         (([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [7])])
        tm = ia.demande("toeplitz_matrix", "matrix", [(([[1, 2, 3, 4], [5, 1, 2, 3], [9, 5, 1, 2]],), True),
                                                      (([[1, 2], [2, 2]],), False)],
                        [(([[1]],), True), (([[1, 2], [3, 1]],), True), (([[1, 2], [3, 4]],), False),
                         (([[1, 2, 3], [4, 1, 2], [5, 4, 1]],), True)])
        fi = ia.demande("flip_and_invert_image", "image",
                        [(([[1, 1, 0], [1, 0, 1], [0, 0, 0]],), [[1, 0, 0], [0, 1, 0], [1, 1, 1]])],
                        [(([[1, 0]],), [[1, 0]]), (([[1]],), [[0]]), (([[0, 0], [1, 1]],), [[1, 1], [0, 0]]),
                         (([[1, 1, 0]],), [[1, 0, 0]])])
        r.append(_check(f"MATRICE-1 lucky->`{ln.etage}` toeplitz->`{tm.etage}` flip_invert->`{fi.etage}` (==matrice)",
                        all(resolu(x) for x in (ln, tm, fi))))

        rc = ia.demande("richest_customer_wealth", "accounts", [(([[1, 2, 3], [3, 2, 1]],), 6), (([[1, 5], [7, 3], [3, 5]],), 10)],
                        [(([[2, 8, 7], [7, 1, 3], [1, 9, 5]],), 17), (([[1]],), 1), (([[5, 5, 5]],), 15)])
        cb = ia.demande("count_battleships", "board", [(([[1, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]],), 2), (([[1]],), 1)],
                        [(([[0, 0], [0, 0]],), 0), (([[1, 1, 1]],), 1), (([[1], [1], [1]],), 1), (([[1, 0, 1]],), 2)])
        mc = ia.demande("min_cost_climbing_stairs", "cost", [(([10, 15, 20],), 15), (([1, 100, 1, 1, 1, 100, 1, 1, 100, 1],), 6)],
                        [(([0, 0],), 0), (([1, 2],), 1), (([10, 15],), 10), (([0, 1, 2, 2],), 2)])
        r.append(_check(f"REDUCE/TAB richest->`{rc.etage}`(==matrice-reduce) battleships->`{cb.etage}` min_cost->`{mc.etage}`(==tableaux)",
                        resolu(rc) and resolu(cb) and resolu(mc)))

        pr = ia.demande("get_pascal_row", "rowIndex", [((3,), [1, 3, 3, 1]), ((0,), [1])],
                        [((1,), [1, 1]), ((2,), [1, 2, 1]), ((4,), [1, 4, 6, 4, 1]), ((5,), [1, 5, 10, 10, 5, 1])])
        ci = ia.demande("climb_stairs", "n", [((2,), 2), ((3,), 3)],
                        [((1,), 1), ((4,), 5), ((5,), 8), ((6,), 13)])
        r.append(_check(f"COMBI/RÉCUR pascal_row->`{pr.etage}`(==comptage-combinatoire) climb->`{ci.etage}`(==recurrence)",
                        resolu(pr) and resolu(ci)))

        inc = ia.demande("incoherent_v38", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 38 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
