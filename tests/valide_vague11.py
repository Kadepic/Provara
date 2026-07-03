"""
VAGUE 11 — Bellman-Ford / spirale / 3D / jokers / DP / zigzag / max-xor / chiffres (2026-06-19, autonomie).
Lacunes MESURÉES par gap_probe_vague11 (10 vrais HORS, held-out durcis d'emblée -> 0 coïncidence). Validées dans
le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GRAPHE/MATRICE/3D : bellman_ford via `graphe-connexite` ; spiral_order via `tableaux` ; dot3d via `numerique`.
  2. AUTOMATE/ENCODAGE/CHIFFRES : match_wildcard via `chaines-avancees` ; zigzag_encode via `conversion` ;
     digit_factorial_sum via `chiffres`.
  3. DP/BITS : subarray_sum_count + product_except_self + trapping_rain_water via `tableaux` ; max_xor_pair via `bits`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; matmul via `matrice`, knapsack01 via `tableaux`.

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

        bf = ia.demande("bellman_ford", "n, edges, src, dst", [((3, [(0, 1, 4), (0, 2, 1), (2, 1, 2)], 0, 1), 3)],
                        [((3, [(0, 1, 5), (1, 2, -3)], 0, 2), 2), ((4, [(0, 1, 1)], 0, 3), -1), ((1, [], 0, 0), 0)])
        sp = ia.demande("spiral_order", "m", [(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [1, 2, 3, 6, 9, 8, 7, 4, 5])],
                        [(([[1, 2], [3, 4]],), [1, 2, 4, 3]), (([[1]],), [1]), (([[1, 2, 3]],), [1, 2, 3])])
        dt = ia.demande("dot3d", "a, b", [(([1, 2, 3], [4, 5, 6]), 32), (([0, 0, 0], [1, 1, 1]), 0)],
                        [(([1, 0, 0], [0, 1, 0]), 0), (([2, 2, 2], [1, 1, 1]), 6)])
        r.append(_check(f"bellman->`{bf.etage}`(==graphe-connexite) spiral->`{sp.etage}`(==tableaux) dot3d->`{dt.etage}`(==numerique)",
                        resolu(bf) and resolu(sp) and resolu(dt)))

        mw = ia.demande("match_wildcard", "s, p", [(("aa", "a"), False), (("aa", "*"), True)],
                        [(("cb", "?b"), True), (("adceb", "*a*b"), True), (("acdcb", "a*c?b"), False), (("", "*"), True)])
        zz = ia.demande("zigzag_encode", "n", [((0,), 0), ((-1,), 1)], [((1,), 2), ((-2,), 3), ((2,), 4), ((-3,), 5)])
        df = ia.demande("digit_factorial_sum", "n", [((145,), 145), ((1,), 1)], [((0,), 1), ((2,), 2), ((10,), 2), ((40585,), 40585)])
        r.append(_check(f"wildcard->`{mw.etage}`(==chaines) zigzag->`{zz.etage}`(==conversion) digfact->`{df.etage}`(==chiffres)",
                        resolu(mw) and resolu(zz) and resolu(df)))

        sc = ia.demande("subarray_sum_count", "xs, k", [(([1, 1, 1], 2), 2), (([1, 2, 3], 3), 2)],
                        [(([1, -1, 0], 0), 3), (([3], 3), 1), (([], 0), 0)])
        ps = ia.demande("product_except_self", "xs", [(([1, 2, 3, 4],), [24, 12, 8, 6])],
                        [(([2, 3],), [3, 2]), (([5],), [1]), (([1, 0, 2],), [0, 2, 0])])
        tr = ia.demande("trapping_rain_water", "h", [(([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), 6)],
                        [(([4, 2, 0, 3, 2, 5],), 9), (([1, 2, 3],), 0), (([3, 0, 2],), 2)])
        mx = ia.demande("max_xor_pair", "xs", [(([3, 10, 5, 25, 2, 8],), 28)], [(([1, 2],), 3), (([0, 0],), 0), (([8, 1, 2, 12, 7, 6],), 15)])
        r.append(_check(f"DP sub->`{sc.etage}` prod->`{ps.etage}` rain->`{tr.etage}` (==tableaux) | maxxor->`{mx.etage}`(==bits)",
                        all(resolu(x) for x in (sc, ps, tr)) and resolu(mx)))

        inc = ia.demande("incoherent_v11", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        mm = ia.demande("matmul", "a, b", [(([[1, 2], [3, 4]], [[5, 6], [7, 8]]), [[19, 22], [43, 50]])],
                        [(([[1, 0], [0, 1]], [[5, 6], [7, 8]]), [[5, 6], [7, 8]])])
        kn = ia.demande("knapsack01", "weights, values, cap", [(([1, 2, 3], [6, 10, 12], 5), 22), (([2], [3], 1), 0)],
                        [(([1, 2, 3], [10, 15, 40], 6), 65)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG matmul->`{mm.etage}` knapsack->`{kn.etage}`",
                        not inc.ok and resolu(mm) and resolu(kn)))

    print()
    print("VAGUE 11 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
