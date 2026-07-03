"""
VAGUE 14 — INTERVAL SCHEDULING (transfer web) + breadth (2026-06-19, nuit). Lacunes MESURÉES par gap_probe_vague14
(6 vrais HORS, held-out DURCIS). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. INTERVALLES (struct) : merge_intervals + insert_interval via `chevauchement`.
  2. INTERVALLES (scalaire) : max_non_overlapping + union_length via `chevauchement`.
  3. BREADTH : gcd_list via `numerique` ; longest_subarray_sum_k via `tableaux`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; min_meeting_rooms + max_overlap restent via `chevauchement`.

SÉQUENTIEL + garde.
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

        mi = ia.demande("merge_intervals", "intervals",
                        [(([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]), (([[1, 4], [4, 5]],), [[1, 5]])],
                        [(([[1, 4], [0, 4]],), [[0, 4]]), (([[1, 2], [3, 4]],), [[1, 2], [3, 4]])])
        ii = ia.demande("insert_interval", "intervals, novel",
                        [(([[1, 3], [6, 9]], [2, 5]), [[1, 5], [6, 9]]), (([[1, 5]], [2, 3]), [[1, 5]])],
                        [(([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]), [[1, 2], [3, 10], [12, 16]]),
                         (([], [5, 7]), [[5, 7]])])
        r.append(_check(f"INTERVALLES struct merge->`{mi.etage}` insert->`{ii.etage}` (==chevauchement)",
                        resolu(mi) and resolu(ii)))

        # held-out DURCI (2026-06-24) : [[0,4],[0,2]]->1 et [[3,5],[2,5]]->1 DISCRIMINENT activity-selection de
        # `wiggle_max_length` (tableaux) qui coïncidait sur l'ancien held faible -> force le bon étage `chevauchement`.
        mn = ia.demande("max_non_overlapping", "intervals", [(([[1, 2], [2, 3], [3, 4], [1, 3]],), 3), (([[1, 2], [7, 8], [4, 5]],), 3)],
                        [(([[1, 3], [2, 4], [3, 5]],), 2), (([[1, 2]],), 1), (([[1, 10], [2, 3], [3, 4]],), 2),
                         (([[0, 4], [0, 2]],), 1), (([[3, 5], [2, 5]],), 1)])
        ul = ia.demande("union_length", "intervals", [(([[1, 3], [2, 4]],), 3), (([[1, 2], [3, 4]],), 2)],
                        [(([[1, 5], [2, 3]],), 4), (([[1, 3], [3, 5]],), 4), (([[1, 2]],), 1)])
        r.append(_check(f"INTERVALLES scalaire max_no->`{mn.etage}` union->`{ul.etage}` (==chevauchement)",
                        resolu(mn) and resolu(ul)))

        gl = ia.demande("gcd_list", "xs", [(([12, 18, 24],), 6), (([7, 14],), 7)], [(([5],), 5), (([9, 6],), 3), (([100, 80, 60],), 20)])
        ls = ia.demande("longest_subarray_sum_k", "xs, k", [(([1, -1, 5, -2, 3], 3), 4), (([-2, -1, 2, 1], 1), 2)],
                        [(([1, 2, 3], 6), 3), (([1, 2, 3], 7), 0), (([0, 0, 0], 0), 3)])
        r.append(_check(f"BREADTH gcd_list->`{gl.etage}`(==numerique) lsk->`{ls.etage}`(==tableaux)",
                        resolu(gl) and resolu(ls)))

        inc = ia.demande("incoherent_v14", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        mr = ia.demande("min_meeting_rooms", "intervals", [(([[0, 30], [5, 10], [15, 20]],), 2), (([[7, 10], [2, 4]],), 1)],
                        [(([[1, 5], [2, 6], [3, 7]],), 3), (([[1, 2], [2, 3]],), 1)])
        mo = ia.demande("max_overlap", "intervals", [(([[1, 4], [2, 5], [7, 8]],), 2), (([[1, 2], [3, 4]],), 1)],
                        [(([[1, 10], [2, 3], [4, 5]],), 2)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG rooms->`{mr.etage}` overlap->`{mo.etage}`",
                        not inc.ok and resolu(mr) and resolu(mo)))

    print()
    print("VAGUE 14 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
