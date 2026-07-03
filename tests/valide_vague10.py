"""
VAGUE 10 — géométrie computationnelle / CRT / DP / chaînes (2026-06-19, autonomie). Lacunes MESURÉES par
gap_probe_vague10 : 8 vrais trous, dont **4 ex-COÏNCIDENCES** (point_in_polygon via bits, segments_intersect via
math-avance, merge_sorted via ensembles, hamming_str via dp2d) débusquées à froid sur held-out durci -> ancrées en
1ʳᵉ classe. Held-out DURCIS ici exprès. Validées dans le MOTEUR COMPLET.

Critères de MORT (4) :
  1. GÉOMÉTRIE : convex_hull_size + segments_intersect + point_in_polygon via `geometrie`.
  2. CRT + DP : crt2 via `diviseurs` ; matrix_chain_min + max_sum_increasing_subseq + merge_sorted via `tableaux`.
  3. CHAÎNE : hamming_str via `chaines-avancees`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; manhattan via `geometrie`, kth_smallest via `index-ordonne`.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from valide_commun import resolu

SQ = [(0, 0), (4, 0), (4, 4), (0, 4)]


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        ch = ia.demande("convex_hull_size", "points", [(([(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)],), 4)],
                        [(([(0, 0), (1, 1), (2, 2), (3, 3)],), 2), (([(0, 0), (4, 0), (2, 3)],), 3),
                         (([(0, 0), (4, 0), (4, 4), (0, 4), (2, 2), (1, 1)],), 4)])
        si = ia.demande("segments_intersect", "x1, y1, x2, y2, x3, y3, x4, y4",
                        [((0, 0, 2, 2, 0, 2, 2, 0), True), ((0, 0, 1, 1, 2, 2, 3, 3), False)],
                        [((0, 0, 4, 4, 0, 4, 4, 0), True), ((0, 0, 1, 1, 5, 5, 6, 6), False),
                         ((0, 0, 2, 0, 2, 0, 2, 2), True), ((0, 0, 2, 0, 0, 1, 2, 1), False)])
        pp = ia.demande("point_in_polygon", "px, py, poly", [((1, 1, SQ), True), ((5, 5, SQ), False)],
                        [((2, 2, SQ), True), ((3, 1, SQ), True), ((-1, 2, SQ), False), ((2, 5, SQ), False),
                         ((2, 1, [(0, 0), (4, 0), (2, 4)]), True), ((0, 3, [(0, 0), (4, 0), (2, 4)]), False)])
        r.append(_check(f"GÉO hull->`{ch.etage}` seg->`{si.etage}` poly->`{pp.etage}` (résolu, étage libre)",
                        all(resolu(x) for x in (ch, si, pp))))

        cr = ia.demande("crt2", "a1, m1, a2, m2", [((2, 3, 3, 5), 8), ((0, 2, 0, 3), 0)], [((1, 2, 2, 3), 5), ((1, 3, 4, 5), 4)])
        mc = ia.demande("matrix_chain_min", "dims", [(([1, 2, 3, 4],), 18), (([10, 20, 30],), 6000)],
                        [(([5, 10, 3],), 150), (([40, 20, 30, 10, 30],), 26000)])
        ms = ia.demande("max_sum_increasing_subseq", "xs", [(([1, 101, 2, 3, 100],), 106), (([3, 4, 5, 10],), 22)],
                        [(([10, 5, 4, 3],), 10), (([1, 2, 3],), 6), (([],), 0)])
        mg = ia.demande("merge_sorted", "a, b", [(([1, 3, 5], [2, 4]), [1, 2, 3, 4, 5]), (([], [1]), [1])],
                        [(([1, 1, 2], [1, 3]), [1, 1, 1, 2, 3]), (([2, 2], [2]), [2, 2, 2])])
        r.append(_check(f"CRT crt2->`{cr.etage}` | DP mc->`{mc.etage}` msis->`{ms.etage}` merge->`{mg.etage}` (résolu, étage libre)",
                        resolu(cr) and all(resolu(x) for x in (mc, ms, mg))))

        hm = ia.demande("hamming_str", "a, b", [(("karolin", "kathrin"), 3), (("abc", "abc"), 0)],
                        [(("abc", "bca"), 3), (("0000", "1111"), 4), (("ab", "ba"), 2), (("abcd", "abce"), 1)])
        r.append(_check(f"CHAÎNE hamming_str->`{hm.etage}` (résolu, étage libre)",
                        resolu(hm)))

        inc = ia.demande("incoherent_v10", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        mh = ia.demande("manhattan", "x1, y1, x2, y2", [((0, 0, 3, 4), 7), ((1, 1, 1, 1), 0)], [((-1, -1, 2, 3), 7)])
        ks = ia.demande("kth_smallest", "xs, k", [(([3, 1, 2], 2), 2), (([5, 4], 1), 4)], [(([9, 7, 8], 3), 9)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG manhattan->`{mh.etage}` kth->`{ks.etage}`",
                        not inc.ok and resolu(mh) and resolu(ks)))

    print()
    print("VAGUE 10 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
