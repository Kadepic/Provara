"""
VAGUE 27 — pile / tableaux / numération / bits (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par gap_probe_vague27
(7 vrais trous). Validées dans le MOTEUR COMPLET, held-out ADVERSE (exemples frais, distincts de la sonde).

Critères de MORT (4) :
  1. PILE : longest_valid_parentheses via `pile`.
  2. TABLEAUX : shortest_unsorted_subarray + max_distance_to_closest via `tableaux`.
  3. NUMÉRATION : nth_digit + integer_replacement + divide_integers via `numerique`.
  4. BITS + HORS + NON-RÉG : count_bits_list via `bits` ; incohérent -> HORS ; max_chunks_to_sort généralise.

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

        lp = ia.demande("longest_valid_parentheses", "s", [(("(()",), 2), ((")()())",), 4)],
                        [(("",), 0), ((")(",), 0), (("(())",), 4), (("()(())",), 6), (("()))",), 2)])
        r.append(_check(f"PILE longest_valid_parentheses->`{lp.etage}`",
                        resolu(lp)))

        su = ia.demande("shortest_unsorted_subarray", "nums",
                        [(([2, 6, 4, 8, 10, 9, 15],), 5), (([1, 2, 3, 4],), 0)],
                        [(([1],), 0), (([2, 1],), 2), (([1, 3, 5, 4, 2],), 4), (([5, 4, 3, 2, 1],), 5)])
        md = ia.demande("max_distance_to_closest", "seats",
                        [(([1, 0, 0, 0, 1, 0, 1],), 2), (([1, 0, 0, 0],), 3)],
                        [(([0, 0, 1],), 2), (([1, 0, 1],), 1), (([0, 1],), 1), (([1, 0, 0, 1],), 1)])
        r.append(_check(f"TABLEAUX shortest_unsorted->`{su.etage}` max_distance->`{md.etage}`",
                        all(resolu(x) for x in (su, md))))

        nd = ia.demande("nth_digit", "n", [((3,), 3), ((11,), 0)],
                        [((1,), 1), ((10,), 1), ((15,), 2), ((7,), 7), ((12,), 1)])
        ir = ia.demande("integer_replacement", "n", [((8,), 3), ((7,), 4)],
                        [((1,), 0), ((2,), 1), ((4,), 2), ((15,), 5), ((3,), 2)])
        di = ia.demande("divide_integers", "a, b", [((10, 3), 3), ((7, -2), -3)],
                        [((-7, 2), -3), ((10, 2), 5), ((1, 1), 1), ((-10, -3), 3), ((-8, 3), -2)])
        r.append(_check(f"NUMÉRATION nth_digit->`{nd.etage}` int_replace->`{ir.etage}` divide->`{di.etage}`",
                        all(resolu(x) for x in (nd, ir, di))))

        cb = ia.demande("count_bits_list", "n", [((5,), [0, 1, 1, 2, 1, 2]), ((0,), [0])],
                        [((2,), [0, 1, 1]), ((1,), [0, 1]), ((7,), [0, 1, 1, 2, 1, 2, 2, 3]), ((4,), [0, 1, 1, 2, 1])])
        inc = ia.demande("incoherent_v27", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        mc = ia.demande("max_chunks_to_sort", "arr", [(([4, 3, 2, 1, 0],), 1), (([1, 0, 2, 3, 4],), 4)],
                        [(([0, 1, 2, 3],), 4), (([2, 0, 1],), 1), (([1, 2, 0],), 1)])
        r.append(_check(f"BITS count_bits->`{cb.etage}` | HORS ok={inc.ok} | NON-RÉG chunks->`{mc.etage}`",
                        resolu(cb) and not inc.ok and resolu(mc)))

    print()
    print("VAGUE 27 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
