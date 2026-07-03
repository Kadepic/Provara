"""
VAGUE 13 — DP (word break, profit, décodages) / combinatoire (Bell, Stirling) / déterminant entier / Möbius / Σφ /
puissance de 2 / triangles (2026-06-19, autonomie de nuit). Lacunes MESURÉES par gap_probe_vague13 (11 vrais HORS,
held-out DURCIS d'emblée). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. DP : word_break via `chaines-avancees` ; max_profit + max_profit_multi + decode_ways via `tableaux`.
  2. COMBINATOIRE/ALGÈBRE : bell_number + stirling_second via `comptage-combinatoire` ; determinant_int via `numerique`.
  3. NOMBRES/BITS/GRAPHE : mobius + euler_phi_sum via `diviseurs` ; next_power_of_two via `bits` ;
     count_triangles via `graphe-connexite`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; edit_distance reste via `dp2d`, pascal_row via `comptage-combinatoire`.

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

        wb = ia.demande("word_break", "s, words", [(("leetcode", ["leet", "code"]), True), (("ab", ["a"]), False)],
                        [(("applepenapple", ["apple", "pen"]), True),
                         (("catsandog", ["cats", "dog", "sand", "and", "cat"]), False), (("a", ["a"]), True)])
        mp = ia.demande("max_profit", "prices", [(([7, 1, 5, 3, 6, 4],), 5), (([7, 6, 4, 3, 1],), 0)],
                        [(([1, 2],), 1), (([2, 4, 1],), 2), (([5],), 0)])
        mm = ia.demande("max_profit_multi", "prices", [(([7, 1, 5, 3, 6, 4],), 7), (([1, 2, 3, 4, 5],), 4)],
                        [(([7, 6, 4, 3, 1],), 0), (([1, 5, 2, 8],), 10), (([3],), 0)])
        dw = ia.demande("decode_ways", "s", [(("12",), 2), (("226",), 3)],
                        [(("0",), 0), (("10",), 1), (("27",), 1), (("100",), 0), (("11",), 2)])
        r.append(_check(f"DP wb->`{wb.etage}`(==chaines) mp->`{mp.etage}` mpm->`{mm.etage}` dw->`{dw.etage}` (==tableaux)",
                        resolu(wb) and all(resolu(x) for x in (mp, mm, dw))))

        bl = ia.demande("bell_number", "n", [((3,), 5), ((0,), 1)], [((1,), 1), ((2,), 2), ((4,), 15), ((5,), 52)])
        st = ia.demande("stirling_second", "n, k", [((3, 2), 3), ((4, 2), 7)],
                        [((5, 3), 25), ((3, 3), 1), ((4, 1), 1), ((0, 0), 1)])
        dt = ia.demande("determinant_int", "m", [(([[1, 2], [3, 4]],), -2), (([[2, 0], [0, 3]],), 6)],
                        [(([[1, 2, 3], [4, 5, 6], [7, 8, 10]],), -3), (([[5]],), 5),
                         (([[1, 0, 0], [0, 1, 0], [0, 0, 1]],), 1)])
        r.append(_check(f"COMB bell->`{bl.etage}` stir->`{st.etage}` (==comptage-combinatoire) | det->`{dt.etage}`(==numerique)",
                        resolu(bl) and resolu(st) and resolu(dt)))

        mo = ia.demande("mobius", "n", [((1,), 1), ((6,), 1)], [((2,), -1), ((4,), 0), ((12,), 0), ((30,), -1), ((5,), -1)])
        ep = ia.demande("euler_phi_sum", "n", [((3,), 4), ((1,), 1)], [((2,), 2), ((5,), 10), ((6,), 12)])
        np = ia.demande("next_power_of_two", "n", [((5,), 8), ((16,), 16)], [((17,), 32), ((1,), 1), ((6,), 8), ((1000,), 1024)])
        ct = ia.demande("count_triangles", "n, edges", [((3, [(0, 1), (1, 2), (2, 0)]), 1), ((4, [(0, 1), (1, 2), (2, 3)]), 0)],
                        [((4, [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3)]), 2),
                         ((4, [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]), 4)])
        r.append(_check(f"NOMBRES mob->`{mo.etage}` phi->`{ep.etage}`(==diviseurs) npot->`{np.etage}`(==bits) tri->`{ct.etage}`(==graphe-connexite)",
                        resolu(mo) and resolu(ep) and resolu(np) and resolu(ct)))

        inc = ia.demande("incoherent_v13", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        ed = ia.demande("edit_distance", "a, b", [(("kitten", "sitting"), 3), (("abc", "abc"), 0)],
                        [(("", "abc"), 3), (("ab", "ba"), 2), (("horse", "ros"), 3)])
        pa = ia.demande("pascal_row", "n", [((4,), [1, 4, 6, 4, 1]), ((0,), [1])], [((1,), [1, 1]), ((3,), [1, 3, 3, 1])])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG edit->`{ed.etage}` pascal->`{pa.etage}`",
                        not inc.ok and resolu(ed) and resolu(pa)))

    print()
    print("VAGUE 13 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
