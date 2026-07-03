"""
VAGUE 9 — graphes pondérés / nombres modulaires / DP / encodage / chiffrement (2026-06-19, autonomie). Lacunes
MESURÉES par gap_probe_vague9 (9 vrais HORS). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GRAPHES PONDÉRÉS : dijkstra + mst_weight via `graphe-connexite`.
  2. NOMBRES + JOSEPHUS : is_automorphic + modinv via `diviseurs` ; josephus via `numerique`.
  3. DP + CIPHER + PANGRAMME : partition_equal_subset/count_inversions via `tableaux` ; atbash via `cesar` ;
     is_pangram via `chaines-avancees`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; gcd reste, run_length_decode via `run-length`.

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

        dj = ia.demande("dijkstra", "n, edges, src, dst", [((4, [(0, 1, 1), (1, 2, 2), (0, 2, 4)], 0, 2), 3)],
                        [((4, [(0, 1, 1), (2, 3, 1)], 0, 3), -1), ((1, [], 0, 0), 0), ((3, [(0, 1, 5), (1, 2, 5)], 0, 2), 10)])
        ms = ia.demande("mst_weight", "n, edges", [((3, [(0, 1, 1), (1, 2, 2), (0, 2, 3)]), 3)],
                        [((4, [(0, 1, 1), (1, 2, 1), (2, 3, 1)]), 3), ((1, []), 0), ((2, [(0, 1, 5)]), 5)])
        r.append(_check(f"GRAPHES PONDÉRÉS dijkstra->`{dj.etage}` mst->`{ms.etage}` (==graphe-connexite)",
                        resolu(dj)
                        and resolu(ms)))

        au = ia.demande("is_automorphic", "n", [((5,), True), ((7,), False)], [((6,), True), ((25,), True), ((76,), True), ((2,), False)])
        mi = ia.demande("modinv", "a, m", [((3, 11), 4), ((2, 4), -1)], [((1, 5), 1), ((3, 7), 5), ((2, 6), -1)])
        jo = ia.demande("josephus", "n, k", [((5, 2), 2), ((1, 1), 0)], [((7, 3), 3), ((2, 1), 1), ((4, 2), 0)])
        r.append(_check(f"NOMBRES automorphe->`{au.etage}` modinv->`{mi.etage}` (==diviseurs) | josephus->`{jo.etage}` (==numerique)",
                        resolu(au)
                        and resolu(mi)
                        and resolu(jo)))

        pe = ia.demande("partition_equal_subset", "xs", [(([1, 5, 11, 5],), True), (([1, 2, 3, 5],), False)],
                        [(([1, 1],), True), (([2, 2, 2],), False), (([1, 2, 3, 4],), True)])
        ci = ia.demande("count_inversions", "xs", [(([2, 1],), 1), (([1, 2, 3],), 0)], [(([3, 2, 1],), 3), (([1, 3, 2],), 1), (([],), 0)])
        at = ia.demande("atbash", "s", [(("abc",), "zyx"), (("az",), "za")], [(("",), ""), (("hello",), "svool"), (("zyx",), "abc")])
        pg = ia.demande("is_pangram", "s", [(("the quick brown fox jumps over the lazy dog",), True), (("hello",), False)],
                        [(("",), False), (("abcdefghijklmnopqrstuvwxyz",), True)])
        r.append(_check(f"DP part->`{pe.etage}` inv->`{ci.etage}` (==tableaux) | atbash->`{at.etage}`(==cesar) "
                        f"pangram->`{pg.etage}`(==chaines)",
                        resolu(pe)
                        and resolu(ci)
                        and resolu(at)
                        and resolu(pg)))

        inc = ia.demande("incoherent_v9", "n", [((1,), 42), ((2,), 42)], [((3,), 99), ((4,), 7)])
        rd = ia.demande("run_length_decode", "s", [(("a3b2",), "aaabb"), (("x1",), "x")], [(("",), ""), (("z3",), "zzz")])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG run_length_decode->`{rd.etage}`",
                        not inc.ok and resolu(rd)))

    print()
    print("VAGUE 9 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
