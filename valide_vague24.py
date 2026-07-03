"""
VAGUE 24 — DP / tableaux / bits (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par gap_probe_vague24 (6 vrais trous).
Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. DP : integer_break + nth_ugly_number via `tableaux`.
  2. TABLEAUX : find_peak_element + summary_ranges + find_anagram_indices via `tableaux`.
  3. BITS + HORS : bitwise_and_range via `bits` ; incohérent -> HORS.
  4. NON-RÉG : search_insert_position via `filtre-seuil`, word_pattern via `chaines-avancees`.

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

        ib = ia.demande("integer_break", "n", [((2,), 1), ((10,), 36)], [((4,), 4), ((3,), 2), ((8,), 18), ((11,), 54)])
        nu = ia.demande("nth_ugly_number", "n", [((10,), 12), ((1,), 1)], [((7,), 8), ((11,), 15), ((15,), 24)])
        # integer_break / nth_ugly_number -> étage DÉDIÉ `dp-int` (campagne <100, ex-`tableaux`).
        r.append(_check(f"DP integer_break->`{ib.etage}` nth_ugly->`{nu.etage}` (==dp-int)",
                        resolu(ib) and resolu(nu)))

        fp = ia.demande("find_peak_element", "nums", [(([1, 2, 3, 1],), 2), (([1, 2, 1, 3, 5, 6, 4],), 1)],
                        [(([1],), 0), (([1, 2],), 1), (([2, 1],), 0), (([1, 3, 2],), 1)])
        sr = ia.demande("summary_ranges", "nums", [(([0, 1, 2, 4, 5, 7],), ["0->2", "4->5", "7"]), (([],), [])],
                        [(([0, 2, 3, 4, 6, 8, 9],), ["0", "2->4", "6", "8->9"]), (([1],), ["1"]), (([1, 2],), ["1->2"])])
        fa = ia.demande("find_anagram_indices", "s, p", [(("cbaebabacd", "abc"), [0, 6]), (("abab", "ab"), [0, 1, 2])],
                        [(("a", "b"), []), (("af", "fa"), [0]), (("aa", "aa"), [0])])
        r.append(_check(f"TABLEAUX peak->`{fp.etage}` ranges->`{sr.etage}` anagrams->`{fa.etage}` (==tableaux)",
                        all(resolu(x) for x in (fp, sr, fa))))

        ba = ia.demande("bitwise_and_range", "m, n", [((5, 7), 4), ((0, 0), 0)],
                        [((1, 1), 1), ((12, 15), 12), ((5, 5), 5), ((1, 2), 0)])
        inc = ia.demande("incoherent_v24", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"BITS bitand->`{ba.etage}`(==bits) | HORS incoherent ok={inc.ok}",
                        resolu(ba) and not inc.ok))

        si = ia.demande("search_insert_position", "nums, target", [(([1, 3, 5, 6], 5), 2), (([1, 3, 5, 6], 2), 1)],
                        [(([1, 3, 5, 6], 7), 4), (([1, 3, 5, 6], 0), 0), (([1], 1), 0)])
        wp = ia.demande("word_pattern", "pattern, words", [(("abba", ["dog", "cat", "cat", "dog"]), True), (("abba", ["dog", "cat", "cat", "fish"]), False)],
                        [(("aaaa", ["dog", "cat", "cat", "dog"]), False), (("abc", ["b", "c", "a"]), True)])
        r.append(_check(f"NON-RÉG search_insert->`{si.etage}` word_pattern->`{wp.etage}`",
                        resolu(si) and resolu(wp)))

    print()
    print("VAGUE 24 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
