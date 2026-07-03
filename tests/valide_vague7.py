"""
VAGUE 7 — graphes dirigés / DP / géométrie point / combinatoire (2026-06-19, autonomie). Lacunes MESURÉES par
gap_probe_vague7 (9 vrais HORS, dont min_path_sum « résolu » par COÏNCIDENCE via matrice-reduce -> HORS à froid sur
held-out durci -> ancré en 1ʳᵉ classe). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GRAPHES DIRIGÉS : is_dag + degree_sequence via `graphe-connexite`.
  2. DP : knapsack01 + max_product_subarray + min_path_sum via `tableaux`.
  3. GÉO + COMBINATOIRE : point_in_rectangle/point_in_circle via `geometrie` ; unique_paths/pascal_row via `comptage-combinatoire`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; house_robber reste via `tableaux`, manhattan via `geometrie`.

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

        dg = ia.demande("is_dag", "n, edges", [((3, [(0, 1), (1, 2)]), True), ((3, [(0, 1), (1, 2), (2, 0)]), False)],
                        [((2, [(0, 1), (1, 0)]), False), ((4, [(0, 1), (0, 2), (1, 3), (2, 3)]), True), ((1, []), True)])
        ds = ia.demande("degree_sequence", "n, edges", [((3, [(0, 1), (1, 2)]), [2, 1, 1]), ((2, [(0, 1)]), [1, 1])],
                        [((4, [(0, 1), (0, 2), (0, 3)]), [3, 1, 1, 1]), ((2, []), [0, 0])])
        r.append(_check(f"GRAPHES is_dag->`{dg.etage}` degree_seq->`{ds.etage}`",
                        resolu(dg)
                        and resolu(ds)))

        kn = ia.demande("knapsack01", "weights, values, cap", [(([1, 2, 3], [6, 10, 12], 5), 22), (([2], [3], 1), 0)],
                        [(([1, 2, 3], [10, 15, 40], 6), 65), (([1, 1], [1, 1], 1), 1), (([3], [9], 3), 9)])
        mp = ia.demande("max_product_subarray", "xs", [(([2, 3, -2, 4],), 6), (([-2, 0, -1],), 0)],
                        [(([-2, 3, -4],), 24), (([-2],), -2), (([0, 2],), 2)])
        ps = ia.demande("min_path_sum", "grid", [(([[1, 3, 1], [1, 5, 1], [4, 2, 1]],), 7), (([[1, 2], [1, 1]],), 3)],
                        [(([[1, 2, 3], [4, 5, 6]],), 12), (([[5]],), 5), (([[9, 1, 1], [1, 1, 9], [9, 1, 1]],), 13)])
        r.append(_check(f"DP knapsack->`{kn.etage}` maxprod->`{mp.etage}` minpath->`{ps.etage}` (==tableaux)",
                        all(resolu(x) for x in (kn, mp, ps))))

        pr = ia.demande("point_in_rectangle", "px, py, x1, y1, x2, y2",
                        [((1, 1, 0, 0, 2, 2), True), ((3, 1, 0, 0, 2, 2), False)],
                        [((0, 0, 0, 0, 2, 2), True), ((2, 2, 0, 0, 2, 2), True), ((-1, 1, 0, 0, 2, 2), False)])
        pc = ia.demande("point_in_circle", "px, py, cx, cy, r", [((1, 1, 0, 0, 2), True), ((3, 0, 0, 0, 2), False)],
                        [((2, 0, 0, 0, 2), True), ((0, 0, 0, 0, 0), True), ((2, 2, 0, 0, 2), False)])
        up = ia.demande("unique_paths", "m, n", [((3, 3), 6), ((2, 2), 2)], [((1, 5), 1), ((3, 2), 3), ((3, 7), 28)])
        pa = ia.demande("pascal_row", "n", [((0,), [1]), ((3,), [1, 3, 3, 1])], [((1,), [1, 1]), ((4,), [1, 4, 6, 4, 1])])
        r.append(_check(f"GÉO rect->`{pr.etage}` circ->`{pc.etage}` (==geometrie) | "
                        f"unique_paths->`{up.etage}` pascal->`{pa.etage}` (==comptage-combinatoire)",
                        resolu(pr)
                        and resolu(pc)
                        and resolu(up)
                        and resolu(pa)))

        inc = ia.demande("incoherent_v7", "n, edges", [((2, [(0, 1)]), 42)], [((3, []), 99)])
        hr = ia.demande("house_robber", "xs", [(([2, 7, 9, 3, 1],), 12), (([1, 2, 3, 1],), 4)],
                        [(([],), 0), (([5],), 5), (([2, 1, 1, 2],), 4), (([5, 5, 10, 100, 10, 5],), 110),
                         (([4, 1, 1, 4, 2, 1],), 9)])  # held-out DURCI : force le vrai DP (tableaux), bloque la coïncidence positionnel
        mh = ia.demande("manhattan", "x1, y1, x2, y2", [((0, 0, 3, 4), 7), ((1, 1, 1, 1), 0)], [((-1, -1, 2, 3), 7)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG house_robber->`{hr.etage}` manhattan->`{mh.etage}`",
                        not inc.ok and resolu(hr) and resolu(mh)))

    print()
    print("VAGUE 7 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
