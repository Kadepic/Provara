"""
VAGUE 21 — parsing / chiffres / chaînes / DP / greedy (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par
gap_probe_vague21 (6 vrais trous, held-out DURCIS ; 1 held-out à MOI corrigé : lemonade_change [5,5,5,5,20,20]=False).
Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. CHIFFRES : reverse_integer + is_palindrome_number via `chiffres`.
  2. CHAÎNES : is_isomorphic + string_to_int via `chaines-avancees`.
  3. DP/GREEDY : wiggle_max_length + lemonade_change via `tableaux`.
  4. HORS + NON-RÉG : incohérent -> HORS ; power_int via `repetition`.

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

        ri = ia.demande("reverse_integer", "n", [((123,), 321), ((-123,), -321)],
                        [((120,), 21), ((0,), 0), ((5,), 5), ((1000,), 1)])
        ip = ia.demande("is_palindrome_number", "n", [((121,), True), ((-121,), False)],
                        [((10,), False), ((0,), True), ((12321,), True), ((100,), False)])
        r.append(_check(f"CHIFFRES reverse->`{ri.etage}` palin->`{ip.etage}` (==chiffres)",
                        resolu(ri) and resolu(ip)))

        iso = ia.demande("is_isomorphic", "s, t", [(("egg", "add"), True), (("foo", "bar"), False)],
                         [(("paper", "title"), True), (("ab", "aa"), False), (("a", "a"), True), (("badc", "baba"), False)])
        st = ia.demande("string_to_int", "s", [(("42",), 42), (("   -42",), -42)],
                        [(("4193 with words",), 4193), (("words",), 0), (("+1",), 1), (("00123",), 123)])
        r.append(_check(f"CHAÎNES iso->`{iso.etage}` atoi->`{st.etage}` (==chaines-avancees)",
                        resolu(iso) and resolu(st)))

        wm = ia.demande("wiggle_max_length", "nums", [(([1, 7, 4, 9, 2, 5],), 6), (([1, 2, 3, 4, 5],), 2)],
                        [(([1, 17, 5, 10, 13, 15, 10, 5, 16, 8],), 7), (([1],), 1), (([1, 1, 1],), 1), (([3, 3, 3, 2, 5],), 3)])
        lc = ia.demande("lemonade_change", "bills", [(([5, 5, 5, 10, 20],), True), (([5, 5, 10, 10, 20],), False)],
                        [(([5, 5, 10],), True), (([10, 10],), False), (([5],), True), (([5, 5, 5, 5, 20, 20],), False)])
        r.append(_check(f"DP/GREEDY wiggle->`{wm.etage}` lemonade->`{lc.etage}` (==tableaux)",
                        resolu(wm) and resolu(lc)))

        inc = ia.demande("incoherent_v21", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        pw = ia.demande("power_int", "x, n", [((2, 10), 1024), ((3, 0), 1)], [((5, 3), 125), ((10, 2), 100), ((1, 100), 1)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG power->`{pw.etage}`",
                        not inc.ok and resolu(pw)))

    print()
    print("VAGUE 21 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
