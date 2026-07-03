"""
VAGUE 4 — graphes connexité / conversions-numération / str_index (2026-06-19). Lacunes MESURÉES par
gap_probe_vague4 (num_components, has_cycle, str_index, to_base_digits, int_to_roman, roman_to_int — toutes HORS
avant). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GRAPHE-CONNEXITÉ : num_components + has_cycle via `graphe-connexite` + généralisent.
  2. CONVERSIONS : to_base_digits + int_to_roman + roman_to_int via `conversion` + généralisent.
  3. STR_INDEX + HORS : str_index via `chaines-avancees` + généralise ; une tâche incohérente -> HORS.
  4. NON-RÉGRESSION : vers_binaire reste via `conversion` ; degre reste via `graphe`.

SÉQUENTIEL + garde.
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

        nc = ia.demande("num_components", "n, edges", [((3, [(0, 1)]), 2), ((3, []), 3)],
                        [((4, [(0, 1), (2, 3)]), 2), ((4, [(0, 1), (1, 2), (2, 3)]), 1), ((1, []), 1), ((5, [(0, 4)]), 4)])
        hc = ia.demande("has_cycle", "n, edges",
                        [((3, [(0, 1), (1, 2), (2, 0)]), True), ((3, [(0, 1), (1, 2)]), False)],
                        [((4, [(0, 1), (2, 3)]), False), ((4, [(0, 1), (1, 2), (2, 3), (3, 1)]), True), ((2, []), False)])
        r.append(_check(f"GRAPHE num_components -> `{nc.etage}`({nc.appels}c) gen={nc.generalise} | "
                        f"has_cycle -> `{hc.etage}`({hc.appels}c) gen={hc.generalise}",
                        resolu(nc)
                        and resolu(hc)))

        tb = ia.demande("to_base_digits", "n, b", [((10, 2), [1, 0, 1, 0]), ((255, 16), [15, 15])],
                        [((0, 2), [0]), ((8, 8), [1, 0]), ((7, 2), [1, 1, 1]), ((100, 10), [1, 0, 0])])
        ir = ia.demande("int_to_roman", "n", [((4,), "IV"), ((9,), "IX")],
                        [((58,), "LVIII"), ((1994,), "MCMXCIV"), ((1,), "I"), ((40,), "XL")])
        ri = ia.demande("roman_to_int", "s", [(("IV",), 4), (("IX",), 9)],
                        [(("LVIII",), 58), (("MCMXCIV",), 1994), (("III",), 3), (("XL",), 40)])
        r.append(_check(f"CONVERSIONS to_base -> `{tb.etage}`({tb.appels}c) | int_to_roman -> `{ir.etage}`({ir.appels}c) | "
                        f"roman_to_int -> `{ri.etage}`({ri.appels}c)",
                        resolu(tb)
                        and resolu(ir)
                        and resolu(ri)))

        si = ia.demande("str_index", "s, sub", [(("hello", "ll"), 2), (("abc", "b"), 1)],
                        [(("abc", "x"), -1), (("abc", "a"), 0), (("banana", "na"), 2)])
        inc = ia.demande("incoherent_v4", "n, edges", [((2, [(0, 1)]), 42)], [((3, []), 99)])
        r.append(_check(f"STR_INDEX -> `{si.etage}`({si.appels}c) gen={si.generalise} | HORS incoherent ok={inc.ok}",
                        resolu(si) and not inc.ok))

        vb = ia.demande("vers_binaire", "n", [((5,), "101"), ((2,), "10")], [((8,), "1000"), ((1,), "1")])
        de = ia.demande("degre", "edges, v", [(([(0, 1), (1, 2)], 1), 2), (([(0, 1)], 0), 1)],
                        [(([(0, 1), (1, 2), (1, 3)], 1), 3), (([(0, 1)], 2), 0)])
        r.append(_check(f"NON-RÉGRESSION : vers_binaire -> `{vb.etage}`(==conversion) | degre -> `{de.etage}`(==graphe)",
                        resolu(vb)
                        and resolu(de)))

    print()
    print("VAGUE 4 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
