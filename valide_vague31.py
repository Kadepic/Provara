"""
VAGUE 31 — matrice / numération / chiffres / chaînes (2026-06-20, nuit, 1.5 Go). gap_probe_vague31 = 8 tâches : 4 vrais
trous bâtis (matrix_diagonal_sum via `matrice` [les 2 diagonales, le générateur ne sommait qu'UNE] ; number_of_steps via
`numerique` ; subtract_product_and_sum via `chiffres` ; balanced_string_split via `chaines-avancees`) + 4 DÉJÀ couvertes
réelles (running_sum->pli, transpose->matrice, intersection->ensembles, max_consecutive_ones->pile). Held-out ADVERSE frais.

Critères de MORT (4) :
  1. MATRICE/NUM : matrix_diagonal_sum via `matrice` ; number_of_steps via `numerique`.
  2. CHIFFRES/CHAÎNE : subtract_product_and_sum via `chiffres` ; balanced_string_split via `chaines-avancees`.
  3. COUVERT-RÉEL : running_sum via `pli` ; transpose via `matrice` ; intersection via `ensembles`.
  4. NON-RÉG + HORS : max_consecutive_ones généralise ; incohérent -> HORS.

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

        md = ia.demande("matrix_diagonal_sum", "mat", [(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), 25), (([[5]],), 5)],
                        [(([[1, 2], [3, 4]],), 10), (([[1, 0, 0], [0, 1, 0], [0, 0, 1]],), 3),
                         (([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],), 68)])
        ns = ia.demande("number_of_steps", "n", [((14,), 6), ((8,), 4)],
                        [((0,), 0), ((1,), 1), ((123,), 12), ((6,), 4), ((2,), 2)])
        r.append(_check(f"MATRICE/NUM matrix_diagonal_sum->`{md.etage}`(==matrice) number_of_steps->`{ns.etage}`(==numerique)",
                        resolu(md) and resolu(ns)))

        sp = ia.demande("subtract_product_and_sum", "n", [((234,), 15), ((4421,), 21)],
                        [((1,), 0), ((10,), -1), ((99,), 63), ((5,), 0)])
        bs = ia.demande("balanced_string_split", "s", [(("RLRRLLRLRL",), 4), (("RLLLLRRRLR",), 3)],
                        [(("RL",), 1), (("RRLL",), 1), (("RLRL",), 2), (("LLLLRRRR",), 1)])
        r.append(_check(f"CHIFFRES/CHAÎNE subtract_ps->`{sp.etage}`(==chiffres) balanced_split->`{bs.etage}`(==chaines)",
                        resolu(sp) and resolu(bs)))

        rs = ia.demande("running_sum", "nums", [(([1, 2, 3, 4],), [1, 3, 6, 10]), (([1, 1, 1],), [1, 2, 3])],
                        [(([3, 1, 2, 10, 1],), [3, 4, 6, 16, 17]), (([0],), [0]), (([5, 5],), [5, 10])])
        tr = ia.demande("transpose", "matrix", [(([[1, 2, 3], [4, 5, 6]],), [[1, 4], [2, 5], [3, 6]]), (([[1]],), [[1]])],
                        [(([[1, 2], [3, 4]],), [[1, 3], [2, 4]]), (([[1, 2, 3]],), [[1], [2], [3]]), (([[1], [2]],), [[1, 2]])])
        it = ia.demande("intersection", "nums1, nums2", [(([1, 2, 2, 1], [2, 2]), [2]), (([4, 9, 5], [9, 4, 9, 8, 4]), [4, 9])],
                        [(([1, 2, 3], [4, 5]), []), (([3, 1, 2], [2, 3]), [2, 3]), (([1, 1], [1]), [1])])
        r.append(_check(f"COUVERT-RÉEL running_sum->`{rs.etage}`(==pli) transpose->`{tr.etage}`(==matrice) intersection->`{it.etage}`(==ensembles)",
                        resolu(rs) and resolu(tr) and resolu(it)))

        mc = ia.demande("max_consecutive_ones", "nums", [(([1, 1, 0, 1, 1, 1],), 3), (([1, 0, 1, 1, 0, 1],), 2)],
                        [(([0],), 0), (([1, 1, 1, 1],), 4), (([0, 0, 0],), 0), (([1, 0, 1],), 1)])
        inc = ia.demande("incoherent_v31", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"NON-RÉG max_consecutive_ones->`{mc.etage}`(gen={mc.generalise}) | HORS ok={inc.ok}",
                        resolu(mc) and not inc.ok))

    print()
    print("VAGUE 31 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
