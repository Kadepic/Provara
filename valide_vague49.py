"""
VAGUE 49 — CHAÎNES AVANCÉES + MATHS MODULAIRES (2026-06-22 nuit, autonomie). gap_probe_vague49 = 8 tâches :
3 VRAIS TROUS bâtis + 5 confirmées.

Bâtis cette vague (-> `GenerateurChainesAvancees`) :
  • `group_anagrams_count`      — nombre de groupes d'anagrammes (clé = lettres triées).
  • `count_distinct_substrings` — nombre de sous-chaînes distinctes (ensemble des tranches).
  • `min_window_length`         — longueur de la plus petite fenêtre couvrante (fenêtre glissante à manques).
  Vérifiés sur cas adverses avant câblage. Confirmées : longest_common_prefix (`prefixe-commun`), pow_mod/lcm
  (`math-avance`), roman_to_int/int_to_roman (`conversion`).

Critères de MORT (4) :
  1. CHAÎNES NOUVELLES (épinglé `chaines-avancees`) : group_anagrams_count + count_distinct_substrings + min_window_length.
  2. CONVERSIONS (épinglé `conversion`) : roman_to_int + int_to_roman.
  3. MATHS/PRÉFIXE : pow_mod + lcm + longest_common_prefix (ok+generalise).
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

        # ---- 1. CHAÎNES NOUVELLES (épinglé chaines-avancees) -----------------------------------------------
        ga = ia.demande("group_anagrams_count", "strs",
                        [((["eat", "tea", "tan", "ate", "nat", "bat"],), 3), ((["abc", "bca", "xyz"],), 2)],
                        [((["a"],), 1), (([""],), 1), ((["ab", "ba", "abc"],), 2), ((["abc", "cba", "bac", "xy"],), 2)])
        cd = ia.demande("count_distinct_substrings", "s",
                        [(("abc",), 6), (("aaa",), 3)],
                        [(("a",), 1), (("",), 0), (("abab",), 7), (("abcabc",), 15)])
        mw = ia.demande("min_window_length", "s, t",
                        [(("ADOBECODEBANC", "ABC"), 4), (("a", "a"), 1)],
                        [(("a", "aa"), 0), (("xyz", "xz"), 3), (("aa", "aa"), 2),
                         (("abcdef", "abcdef"), 6), (("aaflslflsldkalskaaa", "aaa"), 3)])
        r.append(_check(f"CHAÎNES group_anagrams->`{ga.etage}` count_distinct->`{cd.etage}` min_window->`{mw.etage}` (==chaines-avancees)",
                        all(resolu(x) for x in (ga, cd, mw))))

        # ---- 2. CONVERSIONS (épinglé conversion) ----------------------------------------------------------
        ri = ia.demande("roman_to_int", "s", [(("III",), 3), (("MCMXCIV",), 1994)],
                        [(("IV",), 4), (("IX",), 9), (("LVIII",), 58), (("XLII",), 42)])
        ir = ia.demande("int_to_roman", "n", [((3,), "III"), ((1994,), "MCMXCIV")],
                        [((4,), "IV"), ((9,), "IX"), ((58,), "LVIII"), ((42,), "XLII")])
        r.append(_check(f"CONVERSIONS roman_to_int->`{ri.etage}` int_to_roman->`{ir.etage}` (==conversion)",
                        all(resolu(x) for x in (ri, ir))))

        # ---- 3. MATHS / PRÉFIXE (ok+generalise) -----------------------------------------------------------
        pm = ia.demande("pow_mod", "base, exp, mod", [((2, 10, 1000), 24), ((3, 5, 7), 5)],
                        [((2, 0, 5), 1), ((10, 3, 6), 4), ((7, 256, 13), 9), ((5, 117, 19), 1)])
        lc = ia.demande("lcm", "a, b", [((4, 6), 12), ((3, 5), 15)],
                        [((1, 1), 1), ((12, 8), 24), ((7, 1), 7), ((6, 9), 18)])
        lp = ia.demande("longest_common_prefix", "strs",
                        [((["flower", "flow", "flight"],), "fl"), ((["dog", "racecar", "car"],), "")],
                        [((["abc"],), "abc"), ((["a", "a"],), "a"), ((["", ""],), ""), ((["abcd", "abce"],), "abc")])
        r.append(_check(f"MATHS/PRÉFIXE pow_mod->`{pm.etage}` lcm->`{lc.etage}` lcp->`{lp.etage}`",
                        all(x.ok and x.generalise for x in (pm, lc, lp))))

        # ---- 4. HORS HONNÊTE ------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v49", "s", [(("a",), 42)], [(("b",), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 49 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
