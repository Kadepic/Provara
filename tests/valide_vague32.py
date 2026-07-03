"""
VAGUE 32 — tableaux / grille / chaînes (2026-06-20, nuit, 1.5 Go). gap_probe_vague32 = 8 tâches, TOUTES de vrais trous
(8/8 HORS avant) → 8 briques bâties : monotonic, island_perimeter, set_mismatch, maximum_product_of_three,
array_pair_sum, find_lucky, height_checker via `tableaux` ; judge_circle via `chaines-avancees`. Held-out ADVERSE frais.

Critères de MORT (4) :
  1. TABLEAUX-1 : monotonic + island_perimeter via `tableaux`.
  2. TABLEAUX-2 : set_mismatch + maximum_product_of_three + array_pair_sum via `tableaux`.
  3. TABLEAUX-3/CHAÎNE : find_lucky + height_checker via `tableaux` ; judge_circle via `chaines-avancees`.
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

        mo = ia.demande("monotonic", "nums", [(([1, 2, 2, 3],), True), (([1, 3, 2],), False)],
                        [(([5, 4, 3, 2],), True), (([1, 2, 1],), False), (([7],), True), (([2, 2],), True)])
        ip = ia.demande("island_perimeter", "grid",
                        [(([[0, 1, 0, 0], [1, 1, 1, 0], [0, 1, 0, 0], [1, 1, 0, 0]],), 16), (([[1]],), 4)],
                        [(([[1, 1], [1, 1]],), 8), (([[0, 1, 0], [1, 1, 1], [0, 1, 0]],), 12), (([[1, 0, 1]],), 8)])
        r.append(_check(f"TABLEAUX-1 monotonic->`{mo.etage}` island_perimeter->`{ip.etage}` (==tableaux)",
                        all(resolu(x) for x in (mo, ip))))

        sm = ia.demande("set_mismatch", "nums", [(([1, 2, 2, 4],), [2, 3]), (([1, 1],), [1, 2])],
                        [(([3, 2, 2, 4],), [2, 1]), (([1, 3, 3],), [3, 2]), (([2, 2],), [2, 1])])
        mp = ia.demande("maximum_product_of_three", "nums", [(([1, 2, 3],), 6), (([-10, -10, 5, 2],), 500)],
                        [(([1, 2, 3, 4],), 24), (([-4, -3, -2, -1, 60],), 720), (([0, -1, 3, 100, 70, 50],), 350000),
                         (([-1, -2, -3],), -6)])
        ap = ia.demande("array_pair_sum", "nums", [(([1, 4, 3, 2],), 4), (([6, 2, 6, 5, 1, 2],), 9)],
                        [(([1, 1],), 1), (([0, 0],), 0), (([7, 3, 1, 0, 0, 6],), 7)])
        r.append(_check(f"TABLEAUX-2 set_mismatch->`{sm.etage}` max_prod3->`{mp.etage}` array_pair->`{ap.etage}` (==tableaux)",
                        all(resolu(x) for x in (sm, mp, ap))))

        fl = ia.demande("find_lucky", "arr", [(([2, 2, 3, 4],), 2), (([1, 2, 2, 3, 3, 3],), 3)],
                        [(([5],), -1), (([7, 7, 7, 7, 7, 7, 7],), 7), (([2, 2, 2, 3, 3],), -1), (([1],), 1)])
        hc = ia.demande("height_checker", "heights", [(([1, 1, 4, 2, 1, 3],), 3), (([5, 1, 2, 3, 4],), 5)],
                        [(([1, 2, 3],), 0), (([2, 1],), 2), (([1, 1, 1],), 0), (([4, 3, 2, 1],), 4)])
        jc = ia.demande("judge_circle", "moves", [(("UD",), True), (("LL",), False)],
                        [(("",), True), (("UDLR",), True), (("UUDD",), True), (("UUUU",), False), (("LDRRLRUULR",), False)])
        r.append(_check(f"TAB-3/CHAÎNE find_lucky->`{fl.etage}` height_checker->`{hc.etage}`(==tableaux) judge_circle->`{jc.etage}`(==chaines)",
                        resolu(fl) and resolu(hc) and resolu(jc)))

        inc = ia.demande("incoherent_v32", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 32 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
