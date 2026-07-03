"""
VAGUE 25 — DP / fenêtre / grille BFS / bits (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par gap_probe_vague25 (6 vrais
trous ; 1 held-out à MOI corrigé : house_robber_circular [5,1,1,5]=6). Validées dans le MOTEUR COMPLET.

Critères de MORT (4) :
  1. DP : house_robber_circular + target_sum_ways via `tableaux`.
  2. FENÊTRE/GRILLE : subarray_product_less_than_k + rotting_oranges + longest_mountain via `tableaux`.
  3. BITS + HORS : complement_base10 via `bits` ; incohérent -> HORS.
  4. NON-RÉG : lcs_length via `dp2d`, max_consecutive_ones via `pile`.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurBits
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        hr = ia.demande("house_robber_circular", "nums", [(([2, 3, 2],), 3), (([1, 2, 3, 1],), 4)],
                        [(([1],), 1), (([1, 2],), 2), (([2, 7, 9, 3, 1],), 11), (([5, 1, 1, 5],), 6)])
        ts = ia.demande("target_sum_ways", "nums, target", [(([1, 1, 1, 1, 1], 3), 5), (([1], 1), 1)],
                        [(([1], 2), 0), (([1, 0], 1), 2), (([0, 0, 0, 0, 0], 0), 32)])
        r.append(_check(f"DP robber_circ->`{hr.etage}` target_sum->`{ts.etage}` (==tableaux)",
                        resolu(hr) and resolu(ts)))

        sp = ia.demande("subarray_product_less_than_k", "nums, k", [(([10, 5, 2, 6], 100), 8), (([1, 2, 3], 0), 0)],
                        [(([1, 1, 1], 2), 6), (([10], 5), 0), (([2, 3], 7), 3)])
        ro = ia.demande("rotting_oranges", "grid", [(([[2, 1, 1], [1, 1, 0], [0, 1, 1]],), 4), (([[2, 1, 1], [0, 1, 1], [1, 0, 1]],), -1)],
                        [(([[0, 2]],), 0), (([[2]],), 0), (([[2, 1], [1, 1]],), 2)])
        lm = ia.demande("longest_mountain", "arr", [(([2, 1, 4, 7, 3, 2, 5],), 5), (([2, 2, 2],), 0)],
                        [(([0, 1, 0],), 3), (([1, 2, 3],), 0), (([0, 1, 2, 3, 2, 1, 0],), 7)])
        r.append(_check(f"FEN/GRILLE subprod->`{sp.etage}` rotting->`{ro.etage}` mountain->`{lm.etage}` (==tableaux)",
                        all(resolu(x) for x in (sp, ro, lm))))

        cb = ia.demande("complement_base10", "n", [((5,), 2), ((10,), 5)], [((1,), 0), ((7,), 0), ((2,), 1), ((1023,), 0)])
        inc = ia.demande("incoherent_v25", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"BITS complement->`{cb.etage}`(==bits) | HORS incoherent ok={inc.ok}",
                        resolu(cb) and not inc.ok))

        lc = ia.demande("lcs_length", "a, b", [(("abcde", "ace"), 3), (("abc", "abc"), 3)],
                        [(("abc", "def"), 0), (("aggtab", "gxtxayb"), 4)])
        mc = ia.demande("max_consecutive_ones", "nums", [(([1, 1, 0, 1, 1, 1],), 3), (([1, 0, 1, 1, 0, 1],), 2)],
                        [(([0],), 0), (([1, 1, 1],), 3)])
        r.append(_check(f"NON-RÉG lcs->`{lc.etage}`(==dp2d) maxones->`{mc.etage}`(==pile)",
                        resolu(lc) and resolu(mc)))

        # VIVACITÉ (anti-code-mort) : la brique spécialiste `bits` résout SA tâche canonique complement_base10
        # en DIRECT (hors routeur) sur tests + held-out adverse.
        r.append(_check("VIVACITÉ : la brique `bits` résout complement_base10 en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurBits(), "complement_base10", "n",
                                       "def check(c):\n    assert c(5)==2\n    assert c(10)==5\ncheck(complement_base10)",
                                       "def check(c):\n    assert c(1)==0\n    assert c(7)==0\n    assert c(2)==1\n    assert c(1023)==0\ncheck(complement_base10)")))

    print()
    print(f"VAGUE 25 VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
