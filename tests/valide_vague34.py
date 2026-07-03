"""
VAGUE 34 — tableaux / chaînes (2026-06-20, nuit, 1.5 Go). gap_probe_vague34 = 8 tâches, TOUTES de vrais trous (8/8 HORS
avant) → 8 briques : max_product_difference, max_ascending_sum, count_good_pairs, sum_of_unique, largest_altitude,
min_subsequence via `tableaux` ; max_depth_parentheses + interpret via `chaines-avancees`. Held-out ADVERSE frais, pré-vérifiés.

Critères de MORT (4) :
  1. TABLEAUX-1 : max_product_difference + max_ascending_sum + count_good_pairs via `tableaux`.
  2. TABLEAUX-2 : sum_of_unique + largest_altitude + min_subsequence via `tableaux`.
  3. CHAÎNE : max_depth_parentheses + interpret via `chaines-avancees`.
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

        mpd = ia.demande("max_product_difference", "nums", [(([5, 6, 2, 7, 4],), 34), (([4, 2, 5, 9, 7, 4, 8],), 64)],
                         [(([1, 2, 3, 4],), 10), (([10, 10, 10, 10],), 0), (([1, 5, 4, 5],), 21)])
        ma = ia.demande("max_ascending_sum", "nums", [(([10, 20, 30, 5, 10, 50],), 65), (([12, 17, 15, 13, 10, 11, 12],), 33)],
                        [(([10, 20, 30, 40, 50],), 150), (([100],), 100), (([3, 3, 3],), 3), (([6, 5, 4, 3, 2, 1],), 6)])
        cg = ia.demande("count_good_pairs", "nums", [(([1, 2, 3, 1, 1, 3],), 4), (([1, 1, 1, 1],), 6)],
                        [(([1, 2, 3],), 0), (([1, 1],), 1), (([2, 2, 2],), 3)])
        r.append(_check(f"TABLEAUX-1 max_prod_diff->`{mpd.etage}` max_asc->`{ma.etage}` good_pairs->`{cg.etage}` (==tableaux)",
                        all(resolu(x) for x in (mpd, ma, cg))))

        su = ia.demande("sum_of_unique", "nums", [(([1, 2, 3, 2],), 4), (([1, 1, 2],), 2)],
                        [(([1, 1, 1, 1, 1],), 0), (([1, 2, 3, 4, 5],), 15), (([10],), 10)])
        la = ia.demande("largest_altitude", "gain", [(([-5, 1, 5, 0, -7],), 1), (([-4, -3, -2, -1, 4, 3, 2],), 0)],
                        [(([1, 2, 3],), 6), (([-1, -2],), 0),
                         (([44, 32, -9, 52, 23, -50, 50, 33, -84, 47, -14, 48],), 175)])
        ms = ia.demande("min_subsequence", "nums", [(([4, 3, 10, 9, 8],), [10, 9]), (([4, 4, 7, 6, 7],), [7, 7, 6])],
                        [(([6],), [6]), (([10, 5],), [10]), (([2, 3, 1, 5, 4],), [5, 4])])
        r.append(_check(f"TABLEAUX-2 sum_unique->`{su.etage}` largest_alt->`{la.etage}` min_subseq->`{ms.etage}` (==tableaux)",
                        all(resolu(x) for x in (su, la, ms))))

        md = ia.demande("max_depth_parentheses", "s", [(("(1+(2*3)+((8)/4))+1",), 3), (("(1)+((2))+(((3)))",), 3)],
                        [(("",), 0), (("()",), 1), (("(())",), 2), (("()()",), 1)])
        it = ia.demande("interpret", "command", [(("G()(al)",), "Goal"), (("G",), "G")],
                        [(("()()",), "oo"), (("(al)",), "al"), (("G()()()()(al)",), "Gooooal")])
        r.append(_check(f"CHAÎNE max_depth->`{md.etage}` interpret->`{it.etage}` (==chaines-avancees)",
                        all(resolu(x) for x in (md, it))))

        inc = ia.demande("incoherent_v34", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 34 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
