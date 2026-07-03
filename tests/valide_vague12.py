"""
VAGUE 12 — Floyd-Warshall / topo / KMP / Z-function / somme-2-carrés / variance / suite consécutive (2026-06-19,
autonomie de nuit). Lacunes MESURÉES par gap_probe_vague12 (7 vrais HORS, held-out DURCIS d'emblée -> 0 coïncidence).
Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GRAPHES : apsp_sum (Floyd-Warshall) + topo_first (Kahn) via `graphe-connexite`.
  2. MATCHING DE CHAÎNES : kmp_failure (fonction préfixe) + z_function via `chaines-avancees`.
  3. NOMBRES/STATS/DP : est_somme_deux_carres via `diviseurs` ; variance_num via `statistiques` ;
     longest_consecutive via `tableaux`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; bellman_ford reste via `graphe-connexite`, mediane via `statistiques`.

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

        ap = ia.demande("apsp_sum", "n, edges", [((3, [(0, 1, 2), (1, 2, 3)]), 10), ((2, [(0, 1, 7)]), 7)],
                        [((3, [(0, 1, 1), (1, 2, 1), (0, 2, 5)]), 4), ((4, [(0, 1, 1), (1, 2, 1), (2, 3, 1)]), 10)])
        tp = ia.demande("topo_first", "n, edges", [((3, [(0, 1), (0, 2)]), 0), ((2, [(1, 0)]), 1)],
                        [((4, [(0, 1), (1, 2), (2, 3)]), 0), ((3, [(2, 0), (2, 1)]), 2)])
        r.append(_check(f"GRAPHES apsp->`{ap.etage}` topo->`{tp.etage}` (==graphe-connexite)",
                        resolu(ap) and resolu(tp)))

        km = ia.demande("kmp_failure", "s", [(("ababa",), [0, 0, 1, 2, 3]), (("aaaa",), [0, 1, 2, 3])],
                        [(("abcabd",), [0, 0, 0, 1, 2, 0]), (("aabaa",), [0, 1, 0, 1, 2]), (("abc",), [0, 0, 0])])
        zf = ia.demande("z_function", "s", [(("aaaa",), [0, 3, 2, 1]), (("abab",), [0, 0, 2, 0])],
                        [(("aabaa",), [0, 1, 0, 2, 1]), (("abc",), [0, 0, 0]), (("aaa",), [0, 2, 1])])
        r.append(_check(f"MATCHING kmp->`{km.etage}` z->`{zf.etage}` (==chaines-avancees)",
                        resolu(km) and resolu(zf)))

        s2 = ia.demande("est_somme_deux_carres", "n", [((5,), True), ((3,), False)],
                        [((25,), True), ((7,), False), ((0,), True), ((2,), True), ((11,), False)])
        vn = ia.demande("variance_num", "xs", [(([1, 2, 3],), 6), (([2, 2, 2],), 0)],
                        [(([1, 3],), 4), (([0, 0, 9],), 162), (([1, 2, 3, 4],), 20), (([5, 5, 5, 5],), 0)])
        lc = ia.demande("longest_consecutive", "xs", [(([100, 4, 200, 1, 3, 2],), 4), (([1, 2, 0, 1],), 3)],
                        [(([10],), 1), (([],), 0), (([5, 6, 7, 8, 9],), 5), (([1, 3, 5],), 1)])
        r.append(_check(f"NOMBRES s2c->`{s2.etage}`(==diviseurs) var->`{vn.etage}`(==statistiques) lc->`{lc.etage}`(==tableaux)",
                        resolu(s2) and resolu(vn) and resolu(lc)))

        inc = ia.demande("incoherent_v12", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        bf = ia.demande("bellman_ford", "n, edges, src, dst", [((3, [(0, 1, 4), (0, 2, 1), (2, 1, 2)], 0, 1), 3)],
                        [((3, [(0, 1, 5), (1, 2, -3)], 0, 2), 2), ((4, [(0, 1, 1)], 0, 3), -1)])
        md = ia.demande("mediane", "xs", [(([3, 1, 2],), 2), (([5, 4, 9, 1, 3],), 4)],
                        [(([7],), 7), (([2, 8, 5],), 5)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG bellman->`{bf.etage}` mediane->`{md.etage}`",
                        not inc.ok and resolu(bf) and resolu(md)))

    print()
    print("VAGUE 12 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
