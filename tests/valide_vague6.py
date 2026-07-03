"""
VAGUE 6 — graphes BFS / numérique / matmul / chaînes / pile multi-délimiteurs (2026-06-19, autonomie). Lacunes
MESURÉES par gap_probe_vague6 (7 vrais HORS ; coin_change_min était un FAUX trou = mon held-out erroné, déjà couvert
par `monnaie`). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GRAPHES : bfs_dist + is_bipartite via `graphe-connexite` + généralisent.
  2. NUMÉRIQUE + MATMUL : horner + lcm_list via `numerique` ; matmul via `matrice`.
  3. CHAÎNES + PILE : longest_common_substring via `chaines-avancees` ; multi_balanced via `pile`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; coin_change_min reste via `monnaie` ; num_components via `graphe-connexite`.

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

        bf = ia.demande("bfs_dist", "n, edges, src", [((4, [(0, 1), (1, 2), (2, 3)], 0), [0, 1, 2, 3])],
                        [((4, [(0, 1), (2, 3)], 0), [0, 1, -1, -1]), ((3, [(0, 1), (0, 2)], 0), [0, 1, 1]), ((1, [], 0), [0])])
        bi = ia.demande("is_bipartite", "n, edges",
                        [((4, [(0, 1), (1, 2), (2, 3)]), True), ((3, [(0, 1), (1, 2), (2, 0)]), False)],
                        [((2, [(0, 1)]), True), ((4, [(0, 1), (1, 2), (2, 3), (3, 0)]), True), ((3, []), True)])
        # bfs_dist_st = plus court chemin NON pondéré entre DEUX sommets (gap_probe DUR 2026-06-24) — comble le trou
        # entre bfs_dist (liste depuis source) et dijkstra (pondéré). -1 inatteignable, 0 si s==t.
        bst = ia.demande("bfs_dist_st", "n, edges, s, t", [((4, [(0, 1), (1, 2), (2, 3)], 0, 3), 3), ((4, [(0, 1), (0, 2), (2, 3)], 0, 3), 2)],
                         [((3, [(0, 1), (1, 2)], 0, 2), 2), ((4, [(0, 1)], 0, 3), -1), ((2, [(0, 1)], 1, 1), 0)])
        r.append(_check(f"GRAPHES bfs->`{bf.etage}` bipartite->`{bi.etage}` bfs_st->`{bst.etage}`",
                        resolu(bf)
                        and resolu(bi)
                        and resolu(bst)))

        ho = ia.demande("horner", "coeffs, x", [(([1, 2, 3], 2), 11), (([2, 0, 1], 3), 19)],
                        [(([1], 5), 1), (([1, 0], 4), 4), (([3, 2, 1], 0), 1)])
        lc = ia.demande("lcm_list", "xs", [(([4, 6],), 12), (([2, 3, 4],), 12)], [(([5],), 5), (([2, 4, 8],), 8), (([3, 5],), 15)])
        mm = ia.demande("matmul", "a, b", [(([[1, 2], [3, 4]], [[5, 6], [7, 8]]), [[19, 22], [43, 50]])],
                        [(([[1, 0], [0, 1]], [[5, 6], [7, 8]]), [[5, 6], [7, 8]]), (([[2]], [[3]]), [[6]])])
        r.append(_check(f"NUMÉRIQUE horner->`{ho.etage}` lcm->`{lc.etage}` (==numerique) | matmul->`{mm.etage}` (==matrice)",
                        resolu(ho)
                        and resolu(lc)
                        and resolu(mm)))

        cs = ia.demande("longest_common_substring", "a, b", [(("abcde", "abfce"), 2), (("abc", "xyz"), 0)],
                        [(("aaa", "aa"), 2), (("abcdef", "zabcz"), 3), (("", "x"), 0)])
        mb = ia.demande("multi_balanced", "s", [(("()[]{}",), True), (("([)]",), False)],
                        [(("{[]}",), True), (("(",), False), (("",), True), (("([{}])",), True)])
        r.append(_check(f"CHAÎNES lcs->`{cs.etage}` (==chaines-avancees) | PILE multi_balanced->`{mb.etage}` (==pile)",
                        resolu(cs)
                        and resolu(mb)))

        inc = ia.demande("incoherent_v6", "n, edges", [((2, [(0, 1)]), 42)], [((3, []), 99)])
        cc = ia.demande("coin_change_min", "coins, amt", [(([1, 2, 5], 11), 3), (([2], 3), -1)],
                        [(([1], 0), 0), (([1, 5, 10], 18), 5), (([3, 7], 12), 4)])
        nc = ia.demande("num_components", "n, edges", [((3, [(0, 1)]), 2), ((3, []), 3)],
                        [((4, [(0, 1), (2, 3)]), 2), ((1, []), 1)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG coin_change->`{cc.etage}`(==monnaie) | num_comp->`{nc.etage}`",
                        not inc.ok and resolu(cc)
                        and resolu(nc)))

    print()
    print("VAGUE 6 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
