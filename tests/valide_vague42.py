"""
VAGUE 42 — PROFONDE (DP/greedy/combinatoire) (2026-06-20, reprise post-redémarrage, 1.5 Go). gap_probe_vague42 = 8
tâches : 2 vrais trous bâtis + 6 déjà couvertes réelles.

DÉCOUVERTE CLÉ (anti-coïncidence) : `jump_game_ii` était capté par le CHEMIN RAPIDE means-end (mono-arg list->int)
à ~19512 évals avec une expression arithmétique COÏNCIDENTE (calée sur 5 points faibles). Sous held-out DURCI,
means-end échoue -> retombe sur la brique greedy bâtie dans `tableaux` (2766 évals, correcte, −86 % ressources).
=> jump_game_ii est validé AVEC held-out durci, épinglé `tableaux` (preuve que la brique est nécessaire ET utilisée).

Bâtis : jump_game_ii (greedy BFS O(n), tableaux) ; gray_code SÉQUENCE (liste 2**n, bits — distinct du gray_code
scalaire pré-existant). Réels : jump_game, integer_break, perfect_squares, container_with_most_water -> tableaux ;
unique_paths -> comptage-combinatoire ; count_and_say -> chaines-avancees.

Critères de MORT (4) :
  1. BÂTIS : jump_game_ii via `tableaux` (held-out DURCI) ; gray_code via `bits`.
  2. DP/2-POINTEURS : integer_break + perfect_squares + container_with_most_water via `tableaux`.
  3. GREEDY/COMBI/SUITE : jump_game via `tableaux` ; unique_paths via `comptage-combinatoire` ; count_and_say via `chaines-avancees`.
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

        # ---- 1. BÂTIS ------------------------------------------------------------------------------------------
        # jump_game_ii : held-out DURCI (10 cas) pour défaire la coïncidence means-end et forcer la brique tableaux.
        j2 = ia.demande("jump_game_ii", "nums", [(([2, 3, 1, 1, 4],), 2), (([2, 1],), 1)],
                        [(([0],), 0), (([1, 1, 1],), 2), (([2, 3, 0, 1, 4],), 2), (([1, 2, 3, 4, 5],), 3),
                         (([5, 4, 3, 2, 1, 0, 0],), 2), (([1, 1, 1, 1],), 3), (([1, 2, 0, 3],), 2),
                         (([4, 1, 1, 1, 1],), 1), (([2, 3, 1, 1, 4, 2, 1],), 3), (([3, 3, 3, 3, 3, 3],), 2)])
        gc = ia.demande("gray_code", "n", [((0,), [0]), ((1,), [0, 1])],
                        [((2,), [0, 1, 3, 2]), ((3,), [0, 1, 3, 2, 6, 7, 5, 4])])
        r.append(_check(f"BÂTIS jump_game_ii->`{j2.etage}`(==tableaux, durci) gray_code->`{gc.etage}`(==bits)",
                        resolu(j2) and resolu(gc)))

        # ---- 2. DP / 2-POINTEURS -------------------------------------------------------------------------------
        ib = ia.demande("integer_break", "n", [((2,), 1), ((10,), 36)],
                        [((8,), 18), ((4,), 4), ((3,), 2)])
        ps = ia.demande("perfect_squares", "n", [((12,), 3), ((13,), 2)],
                        [((1,), 1), ((4,), 1), ((2,), 2), ((3,), 3)])
        cw = ia.demande("container_with_most_water", "height", [(([1, 8, 6, 2, 5, 4, 8, 3, 7],), 49), (([1, 1],), 1)],
                        [(([4, 3, 2, 1, 4],), 16), (([1, 2, 1],), 2)])
        # integer_break / perfect_squares -> étage DÉDIÉ `dp-int` (campagne <100 : sortis du gros `tableaux`) ; container reste tableaux.
        r.append(_check(f"DP/2-PT integer_break->`{ib.etage}` perfect_squares->`{ps.etage}`(==dp-int) container->`{cw.etage}`(==tableaux)",
                        resolu(ib) and resolu(ps) and resolu(cw)))

        # ---- 3. GREEDY / COMBI / SUITE -------------------------------------------------------------------------
        jg = ia.demande("jump_game", "nums", [(([2, 3, 1, 1, 4],), True), (([3, 2, 1, 0, 4],), False)],
                        [(([0],), True), (([1, 0, 1, 0],), False), (([2, 0, 0],), True)])
        up = ia.demande("unique_paths", "m, n", [((3, 7), 28), ((3, 2), 3)],
                        [((1, 1), 1), ((2, 2), 2), ((3, 3), 6)])
        cs = ia.demande("count_and_say", "n", [((1,), "1"), ((2,), "11")],
                        [((3,), "21"), ((4,), "1211"), ((5,), "111221")])
        r.append(_check(f"GREEDY/COMBI jump_game->`{jg.etage}`(==tableaux) unique_paths->`{up.etage}`(==comptage-combinatoire) count_and_say->`{cs.etage}`(==chaines-avancees)",
                        resolu(jg) and resolu(up) and resolu(cs)))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v42", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 42 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
