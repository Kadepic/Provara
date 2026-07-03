"""
VAGUE 35 — tableaux / numération (2026-06-20, nuit, 1.5 Go). gap_probe_vague35 = 8 tâches, TOUTES de vrais trous (8/8
HORS avant) → 8 briques : can_make_arithmetic_progression, three_consecutive_odds, largest_unique_number,
find_numbers_with_even_digits, number_of_arithmetic_slices, min_operations, sum_odd_length_subarrays via `tableaux` ;
maximum_69_number via `chiffres`. Held-out ADVERSE frais, pré-vérifiés par référence.

Critères de MORT (4) :
  1. TABLEAUX-1 : can_make_arithmetic_progression + three_consecutive_odds + largest_unique_number via `tableaux`.
  2. TABLEAUX-2 : find_numbers_with_even_digits + number_of_arithmetic_slices via `tableaux`.
  3. TABLEAUX-3/NUM : min_operations + sum_odd_length_subarrays via `tableaux` ; maximum_69_number via `chiffres`.
  4. HORS HONNÊTE : incohérent -> HORS.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurTableaux
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        ap = ia.demande("can_make_arithmetic_progression", "arr", [(([3, 5, 1],), True), (([1, 2, 4],), False)],
                        [(([1],), True), (([1, 3],), True), (([5, 5, 5],), True), (([1, 2, 4, 8],), False)])
        tc = ia.demande("three_consecutive_odds", "arr", [(([2, 6, 4, 1],), False), (([1, 2, 34, 3, 4, 5, 7, 23, 12],), True)],
                        [(([1, 1, 1],), True), (([1, 2, 1],), False), (([3, 5, 7],), True), (([2, 4, 6],), False)])
        lu = ia.demande("largest_unique_number", "nums", [(([5, 7, 3, 9, 4, 9, 8, 3, 1],), 8), (([9, 9, 8, 8],), -1)],
                        [(([8, 8, 7, 6, 5, 5],), 7), (([1],), 1), (([1, 1],), -1), (([10, 20, 20],), 10)])
        r.append(_check(f"TABLEAUX-1 arith_prog->`{ap.etage}` three_odds->`{tc.etage}` largest_uniq->`{lu.etage}` (==tableaux)",
                        all(resolu(x) for x in (ap, tc, lu))))

        fn = ia.demande("find_numbers_with_even_digits", "nums", [(([12, 345, 2, 6, 7896],), 2), (([555, 901, 482, 1771],), 1)],
                        [(([1, 22, 333],), 1), (([10, 100],), 1), (([1, 2, 3],), 0), (([1234],), 1)])
        na = ia.demande("number_of_arithmetic_slices", "nums", [(([1, 2, 3, 4],), 3), (([1, 3, 5, 7, 9],), 6)],
                        [(([1, 2, 3],), 1), (([1, 2, 4],), 0), (([7, 7, 7, 7],), 3), (([1],), 0)])
        r.append(_check(f"TABLEAUX-2 even_digits->`{fn.etage}` arith_slices->`{na.etage}` (==tableaux)",
                        all(resolu(x) for x in (fn, na))))

        mo = ia.demande("min_operations", "nums", [(([1, 1, 1],), 3), (([1, 5, 2, 4, 1],), 14)],
                        [(([1, 2, 3],), 0), (([1, 1, 1, 1],), 6), (([8],), 0), (([3, 2, 1],), 6)])
        so = ia.demande("sum_odd_length_subarrays", "arr", [(([1, 4, 2, 5, 3],), 58), (([10, 11, 12],), 66)],
                        [(([1, 2],), 3), (([1],), 1), (([5, 5, 5],), 30)])
        m69 = ia.demande("maximum_69_number", "num", [((9669,), 9969), ((9996,), 9999)],
                         [((6,), 9), ((66,), 96), ((9,), 9), ((696,), 996), ((9999,), 9999)])
        r.append(_check(f"TAB-3/NUM min_ops->`{mo.etage}` sum_odd->`{so.etage}`(==tableaux) max69->`{m69.etage}`(==chiffres)",
                        resolu(mo) and resolu(so) and resolu(m69)))

        inc = ia.demande("incoherent_v35", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        # VIVACITÉ (anti-code-mort) : la brique spécialiste `tableaux` résout SA tâche canonique
        # can_make_arithmetic_progression en DIRECT (hors routeur) sur tests + held-out adverse.
        r.append(_check("VIVACITÉ : la brique `tableaux` résout can_make_arithmetic_progression en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurTableaux(), "can_make_arithmetic_progression", "arr",
                                       "def check(c):\n    assert c([3,5,1])==True\n    assert c([1,2,4])==False\ncheck(can_make_arithmetic_progression)",
                                       "def check(c):\n    assert c([1])==True\n    assert c([1,3])==True\n    assert c([5,5,5])==True\n    assert c([1,2,4,8])==False\ncheck(can_make_arithmetic_progression)")))

    print()
    print(f"VAGUE 35 VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
