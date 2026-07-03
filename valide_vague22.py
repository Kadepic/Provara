"""
VAGUE 22 — théorie des nombres / DP / chaîne / bits / géométrie (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par
gap_probe_vague22 (7 vrais trous ; is_right_triangle « résolu » via recurrence = SUSPECT -> ancré en geometrie avec
held-out durci (3,4,6)->False qui casse toute coïncidence non-pythagoricienne). Validées dans le MOTEUR COMPLET.

Critères de MORT (4) :
  1. NOMBRES : amicable_pair + aliquot_sum via `diviseurs`.
  2. DP : rod_cutting + min_palindrome_cuts via `tableaux`.
  3. CHAÎNE/BITS/GÉO : ransom_note via `chaines-avancees` ; reverse_bits_width via `bits` ; is_right_triangle via `geometrie`.
  4. HORS + NON-RÉG : incohérent -> HORS ; est_parfait via `diviseurs`.

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

        ap = ia.demande("amicable_pair", "a, b", [((220, 284), True), ((220, 221), False)],
                        [((1184, 1210), True), ((6, 6), False), ((10, 10), False), ((284, 220), True)])
        al = ia.demande("aliquot_sum", "n", [((6,), 6), ((12,), 16)], [((1,), 0), ((28,), 28), ((7,), 1), ((16,), 15)])
        r.append(_check(f"NOMBRES amicable->`{ap.etage}` aliquot->`{al.etage}` (==diviseurs)",
                        resolu(ap) and resolu(al)))

        rc = ia.demande("rod_cutting", "prices", [(([1, 5, 8, 9],), 10), (([2, 5, 7, 8],), 10)],
                        [(([1],), 1), (([3, 5],), 6), (([1, 5, 8, 9, 10, 17, 17, 20],), 22)])
        mc = ia.demande("min_palindrome_cuts", "s", [(("aab",), 1), (("abccba",), 0)],
                        [(("a",), 0), (("ab",), 1), (("aba",), 0), (("aabbc",), 2)])
        r.append(_check(f"DP rod->`{rc.etage}` palcuts->`{mc.etage}` (==tableaux)",
                        resolu(rc) and resolu(mc)))

        rn = ia.demande("ransom_note", "note, magazine", [(("a", "b"), False), (("aa", "aab"), True)],
                        [(("", "abc"), True), (("abc", "cba"), True), (("aa", "ab"), False), (("aabb", "ab"), False)])
        rb = ia.demande("reverse_bits_width", "n, width", [((1, 8), 128), ((3, 2), 3)],
                        [((1, 1), 1), ((5, 4), 10), ((8, 4), 1), ((0, 4), 0)])
        rt = ia.demande("is_right_triangle", "a, b, c", [((3, 4, 5), True), ((1, 2, 3), False)],
                        [((5, 12, 13), True), ((5, 3, 4), True), ((1, 1, 1), False), ((6, 8, 10), True), ((3, 4, 6), False), ((2, 3, 4), False)])
        r.append(_check(f"CH/BITS/GÉO ransom->`{rn.etage}`(==chaines) revbits->`{rb.etage}`(==bits) right->`{rt.etage}`(==geometrie)",
                        resolu(rn) and resolu(rb) and resolu(rt)))

        inc = ia.demande("incoherent_v22", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        pf = ia.demande("est_parfait", "n", [((6,), True), ((10,), False)], [((28,), True), ((12,), False), ((496,), True)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG est_parfait->`{pf.etage}`(==diviseurs)",
                        not inc.ok and resolu(pf)))

    print()
    print("VAGUE 22 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
