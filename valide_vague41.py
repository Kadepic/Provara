"""
VAGUE 41 — CONFIRMATION (2026-06-20, reprise post-redémarrage, 1.5 Go). Vague EXOTIQUE sondée : 8/8 RÉSOLUES par des
étages DÉJÀ existants, AUCUN trou à bâtir. Cette validation est donc un COLD-RETEST DURCI (norme anti-coïncidence :
« résolu via étage générique = suspect → re-tester à froid avec held-out adverse durci ») DOUBLÉ d'un verrou de
non-régression. Held-out durcis pré-vérifiés (1 bug de test attrapé : backspace_compare('a#b#c#','#')=True).

Discriminations durcies : is_power_of_four exige puissance-de-4 (pas seulement de 2 : 2/8/32/128/512 -> False) ;
is_isomorphic exige la BIJECTION (injectivité des deux côtés) ; repeated_substring_pattern/rotate_string sur périodes.

Critères de MORT (4) :
  1. BINAIRE : add_binary via `chaines-avancees` ; hamming_distance + is_power_of_four via `bits`.
  2. BASE/BIJECTION : excel_column_number via `numerique` ; is_isomorphic via `chaines-avancees`.
  3. PILE/PÉRIODE : backspace_compare via `pile` ; rotate_string + repeated_substring_pattern via `chaines-avancees`.
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

        # ---- 1. BINAIRE ----------------------------------------------------------------------------------------
        ab = ia.demande("add_binary", "a, b", [(("11", "1"), "100"), (("1010", "1011"), "10101")],
                        [(("101", "11"), "1000"), (("1111", "1"), "10000"), (("0", "101"), "101")])
        hd = ia.demande("hamming_distance", "x, y", [((1, 4), 2), ((3, 1), 1)],
                        [((4, 1), 2), ((1, 1), 0), ((14, 9), 3), ((1024, 0), 1)])
        p4 = ia.demande("is_power_of_four", "n", [((16,), True), ((5,), False)],
                        [((2,), False), ((8,), False), ((32,), False), ((128,), False), ((512,), False),
                         ((4,), True), ((64,), True), ((256,), True), ((1024,), True), ((3,), False), ((0,), False)])
        r.append(_check(f"BINAIRE add_binary->`{ab.etage}`(==chaines-avancees) hamming->`{hd.etage}` pow4->`{p4.etage}`(==bits)",
                        resolu(ab) and resolu(hd) and resolu(p4)))

        # ---- 2. BASE / BIJECTION -------------------------------------------------------------------------------
        ec = ia.demande("excel_column_number", "s", [(("A",), 1), (("AB",), 28)],
                        [(("BA",), 53), (("AAA",), 703), (("XFD",), 16384), (("ZZ",), 702)])
        iso = ia.demande("is_isomorphic", "s, t", [(("egg", "add"), True), (("foo", "bar"), False)],
                         [(("abba", "cddc"), True), (("abba", "cddd"), False), (("abc", "ddd"), False),
                          (("aab", "xxy"), True), (("aba", "baba"), False)])
        r.append(_check(f"BASE/BIJ excel->`{ec.etage}`(==numerique) isomorphic->`{iso.etage}`(==chaines-avancees)",
                        resolu(ec) and resolu(iso)))

        # ---- 3. PILE / PÉRIODE ---------------------------------------------------------------------------------
        bc = ia.demande("backspace_compare", "s, t", [(("ab#c", "ad#c"), True), (("ab##", "c#d#"), True)],
                        [(("bxj##tw", "bxo#j##tw"), True), (("a#b#c#", "x"), False), (("xy#z", "xz"), True),
                         (("###", "#"), True)])
        rs = ia.demande("rotate_string", "s, goal", [(("abcde", "cdeab"), True), (("abcde", "abced"), False)],
                        [(("abcde", "eabcd"), True), (("abc", "cab"), True), (("abc", "acb"), False), (("aa", "aa"), True)])
        rp = ia.demande("repeated_substring_pattern", "s", [(("abab",), True), (("aba",), False)],
                        [(("abcabc",), True), (("abac",), False), (("xyxyxy",), True), (("abcab",), False), (("zz",), True)])
        r.append(_check(f"PILE/PÉRIODE backspace->`{bc.etage}`(==pile) rotate->`{rs.etage}` repeat_pat->`{rp.etage}`(==chaines-avancees)",
                        resolu(bc) and resolu(rs) and resolu(rp)))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v41", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 41 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
