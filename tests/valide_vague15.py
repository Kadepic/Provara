"""
VAGUE 15 — PILE MONOTONE + GREEDY (2026-06-20, nuit). Lacunes MESURÉES par gap_probe_vague15 (4 vrais trous, held-out
DURCIS). NB ROBUSTESSE : daily_temperatures (list->list, grandes valeurs) FAISAIT OOM/SIGKILL le moteur via un exec
en-process non borné ; corrigé (garde mémoire prefiltre + protocole ulimit -v 1.5 Go) -> MemoryError rattrapable ->
résolu via `pile`. Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. PILE MONOTONE : largest_rectangle_histogram + daily_temperatures via `pile`.
  2. GREEDY : jump_game + gas_station via `tableaux`.
  3. HORS : incohérent -> HORS (jamais de faux).
  4. NON-RÉGRESSION : next_greater reste via `pile`, sliding_window_min via `fenetre`.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurPile
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        lr = ia.demande("largest_rectangle_histogram", "heights", [(([2, 1, 5, 6, 2, 3],), 10), (([2, 4],), 4)],
                        [(([1, 1, 1],), 3), (([5],), 5), (([0, 9],), 9), (([6, 2, 5, 4, 5, 1, 6],), 12)])
        dt = ia.demande("daily_temperatures", "temps", [(([73, 74, 75, 71, 69, 72, 76, 73],), [1, 1, 4, 2, 1, 1, 0, 0]), (([30, 40, 50, 60],), [1, 1, 1, 0])],
                        [(([30, 60, 90],), [1, 1, 0]), (([50],), [0]), (([90, 80, 70],), [0, 0, 0])])
        r.append(_check(f"PILE lrh->`{lr.etage}` dt->`{dt.etage}` (==pile)",
                        resolu(lr) and resolu(dt)))

        jg = ia.demande("jump_game", "nums", [(([2, 3, 1, 1, 4],), True), (([3, 2, 1, 0, 4],), False)],
                        [(([0],), True), (([1, 0],), True), (([0, 1],), False), (([2, 0, 0],), True)])
        gs = ia.demande("gas_station", "gas, cost", [(([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]), 3), (([2, 3, 4], [3, 4, 3]), -1)],
                        [(([5, 1, 2, 3, 4], [4, 4, 1, 5, 1]), 4), (([2], [2]), 0), (([3, 3], [1, 2]), 0)])
        r.append(_check(f"GREEDY jump->`{jg.etage}` gas->`{gs.etage}` (==tableaux)",
                        resolu(jg) and resolu(gs)))

        inc = ia.demande("incoherent_v15", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS incoherent ok={inc.ok}", not inc.ok))

        ng = ia.demande("next_greater", "xs", [(([2, 1, 3],), [3, 3, -1]), (([1, 2],), [2, -1])],
                        [(([5, 4, 3],), [-1, -1, -1]), (([1, 3, 2],), [3, -1, -1])])
        sw = ia.demande("sliding_window_min", "xs, k", [(([1, 3, -1, -3, 5, 3, 6, 7], 3), [-1, -3, -3, -3, 3, 3]), (([1, 2], 1), [1, 2])],
                        [(([4, 3, 2, 1], 2), [3, 2, 1]), (([5], 1), [5])])
        r.append(_check(f"NON-RÉG next_greater->`{ng.etage}`(==pile) swmin->`{sw.etage}`(==fenetre)",
                        resolu(ng) and resolu(sw)))

        # VIVACITÉ (anti-code-mort) : la brique spécialiste `pile` résout SA tâche canonique
        # largest_rectangle_histogram en DIRECT (hors routeur) sur tests + held-out adverse.
        r.append(_check("VIVACITÉ : la brique `pile` résout largest_rectangle_histogram en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurPile(), "largest_rectangle_histogram", "heights",
                                       "def check(c):\n    assert c([2,1,5,6,2,3])==10\n    assert c([2,4])==4\ncheck(largest_rectangle_histogram)",
                                       "def check(c):\n    assert c([1,1,1])==3\n    assert c([5])==5\n    assert c([0,9])==9\n    assert c([6,2,5,4,5,1,6])==12\ncheck(largest_rectangle_histogram)")))

    print()
    print(f"VAGUE 15 VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
