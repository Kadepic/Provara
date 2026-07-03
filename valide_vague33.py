"""
VAGUE 33 — tableaux / grille / chaîne / numération (2026-06-20, nuit, 1.5 Go). gap_probe_vague33 = 8 tâches : 7 vrais
trous bâtis (sort_array_by_parity, valid_mountain_array, count_negatives, largest_perimeter_triangle,
replace_elements_with_greatest_on_right via `tableaux` ; defanging_ip via `chaines-avancees` ; count_odds via
`numerique`) + 1 déjà couverte réelle (squares_of_sorted_array via `means-end`). Held-out ADVERSE frais, pré-vérifiés.

Critères de MORT (4) :
  1. TABLEAUX-1 : sort_array_by_parity + valid_mountain_array via `tableaux`.
  2. TABLEAUX-2 : count_negatives + largest_perimeter_triangle + replace_elements via `tableaux`.
  3. CHAÎNE/NUM : defanging_ip via `chaines-avancees` ; count_odds via `numerique` ; squares_of_sorted_array généralise.
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

        sp = ia.demande("sort_array_by_parity", "nums", [(([3, 1, 2, 4],), [2, 4, 3, 1]), (([0, 1, 2],), [0, 2, 1])],
                        [(([1, 3],), [1, 3]), (([2, 4],), [2, 4]), (([4, 1, 7, 2],), [4, 2, 1, 7]), (([],), [])])
        vm = ia.demande("valid_mountain_array", "arr", [(([0, 3, 2, 1],), True), (([3, 5, 5],), False)],
                        [(([2, 1],), False), (([1, 3, 2],), True), (([0, 1, 2, 3],), False), (([0, 2, 3, 4, 5, 2, 1],), True)])
        r.append(_check(f"TABLEAUX-1 sort_by_parity->`{sp.etage}` valid_mountain->`{vm.etage}` (==tableaux)",
                        all(resolu(x) for x in (sp, vm))))

        cn = ia.demande("count_negatives", "grid",
                        [(([[4, 3, 2, -1], [3, 2, 1, -1], [1, 1, -1, -2], [-1, -1, -2, -3]],), 8), (([[3, 2], [1, 0]],), 0)],
                        [(([[-1]],), 1), (([[1, -1], [-1, -1]],), 3), (([[-5, -5], [-5, -5]],), 4)])
        lp = ia.demande("largest_perimeter_triangle", "nums", [(([2, 1, 2],), 5), (([1, 2, 1],), 0)],
                        [(([3, 2, 3, 4],), 10), (([3, 6, 2, 3],), 8), (([1, 1, 1],), 3), (([1, 1, 10],), 0)])
        re_ = ia.demande("replace_elements_with_greatest_on_right", "arr",
                         [(([17, 18, 5, 4, 6, 1],), [18, 6, 6, 6, 1, -1]), (([400],), [-1])],
                         [(([1, 2, 3],), [3, 3, -1]), (([5, 5],), [5, -1]), (([2, 1],), [1, -1])])
        r.append(_check(f"TABLEAUX-2 count_neg->`{cn.etage}` largest_perim->`{lp.etage}` replace->`{re_.etage}` (==tableaux)",
                        all(resolu(x) for x in (cn, lp, re_))))

        di = ia.demande("defanging_ip", "address", [(("1.1.1.1",), "1[.]1[.]1[.]1"), (("255.100.50.0",), "255[.]100[.]50[.]0")],
                        [(("0.0.0.0",), "0[.]0[.]0[.]0"), (("192.168.1.1",), "192[.]168[.]1[.]1")])
        co = ia.demande("count_odds", "low, high", [((3, 7), 3), ((8, 10), 1)],
                        [((0, 0), 0), ((1, 1), 1), ((0, 10), 5), ((2, 4), 1), ((1, 10), 5)])
        sq = ia.demande("squares_of_sorted_array", "nums", [(([-4, -1, 0, 3, 10],), [0, 1, 9, 16, 100]), (([-2, -1],), [1, 4])],
                        [(([-7, -3, 2, 3, 11],), [4, 9, 9, 49, 121]), (([0],), [0]), (([1, 2, 3],), [1, 4, 9])])
        r.append(_check(f"CHAÎNE/NUM defanging->`{di.etage}`(==chaines) count_odds->`{co.etage}`(==numerique) squares->`{sq.etage}`(gen={sq.generalise})",
                        resolu(di) and resolu(co) and resolu(sq)))

        inc = ia.demande("incoherent_v33", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 33 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
