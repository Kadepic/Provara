"""
VAGUE 18 — dates / géométrie 3D / théorie des jeux / bits / automate cellulaire (2026-06-20, nuit, 1.5 Go). Lacunes
MESURÉES par gap_probe_vague18 (6 vrais trous, held-out DURCIS). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. DATES/GÉO : days_between via `calendrier` ; cross_product_3d + dist_squared_3d via `numerique`.
  2. JEUX/BITS : nim_win + count_bits_range via `bits`.
  3. AUTOMATE + HORS : game_of_life_alive via `tableaux` ; incohérent -> HORS.
  4. NON-RÉGRESSION : matrix_trace via `matrice`, dot3d via `numerique`.

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

        db = ia.demande("days_between", "y1, m1, d1, y2, m2, d2", [((2020, 1, 1, 2020, 1, 2), 1), ((2020, 1, 1, 2021, 1, 1), 366)],
                        [((2019, 1, 1, 2020, 1, 1), 365), ((2020, 1, 1, 2020, 2, 1), 31), ((2020, 3, 1, 2020, 3, 1), 0)])
        cp = ia.demande("cross_product_3d", "a, b", [(([1, 0, 0], [0, 1, 0]), [0, 0, 1]), (([0, 1, 0], [0, 0, 1]), [1, 0, 0])],
                        [(([1, 2, 3], [4, 5, 6]), [-3, 6, -3]), (([2, 0, 0], [0, 2, 0]), [0, 0, 4]), (([1, 1, 1], [1, 1, 1]), [0, 0, 0])])
        ds = ia.demande("dist_squared_3d", "a, b", [(([0, 0, 0], [1, 2, 2]), 9), (([1, 1, 1], [1, 1, 1]), 0)],
                        [(([0, 0, 0], [3, 4, 0]), 25), (([1, 0, 0], [0, 0, 0]), 1), (([1, 2, 3], [4, 6, 3]), 25)])
        r.append(_check(f"DATES/GÉO db->`{db.etage}`(==calendrier) cp->`{cp.etage}` ds->`{ds.etage}`(==numerique)",
                        resolu(db) and resolu(cp) and resolu(ds)))

        nm = ia.demande("nim_win", "piles", [(([1, 1],), False), (([1, 2, 3],), False)],
                        [(([1],), True), (([3, 4, 5],), True), (([0, 0],), False), (([2, 2, 3],), True)])
        cb = ia.demande("count_bits_range", "n", [((2,), 2), ((5,), 7)], [((0,), 0), ((1,), 1), ((3,), 4), ((7,), 12)])
        r.append(_check(f"JEUX/BITS nim->`{nm.etage}` cbr->`{cb.etage}` (==bits)",
                        resolu(nm) and resolu(cb)))

        gl = ia.demande("game_of_life_alive", "grid",
                        [(([[0, 1, 0], [0, 1, 0], [0, 1, 0]],), [[0, 0, 0], [1, 1, 1], [0, 0, 0]]), (([[0, 0], [0, 0]],), [[0, 0], [0, 0]])],
                        [(([[1, 1], [1, 1]],), [[1, 1], [1, 1]]), (([[1, 1, 0], [1, 0, 0], [0, 0, 0]],), [[1, 1, 0], [1, 1, 0], [0, 0, 0]])])
        inc = ia.demande("incoherent_v18", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"AUTOMATE gol->`{gl.etage}`(==tableaux) | HORS incoherent ok={inc.ok}",
                        resolu(gl) and not inc.ok))

        mt = ia.demande("matrix_trace", "m", [(([[1, 2], [3, 4]],), 5), (([[5]],), 5)],
                        [(([[1, 0, 0], [0, 2, 0], [0, 0, 3]],), 6), (([[2, 9], [9, 8]],), 10)])
        dt = ia.demande("dot3d", "a, b", [(([1, 2, 3], [4, 5, 6]), 32), (([0, 0, 0], [1, 1, 1]), 0)],
                        [(([1, 0, 0], [0, 1, 0]), 0), (([2, 2, 2], [1, 1, 1]), 6)])
        r.append(_check(f"NON-RÉG trace->`{mt.etage}`(==matrice) dot3d->`{dt.etage}`(==numerique)",
                        resolu(mt) and resolu(dt)))

    print()
    print("VAGUE 18 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
