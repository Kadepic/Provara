"""
VAGUE 37 — théorie des nombres / numération (2026-06-20, nuit, 1.5 Go). gap_probe_vague37 = 8 tâches : base_7 bâtie
(numerique) + 7 déjà couvertes réelles (count_primes, perfect_number, is_power_of_three, prime_factors,
trailing_zeros_factorial via `diviseurs` ; int_to_roman via `conversion` ; bulb_switch via `math-avance`).
Held-out ADVERSE, pré-vérifiés par référence.

Critères de MORT (4) :
  1. DIVISEURS-1 : count_primes + perfect_number + is_power_of_three via `diviseurs`.
  2. DIVISEURS-2 : prime_factors + trailing_zeros_factorial via `diviseurs`.
  3. NUMÉRATION : int_to_roman via `conversion` ; base_7 via `numerique` ; bulb_switch via `math-avance`.
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

        cp = ia.demande("count_primes", "n", [((10,), 4), ((0,), 0)],
                        [((3,), 1), ((5,), 2), ((20,), 8), ((1,), 0), ((30,), 10)])
        pn = ia.demande("perfect_number", "n", [((28,), True), ((6,), True)],
                        [((496,), True), ((7,), False), ((8128,), True), ((2,), False), ((12,), False)])
        p3 = ia.demande("is_power_of_three", "n", [((27,), True), ((45,), False)],
                        [((3,), True), ((0,), False), ((81,), True), ((2,), False), ((1,), True)])
        r.append(_check(f"DIVISEURS-1 count_primes->`{cp.etage}` perfect->`{pn.etage}` pow3->`{p3.etage}`",
                        all(resolu(x) for x in (cp, pn, p3))))

        pf = ia.demande("prime_factors", "n", [((12,), [2, 2, 3]), ((17,), [17])],
                        [((60,), [2, 2, 3, 5]), ((8,), [2, 2, 2]), ((13,), [13]), ((100,), [2, 2, 5, 5]), ((1,), [])])
        tz = ia.demande("trailing_zeros_factorial", "n", [((5,), 1), ((25,), 6)],
                        [((3,), 0), ((15,), 3), ((100,), 24), ((4,), 0), ((10,), 2)])
        r.append(_check(f"DIVISEURS-2 prime_factors->`{pf.etage}` trailing_zeros->`{tz.etage}`",
                        all(resolu(x) for x in (pf, tz))))

        ir = ia.demande("int_to_roman", "n", [((3,), "III"), ((1994,), "MCMXCIV")],
                        [((4,), "IV"), ((9,), "IX"), ((40,), "XL"), ((2023,), "MMXXIII"), ((3999,), "MMMCMXCIX")])
        b7 = ia.demande("base_7", "n", [((100,), "202"), ((7,), "10")],
                        [((1,), "1"), ((6,), "6"), ((8,), "11"), ((49,), "100"), ((0,), "0")])
        bs = ia.demande("bulb_switch", "n", [((3,), 1), ((1,), 1)],
                        [((4,), 2), ((9,), 3), ((10,), 3), ((16,), 4), ((0,), 0)])
        r.append(_check(f"NUMÉRATION roman->`{ir.etage}` base_7->`{b7.etage}` bulb->`{bs.etage}`",
                        resolu(ir) and resolu(b7) and resolu(bs)))

        inc = ia.demande("incoherent_v37", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 37 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
