"""
VAGUE 8 — arbre/grille / théorie nombres itérative / DP / chaînes / géométrie (2026-06-19, autonomie). Lacunes
MESURÉES par gap_probe_vague8 (11 vrais HORS ; is_happy était une 4ᵉ COÏNCIDENCE via branchement -> HORS à froid durci
-> ancré en 1ʳᵉ classe). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. NOMBRES (diviseurs) : zeros_factorielle + perfect_power + is_happy ; bits : is_power_of_four + gray_code.
  2. GRAPHE/GRILLE : is_tree via `graphe-connexite`, count_islands via `tableaux`.
  3. DP/CHAÎNES/GÉO : coin_change_ways via `monnaie`, longest_palindromic_subseq via `chaines-avancees`,
     word_count via `mots`, triangle_type via `geometrie`.
  4. HORS + NON-RÉGRESSION : incohérent -> HORS ; is_prime reste via `diviseurs`, reverse_words via `mots`.

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

        zf = ia.demande("trailing_zeros_factorial", "n", [((5,), 1), ((10,), 2)], [((0,), 0), ((25,), 6), ((100,), 24)])
        pp = ia.demande("perfect_power", "n", [((8,), True), ((10,), False)], [((4,), True), ((9,), True), ((7,), False), ((16,), True)])
        ih = ia.demande("is_happy", "n", [((19,), True), ((2,), False)],
                        [((1,), True), ((7,), True), ((4,), False), ((23,), True), ((13,), True)])
        p4 = ia.demande("is_power_of_four", "n", [((16,), True), ((8,), False)], [((1,), True), ((4,), True), ((0,), False), ((64,), True)])
        gc = ia.demande("gray_code", "n", [((2,), 3), ((3,), 2)], [((0,), 0), ((1,), 1), ((4,), 6), ((5,), 7)])
        r.append(_check(f"NOMBRES zf->`{zf.etage}` pp->`{pp.etage}` happy->`{ih.etage}` (==diviseurs) | "
                        f"p4->`{p4.etage}` gray->`{gc.etage}` (==bits)",
                        all(resolu(x) for x in (zf, pp, ih))
                        and all(resolu(x) for x in (p4, gc))))

        tr = ia.demande("is_tree", "n, edges", [((3, [(0, 1), (1, 2)]), True), ((3, [(0, 1)]), False)],
                        [((1, []), True), ((4, [(0, 1), (2, 3)]), False), ((3, [(0, 1), (1, 2), (2, 0)]), False)])
        ci = ia.demande("count_islands", "grid", [(([[1, 1, 0], [0, 1, 0], [0, 0, 1]],), 2), (([[0]],), 0)],
                        [(([[1, 0, 1]],), 2), (([[1, 1], [1, 1]],), 1), (([[1, 0], [0, 1]],), 2)])
        r.append(_check(f"GRAPHE/GRILLE is_tree->`{tr.etage}` (==graphe-connexite) | count_islands->`{ci.etage}` (==tableaux)",
                        resolu(tr)
                        and resolu(ci)))

        cw = ia.demande("coin_change_ways", "coins, amt", [(([1, 2, 5], 5), 4), (([2], 3), 0)],
                        [(([1], 0), 1), (([1, 2], 4), 3), (([3, 5], 8), 1)])
        lps = ia.demande("longest_palindromic_subseq", "s", [(("bbbab",), 4), (("cbbd",), 2)],
                         [(("a",), 1), (("",), 0), (("agbdba",), 5), (("ac",), 1)])
        wc = ia.demande("word_count", "s", [(("hello world",), 2), (("one",), 1)], [(("",), 0), (("a b c",), 3), ((" x ",), 1)])
        tt = ia.demande("triangle_type", "a, b, c", [((3, 3, 3), "equilateral"), ((3, 4, 5), "scalene")],
                        [((3, 3, 4), "isosceles"), ((5, 5, 8), "isosceles"), ((2, 3, 4), "scalene")])
        r.append(_check(f"DP/CH/GÉO ways->`{cw.etage}`(==monnaie) lps->`{lps.etage}`(==chaines) "
                        f"wc->`{wc.etage}`(==mots) tri->`{tt.etage}`(==geometrie)",
                        resolu(cw)
                        and resolu(lps)
                        and resolu(wc)
                        and resolu(tt)))

        inc = ia.demande("incoherent_v8", "n", [((1,), 42), ((2,), 42)], [((3,), 99), ((4,), 7)])
        ipr = ia.demande("is_prime", "n", [((7,), True), ((9,), False)], [((2,), True), ((1,), False), ((97,), True)])
        rw = ia.demande("reverse_words", "s", [(("hello world",), "world hello"), (("one",), "one")], [(("a b c",), "c b a")])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG is_prime->`{ipr.etage}` reverse_words->`{rw.etage}`",
                        not inc.ok and resolu(ipr) and resolu(rw)))

    print()
    print("VAGUE 8 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
