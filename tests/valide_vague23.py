"""
VAGUE 23 — chaînes arithmétiques / pile / nombres / tableau (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par
gap_probe_vague23 (6 vrais trous). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. CHAÎNES ARITH : add_strings + add_binary via `chaines-avancees`.
  2. CHAÎNE/PILE : repeated_substring_pattern via `chaines-avancees` ; backspace_compare via `pile`.
  3. NOMBRES/TABLEAU : power_of_three via `diviseurs` ; find_disappeared_numbers via `tableaux`.
  4. HORS + NON-RÉG : incohérent -> HORS ; ransom_note via `chaines-avancees`.

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

        ad = ia.demande("add_strings", "a, b", [(("11", "123"), "134"), (("0", "0"), "0")],
                        [(("99", "1"), "100"), (("456", "77"), "533"), (("1", "9"), "10")])
        ab = ia.demande("add_binary", "a, b", [(("11", "1"), "100"), (("1010", "1011"), "10101")],
                        [(("0", "0"), "0"), (("1", "1"), "10"), (("110", "11"), "1001")])
        r.append(_check(f"CHAÎNES ARITH add_strings->`{ad.etage}` add_binary->`{ab.etage}` (==chaines-avancees)",
                        resolu(ad) and resolu(ab)))

        rp = ia.demande("repeated_substring_pattern", "s", [(("abab",), True), (("aba",), False)],
                        [(("abcabcabc",), True), (("a",), False), (("aaaa",), True), (("abcab",), False)])
        bs = ia.demande("backspace_compare", "s, t", [(("ab#c", "ad#c"), True), (("a#c", "b"), False)],
                        [(("ab##", "c#d#"), True), (("a##c", "#a#c"), True), (("xy#z", "xz"), True)])
        r.append(_check(f"CHAÎNE/PILE rsp->`{rp.etage}`(==chaines) backspace->`{bs.etage}`(==pile)",
                        resolu(rp) and resolu(bs)))

        p3 = ia.demande("power_of_three", "n", [((27,), True), ((45,), False)],
                        [((1,), True), ((0,), False), ((9,), True), ((243,), True), ((6,), False)])
        fd = ia.demande("find_disappeared_numbers", "nums", [(([4, 3, 2, 7, 8, 2, 3, 1],), [5, 6]), (([1, 1],), [2])],
                        [(([2, 2],), [1]), (([1, 2, 3],), []), (([1],), [])])
        r.append(_check(f"NOMBRES/TAB power3->`{p3.etage}`(==diviseurs) disappeared->`{fd.etage}`(==tableaux)",
                        resolu(p3) and resolu(fd)))

        inc = ia.demande("incoherent_v23", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        rn = ia.demande("ransom_note", "note, magazine", [(("a", "b"), False), (("aa", "aab"), True)],
                        [(("", "abc"), True), (("abc", "cba"), True), (("aabb", "ab"), False)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG ransom->`{rn.etage}`(==chaines-avancees)",
                        not inc.ok and resolu(rn)))

    print()
    print("VAGUE 23 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
