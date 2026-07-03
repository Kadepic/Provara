"""
VAGUE 51 — DEUX-POINTEURS / PARTITION DE TABLEAU (2026-06-23 nuit, autonomie). gap_probe_vague51 = 6 tâches :
2 VRAIS TROUS bâtis + 4 confirmées (held-out durci).

Bâtis cette vague :
  • `three_sum_count` -> `comptage-combinatoire` (tri + deux pointeurs, dédup par ensemble ; placé HORS de tableaux
    pour limiter le churn round-robin).
  • `dominant_index` -> `tableaux` (max ≥ 2× tous les autres -> index, sinon -1).
Confirmées À FROID : find_pivot_index, move_zeroes (`tableaux`), count_pairs_sum (`comptage-combinatoire`),
max_consecutive_ones (`pile`). ÉTAGES des confirmées NON épinglés (round-robin instable) -> on exige ok+generalise
sur held DURCI (leçon partition_labels). Les 2 BÂTIES sont épinglées (briques neuves, étage stable).

Critères de MORT (4) :
  1. TROUS BÂTIS : three_sum_count + dominant_index (épinglés, held durci).
  2. PRÉFIXES/RUNS : find_pivot_index + count_pairs_sum + max_consecutive_ones (ok+generalise, held durci).
  3. MOUVEMENT : move_zeroes (ok+generalise, held durci).
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

        # ---- 1. TROUS BÂTIS (épinglés) --------------------------------------------------------------------
        ts = ia.demande("three_sum_count", "nums", [(([-1, 0, 1, 2, -1, -4],), 2), (([0, 0, 0],), 1)],
                        [(([1, 2, 3],), 0), (([0, 1, 1],), 0), (([-2, 0, 1, 1, 2],), 2),
                         (([3, 0, -2, -1, 1, 2],), 3), (([],), 0)])
        di = ia.demande("dominant_index", "nums", [(([3, 6, 1, 0],), 1), (([1, 2, 3, 4],), -1)],
                        [(([1],), 0), (([0, 0, 3, 2],), -1), (([6, 2, 3, 1],), 0),
                         (([0, 0, 0, 1],), 3), (([8, 4, 2, 1],), 0)])
        r.append(_check(f"TROUS three_sum_count->`{ts.etage}`(==comptage-combinatoire) dominant_index->`{di.etage}`(==tableaux)",
                        resolu(ts) and resolu(di)))

        # ---- 2. PRÉFIXES / RUNS (ok+generalise, held durci) ----------------------------------------------
        fp = ia.demande("find_pivot_index", "nums", [(([1, 7, 3, 6, 5, 6],), 3), (([1, 2, 3],), -1)],
                        [(([2, 1, -1],), 0), (([0],), 0), (([1, -1, 0],), 2), (([-1, -1, -1, 0, 1, 1],), 0)])
        cps = ia.demande("count_pairs_sum", "nums, target", [(([1, 2, 3, 4], 5), 2), (([1, 1, 1, 1], 2), 6)],
                         [(([5], 10), 0), (([3, 3, 3], 6), 3), (([1, 2, 3], 7), 0), (([2, 2, 2, 2], 4), 6)])
        mc = ia.demande("max_consecutive_ones", "nums", [(([1, 1, 0, 1, 1, 1],), 3), (([1, 0, 1, 1, 0, 1],), 2)],
                        [(([0, 0],), 0), (([1, 1, 1],), 3), (([0],), 0), (([1, 1, 0, 1, 1, 1, 1],), 4)])
        r.append(_check(f"PRÉFIXES/RUNS find_pivot->`{fp.etage}` count_pairs->`{cps.etage}` max_ones->`{mc.etage}`",
                        all(resolu(x) for x in (fp, cps, mc))))

        # ---- 3. MOUVEMENT (ok+generalise, held durci) ----------------------------------------------------
        mz = ia.demande("move_zeroes", "nums", [(([0, 1, 0, 3, 12],), [1, 3, 12, 0, 0]), (([0, 0, 1],), [1, 0, 0])],
                        [(([1, 2, 3],), [1, 2, 3]), (([0],), [0]), (([1, 0, 0, 2],), [1, 2, 0, 0]),
                         (([0, 0, 0],), [0, 0, 0]), (([5, 0, 5, 0],), [5, 5, 0, 0])])
        r.append(_check(f"MOUVEMENT move_zeroes->`{mz.etage}`", resolu(mz)))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------
        inc = ia.demande("incoherent_v51", "nums", [(([1],), 42)], [(([2],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 51 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
