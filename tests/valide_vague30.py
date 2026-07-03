"""
VAGUE 30 — tableaux / chiffres / DP-2D / chaînes (2026-06-20, nuit, 1.5 Go). gap_probe_vague30 = 8 tâches : 4 vrais
trous bâtis (single_number_iii + min_moves via `tableaux` ; fizzbuzz via `chiffres` ; find_the_difference via
`chaines-avancees`, XOR) + 4 DÉJÀ couvertes réelles (reverse_integer->chiffres, longest_common_subsequence &
edit_distance->dp2d, sort_colors). find_the_difference exige un held-out DUR (sinon coïncidence `invention`).

Critères de MORT (4) :
  1. TABLEAUX : single_number_iii + min_moves via `tableaux`.
  2. CHIFFRES : reverse_integer + fizzbuzz via `chiffres`.
  3. DP2D/CHAÎNE : longest_common_subsequence + edit_distance via `dp2d` ; find_the_difference via `chaines-avancees`.
  4. NON-RÉG + HORS : sort_colors généralise ; incohérent -> HORS.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from valide_commun import resolu

_FB15 = ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        sn = ia.demande("single_number_iii", "nums", [(([1, 2, 1, 3, 2, 5],), [3, 5]), (([0, 1],), [0, 1])],
                        [(([1, 2, 2, 3, 3, 4],), [1, 4]), (([5, 5, 7, 9],), [7, 9]), (([-1, 0],), [-1, 0]),
                         (([8, 8, 1, 1, 2, 3],), [2, 3])])
        mm = ia.demande("min_moves", "nums", [(([1, 2, 3],), 3), (([1, 1, 1],), 0)],
                        [(([1, 2, 3, 4],), 6), (([5],), 0), (([0, 0, 1],), 1), (([1, 10],), 9)])
        r.append(_check(f"TABLEAUX single_number_iii->`{sn.etage}` min_moves->`{mm.etage}` (résolu, étage libre)",
                        all(resolu(x) for x in (sn, mm))))

        ri = ia.demande("reverse_integer", "x", [((123,), 321), ((-123,), -321)],
                        [((120,), 21), ((-100,), -1), ((0,), 0), ((7,), 7), ((-90,), -9)])
        fb = ia.demande("fizzbuzz", "n", [((3,), ["1", "2", "Fizz"]), ((5,), ["1", "2", "Fizz", "4", "Buzz"])],
                        [((1,), ["1"]), ((2,), ["1", "2"]), ((15,), _FB15)])
        r.append(_check(f"CHIFFRES reverse_integer->`{ri.etage}` fizzbuzz->`{fb.etage}` (résolu, étage libre)",
                        all(resolu(x) for x in (ri, fb))))

        lc = ia.demande("longest_common_subsequence", "text1, text2", [(("abcde", "ace"), 3), (("abc", "abc"), 3)],
                        [(("abc", "def"), 0), (("a", "a"), 1), (("abcba", "abcbcba"), 5), (("ace", "abcde"), 3)])
        ed = ia.demande("edit_distance", "word1, word2", [(("horse", "ros"), 3), (("intention", "execution"), 5)],
                        [(("", "abc"), 3), (("a", "b"), 1), (("kitten", "sitting"), 3), (("abc", "abc"), 0)])
        fdiff = ia.demande("find_the_difference", "s, t", [(("abcd", "abcde"), "e"), (("", "y"), "y")],
                           [(("abc", "cbad"), "d"), (("xy", "yxz"), "z"), (("aabb", "aabbc"), "c"),
                            (("z", "az"), "a"), (("hello", "ohlleg"), "g")])  # held-out DUR : force le XOR (chaines), bloque invention
        r.append(_check(f"DP2D/CHAÎNE lcs->`{lc.etage}` edit->`{ed.etage}` | find_diff->`{fdiff.etage}` (résolu, étage libre)",
                        resolu(lc) and resolu(ed) and resolu(fdiff)))

        sc = ia.demande("sort_colors", "nums", [(([2, 0, 2, 1, 1, 0],), [0, 0, 1, 1, 2, 2]), (([2, 0, 1],), [0, 1, 2])],
                        [(([0],), [0]), (([2, 2, 0, 0],), [0, 0, 2, 2]), (([1, 2, 0],), [0, 1, 2])])
        inc = ia.demande("incoherent_v30", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"NON-RÉG sort_colors->`{sc.etage}`(gen={sc.generalise}) | HORS ok={inc.ok}",
                        resolu(sc) and not inc.ok))

    print()
    print("VAGUE 30 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
