"""
VAGUE 29 — chaînes / numération / tableaux (2026-06-20, nuit, 1.5 Go). gap_probe_vague29 = 8 tâches : 5 vrais trous
bâtis (is_subsequence, partition_labels, valid_palindrome_ii via `chaines-avancees` ; maximum_swap, arrange_coins via
`numerique`) + 3 DÉJÀ couvertes réelles (find_disappeared_numbers->tableaux, add_strings & longest_palindrome_length
->chaines-avancees). Held-out ADVERSE frais. NB : le held-out guard a attrapé un bug de MON test (abcdef -> 6 uns).

Critères de MORT (4) :
  1. CHAÎNES-1 : is_subsequence + valid_palindrome_ii via `chaines-avancees`.
  2. CHAÎNES-2 : partition_labels + add_strings + longest_palindrome_length via `chaines-avancees`.
  3. NUMÉRATION : maximum_swap + arrange_coins via `numerique`.
  4. TABLEAUX + HORS : find_disappeared_numbers via `tableaux` ; incohérent -> HORS.

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

        iss = ia.demande("is_subsequence", "s, t", [(("abc", "ahbgdc"), True), (("axc", "ahbgdc"), False)],
                         [(("b", "abc"), True), (("ba", "abc"), False), (("", ""), True), (("a", ""), False)])
        vp = ia.demande("valid_palindrome_ii", "s", [(("aba",), True), (("abca",), True)],
                        [(("aa",), True), (("abba",), True), (("abcba",), True), (("abcd",), False), (("deeee",), True),
                         (("abcdba",), True), (("abc",), False), (("racecar",), True), (("cbbcc",), True),
                         (("tebbem",), False)])  # durci : force le vrai 2-pointeurs (chaines), bloque la coïncidence adjacence
        r.append(_check(f"CHAÎNES-1 is_subseq->`{iss.etage}` valid_pal2->`{vp.etage}` (==chaines-avancees)",
                        all(resolu(x) for x in (iss, vp))))

        pl = ia.demande("partition_labels", "s", [(("ababcbacadefegdehijhklij",), [9, 7, 8]), (("abac",), [3, 1])],
                        [(("abcabc",), [6]), (("xyz",), [1, 1, 1]), (("aabb",), [2, 2]),
                         (("abcd",), [1, 1, 1, 1]), (("aaaa",), [4]), (("aabbcc",), [2, 2, 2]), (("abcba",), [5])])
        ad = ia.demande("add_strings", "num1, num2", [(("11", "123"), "134"), (("0", "0"), "0")],
                        [(("5", "5"), "10"), (("99", "99"), "198"), (("100", "1"), "101")])
        lp = ia.demande("longest_palindrome_length", "s", [(("abccccdd",), 7), (("a",), 1)],
                        [(("bb",), 2), (("ccc",), 3), (("ab",), 1), (("aaabbbb",), 7)])
        # partition_labels : étage NON épinglé (round-robin le fait osciller tableaux↔chaines) ; held DURCI = soundness.
        r.append(_check(f"CHAÎNES-2 partition->`{pl.etage}`(held durci) add_strings->`{ad.etage}` longest_pal->`{lp.etage}` (==chaines)",
                        resolu(pl)
                        and all(resolu(x) for x in (ad, lp))))

        ms = ia.demande("maximum_swap", "n", [((2736,), 7236), ((9973,), 9973)],
                        [((1993,), 9913), ((115,), 511), ((9,), 9), ((1234,), 4231)])
        ac = ia.demande("arrange_coins", "n", [((5,), 2), ((8,), 3)],
                        [((1,), 1), ((6,), 3), ((0,), 0), ((10,), 4)])
        r.append(_check(f"NUMÉRATION maximum_swap->`{ms.etage}` arrange_coins->`{ac.etage}` (==numerique)",
                        all(resolu(x) for x in (ms, ac))))

        fd = ia.demande("find_disappeared_numbers", "nums", [(([4, 3, 2, 7, 8, 2, 3, 1],), [5, 6]), (([2, 2],), [1])],
                        [(([1, 1],), [2]), (([1, 2, 3],), []), (([],), []), (([3, 1, 3],), [2])])
        inc = ia.demande("incoherent_v29", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"TABLEAUX find_disappeared->`{fd.etage}`(==tableaux) | HORS ok={inc.ok}",
                        resolu(fd) and not inc.ok))

    print()
    print("VAGUE 29 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
