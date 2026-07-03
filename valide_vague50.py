"""
VAGUE 50 — BACKTRACKING & COMPTAGE (2026-06-23 nuit, autonomie). gap_probe_vague50 = 6 tâches :
3 VRAIS TROUS bâtis + 3 confirmées.

Bâtis cette vague :
  • `n_queens_count` -> `comptage-combinatoire` (BACKTRACKING colonnes + 2 diagonales ; 1er vrai backtracking récursif).
  • `count_paths_obstacles` -> `tableaux` (DP chemins avec obstacles).
  • `letter_combinations_count` -> `chaines-avancees` (produit des tailles de touches du clavier téléphone).
  Vérifiés sur cas adverses (n_queens(9)=352, grille pleine 3×3=6, '789'=48) avant câblage.
Confirmées : catalan (`dp-int`), partitions_count (`comptage-combinatoire`), factorial (`chiffres`).

Critères de MORT (4) :
  1. BACKTRACKING : n_queens_count via `comptage-combinatoire` (held-out 1..8).
  2. COMPTAGE APPLICATIF : count_paths_obstacles via `tableaux` ; letter_combinations_count via `chaines-avancees`.
  3. FORMULES (confirmation) : catalan + partitions_count + factorial (ok+generalise).
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

        # ---- 1. BACKTRACKING ------------------------------------------------------------------------------
        nq = ia.demande("n_queens_count", "n", [((4,), 2), ((5,), 10)],
                        [((1,), 1), ((2,), 0), ((3,), 0), ((6,), 4), ((7,), 40), ((8,), 92)])
        r.append(_check(f"BACKTRACKING n_queens_count->`{nq.etage}` (résolu, étage libre)",
                        resolu(nq)))

        # ---- 2. COMPTAGE APPLICATIF ----------------------------------------------------------------------
        cp = ia.demande("count_paths_obstacles", "grid",
                        [(([[0, 0, 0], [0, 1, 0], [0, 0, 0]],), 2), (([[0, 1], [0, 0]],), 1)],
                        [(([[0]],), 1), (([[1, 0]],), 0), (([[0, 0], [0, 0]],), 2),
                         (([[0, 0, 0], [0, 0, 0], [0, 0, 0]],), 6), (([[0, 0], [1, 0]],), 1)])
        lc = ia.demande("letter_combinations_count", "digits", [(("23",), 9), (("7",), 4)],
                        [(("79",), 16), (("2",), 3), (("",), 0), (("234",), 27), (("789",), 48)])
        r.append(_check(f"COMPTAGE count_paths_obstacles->`{cp.etage}` letter_combinations->`{lc.etage}` (résolu, étage libre)",
                        resolu(cp) and resolu(lc)))

        # ---- 3. FORMULES (confirmation, ok+generalise) ---------------------------------------------------
        ca = ia.demande("catalan", "n", [((3,), 5), ((4,), 14)], [((0,), 1), ((1,), 1), ((2,), 2), ((5,), 42)])
        pc = ia.demande("partitions_count", "n", [((4,), 5), ((6,), 11)], [((1,), 1), ((5,), 7), ((0,), 1), ((7,), 15)])
        fa = ia.demande("factorial", "n", [((5,), 120), ((6,), 720)], [((0,), 1), ((1,), 1), ((3,), 6), ((7,), 5040)])
        r.append(_check(f"FORMULES catalan->`{ca.etage}` partitions->`{pc.etage}` factorial->`{fa.etage}`",
                        all(resolu(x) for x in (ca, pc, fa))))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------
        inc = ia.demande("incoherent_v50", "n", [((1,), 42)], [((2,), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 50 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
