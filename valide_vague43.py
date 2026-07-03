"""
VAGUE 43 — INTERVALLES (domaine étendu) + MATRICE + TRI-COMPARATEUR (2026-06-20, reprise post-redémarrage, 1.5 Go).
gap_probe_vague43 = 8 tâches : 6 vrais trous bâtis + 2 réelles (merge_intervals, rotate_image).

Bâtis : can_attend_meetings + min_arrows (burst balloons) + erase_overlap -> `chevauchement` (greedy d'ordonnancement
d'intervalles, tri par fin) ; set_zeroes + diagonal_traverse -> `matrice` ; largest_number -> `chaines-avancees`
(tri par comparateur a+b vs b+a). LEÇON (entorse attrapée) : largest_number([432,43,43])='4343432' (pas '4324343' —
'434...' > '432...') ; held-out de sonde corrigé après coup (toujours pré-vérifier CHAQUE cas).

Critères de MORT (4) :
  1. INTERVALLES : can_attend_meetings + min_arrows + erase_overlap via `chevauchement`.
  2. MATRICE : set_zeroes + diagonal_traverse + rotate_image via `matrice`.
  3. RÉELS : merge_intervals via `chevauchement` ; largest_number via `chaines-avancees`.
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

        # ---- 1. INTERVALLES ------------------------------------------------------------------------------------
        ca = ia.demande("can_attend_meetings", "intervals", [(([[0, 30], [5, 10], [15, 20]],), False), (([[7, 10], [2, 4]],), True)],
                        [(([[1, 2], [2, 3]],), True), (([[1, 5], [3, 7]],), False), (([[1, 2]],), True), (([[5, 8], [9, 10], [3, 4]],), True)])
        ma = ia.demande("min_arrows", "points", [(([[10, 16], [2, 8], [1, 6], [7, 12]],), 2), (([[1, 2], [3, 4], [5, 6], [7, 8]],), 4)],
                        [(([[1, 2], [2, 3], [3, 4], [4, 5]],), 2), (([[1, 10]],), 1), (([[1, 2], [1, 2]],), 1), (([[2, 3], [2, 3], [3, 4], [5, 6]],), 2)])
        eo = ia.demande("erase_overlap", "intervals", [(([[1, 2], [2, 3], [3, 4], [1, 3]],), 1), (([[1, 2], [1, 2], [1, 2]],), 2)],
                        [(([[1, 2], [2, 3]],), 0), (([[1, 100], [11, 22], [1, 11], [2, 12]],), 2), (([[1, 2]],), 0), (([[1, 5], [2, 3], [3, 4]],), 1)])
        r.append(_check(f"INTERVALLES can_attend->`{ca.etage}` min_arrows->`{ma.etage}` erase_overlap->`{eo.etage}` (==chevauchement)",
                        all(resolu(x) for x in (ca, ma, eo))))

        # ---- 2. MATRICE ----------------------------------------------------------------------------------------
        sz = ia.demande("set_zeroes", "matrix", [(([[1, 1, 1], [1, 0, 1], [1, 1, 1]],), [[1, 0, 1], [0, 0, 0], [1, 0, 1]])],
                        [(([[0, 1], [1, 1]],), [[0, 0], [0, 1]]), (([[1, 2], [3, 4]],), [[1, 2], [3, 4]]), (([[1, 0, 3]],), [[0, 0, 0]])])
        dt = ia.demande("diagonal_traverse", "matrix", [(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [1, 2, 4, 7, 5, 3, 6, 8, 9])],
                        [(([[1, 2], [3, 4]],), [1, 2, 3, 4]), (([[1]],), [1]), (([[1, 2, 3]],), [1, 2, 3])])
        ri = ia.demande("rotate_image", "matrix", [(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [[7, 4, 1], [8, 5, 2], [9, 6, 3]])],
                        [(([[1, 2], [3, 4]],), [[3, 1], [4, 2]]), (([[1]],), [[1]])])
        r.append(_check(f"MATRICE set_zeroes->`{sz.etage}` diagonal->`{dt.etage}` rotate->`{ri.etage}` (==matrice)",
                        all(resolu(x) for x in (sz, dt, ri))))

        # ---- 3. RÉELS ------------------------------------------------------------------------------------------
        mi = ia.demande("merge_intervals", "intervals",
                        [(([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]), (([[1, 4], [4, 5]],), [[1, 5]])],
                        [(([[1, 4], [2, 3]],), [[1, 4]]), (([[1, 2], [3, 4]],), [[1, 2], [3, 4]]), (([[5, 6]],), [[5, 6]])])
        ln = ia.demande("largest_number", "nums", [(([10, 2],), "210"), (([3, 30, 34, 5, 9],), "9534330")],
                        [(([0, 0],), "0"), (([1],), "1"), (([432, 43, 43],), "4343432"), (([121, 12],), "12121")])
        r.append(_check(f"RÉELS merge_intervals->`{mi.etage}`(==chevauchement) largest_number->`{ln.etage}`(==chaines-avancees)",
                        resolu(mi) and resolu(ln)))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v43", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 43 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
