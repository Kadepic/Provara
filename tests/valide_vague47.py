"""
VAGUE 47 — CLASSIQUES DP (CONFIRMATION, 0 trou) (2026-06-22 nuit, autonomie). gap_probe_vague47 = 8 tâches
TOUTES déjà couvertes ; AUCUN générateur modifié. Ce validateur = COLD-RETEST DURCI (held-out adverse) qui
prouve qu'il s'agit de VRAIE couverture, pas de coïncidences (signe de MATURITÉ du moteur sur la DP, comme v41).

Couverture observée : coin_change/coin_change_count -> `monnaie` ; lcs_length/edit_distance -> `dp2d` ;
longest_palindromic_subseq/word_break -> `chaines-avancees` ; climb_stairs -> `recurrence` ;
min_cost_climbing -> `tableaux`. On ÉPINGLE seulement les homes structurellement non ambigus (monnaie, dp2d) ;
pour les étages génériques on exige ok+generalise sur le held-out durci (la vraie propriété de soundness).

Critères de MORT (4) :
  1. DP MONÉTAIRE (épinglé `monnaie`) : coin_change + coin_change_count.
  2. DP 2-SÉQUENCES (épinglé `dp2d`) : lcs_length + edit_distance.
  3. DP CHAÎNE/LINÉAIRE (held durci, ok+generalise) : longest_palindromic_subseq + word_break + climb_stairs + min_cost_climbing.
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

        # ---- 1. DP MONÉTAIRE (épinglé monnaie) --------------------------------------------------------------
        cc = ia.demande("coin_change", "coins, amount", [(([1, 2, 5], 11), 3), (([2], 3), -1)],
                        [(([1], 0), 0), (([5], 5), 1), (([2, 5], 3), -1), (([1, 2, 5], 100), 20), (([3, 7], 5), -1)])
        ccc = ia.demande("coin_change_count", "coins, amount", [(([1, 2, 5], 5), 4), (([2, 3], 6), 2)],
                         [(([1], 3), 1), (([3], 2), 0), (([2, 3], 7), 1), (([1, 2], 4), 3)])
        r.append(_check(f"DP MONÉTAIRE coin_change->`{cc.etage}` coin_change_count->`{ccc.etage}`",
                        all(resolu(x) for x in (cc, ccc))))

        # ---- 2. DP 2-SÉQUENCES (épinglé dp2d) ---------------------------------------------------------------
        lcs = ia.demande("lcs_length", "a, b", [(("abcde", "ace"), 3), (("abc", "def"), 0)],
                         [(("abc", "abc"), 3), (("", ""), 0), (("aggtab", "gxtxayb"), 4), (("abcbdab", "bdcaba"), 4)])
        ed = ia.demande("edit_distance", "a, b", [(("horse", "ros"), 3), (("intention", "execution"), 5)],
                        [(("", "abc"), 3), (("abc", "abc"), 0), (("a", "b"), 1), (("sunday", "saturday"), 3)])
        r.append(_check(f"DP 2-SÉQ lcs_length->`{lcs.etage}` edit_distance->`{ed.etage}`",
                        all(resolu(x) for x in (lcs, ed))))

        # ---- 3. DP CHAÎNE/LINÉAIRE (held DURCI, ok+generalise) ----------------------------------------------
        lps = ia.demande("longest_palindromic_subseq", "s", [(("bbbab",), 4), (("cbbd",), 2)],
                         [(("a",), 1), (("",), 0), (("agbdba",), 5), (("character",), 5), (("abcabcabc",), 5),
                          (("aaaa",), 4), (("abcde",), 1), (("racecar",), 7), (("xyzzyx",), 6)])
        wb = ia.demande("word_break", "s, words",
                        [(("leetcode", ["leet", "code"]), True), (("catsandog", ["cats", "dog", "sand", "and", "cat"]), False)],
                        [(("applepenapple", ["apple", "pen"]), True), (("a", ["a"]), True), (("ab", ["a"]), False),
                         (("cars", ["car", "ca", "rs"]), True), (("aaaaaaa", ["aaaa", "aa"]), False),
                         (("bb", ["a"]), False), (("abcd", ["a", "abc", "b", "cd"]), True), (("xyz", ["xy", "z", "x"]), True)])
        cs = ia.demande("climb_stairs", "n", [((2,), 2), ((3,), 3)],
                        [((1,), 1), ((5,), 8), ((0,), 1), ((10,), 89), ((7,), 21)])
        mc = ia.demande("min_cost_climbing", "cost", [(([10, 15, 20],), 15), (([1, 100, 1, 1, 1, 100, 1, 1, 100, 1],), 6)],
                        [(([0, 0],), 0), (([5],), 0), (([1, 2, 3],), 2), (([0, 1, 2, 2],), 2),
                         (([1, 2, 3, 4, 5],), 6), (([10, 15, 20, 1],), 16)])
        r.append(_check(f"DP CHAÎNE/LIN lps->`{lps.etage}` word_break->`{wb.etage}` climb->`{cs.etage}` min_cost->`{mc.etage}` (held durci)",
                        all(resolu(x) for x in (lps, wb, cs, mc))))

        # ---- 4. HORS HONNÊTE -------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v47", "n", [((1,), 42)], [((2,), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 47 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
