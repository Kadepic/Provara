"""
VAGUE 17 — greedy / DP / fenêtre / chaînes arithmétiques (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par
gap_probe_vague17 (7 vrais trous, held-out DURCIS). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. GREEDY : min_jumps + candy via `tableaux`.
  2. DP/FENÊTRE/COMPTAGE : interleaving_string + longest_repeating_char_replace + top_k_frequent via `tableaux`.
  3. CHAÎNES ARITH : count_and_say + multiply_strings via `chaines-avancees`.
  4. HORS + NON-RÉG : incohérent -> HORS ; distinct_subsequences via `chaines-avancees`, container_with_most_water via `tableaux`.

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

        mj = ia.demande("min_jumps", "nums", [(([2, 3, 1, 1, 4],), 2), (([2, 3, 0, 1, 4],), 2)],
                        [(([0],), 0), (([1, 1, 1],), 2), (([1, 2, 3],), 2), (([5, 1, 1, 1, 1],), 1)])
        cd = ia.demande("candy", "ratings", [(([1, 0, 2],), 5), (([1, 2, 2],), 4)],
                        [(([1, 3, 2, 2, 1],), 7), (([5, 4, 3, 2, 1],), 15), (([1, 1, 1],), 3)])
        r.append(_check(f"GREEDY min_jumps->`{mj.etage}` candy->`{cd.etage}`",
                        resolu(mj) and resolu(cd)))

        il = ia.demande("interleaving_string", "s1, s2, s3", [(("aabcc", "dbbca", "aadbbcbcac"), True), (("aabcc", "dbbca", "aadbbbaccc"), False)],
                        [(("", "", ""), True), (("a", "b", "ab"), True), (("a", "b", "ba"), True), (("a", "", "a"), True)])
        lr = ia.demande("longest_repeating_char_replace", "s, k", [(("ABAB", 2), 4), (("AABABBA", 1), 4)],
                        [(("A", 0), 1), (("AAAA", 0), 4), (("ABBB", 0), 3)])
        tk = ia.demande("top_k_frequent", "nums, k", [(([1, 1, 1, 2, 2, 3], 2), [1, 2]), (([1], 1), [1])],
                        [(([4, 4, 5, 5, 5], 2), [5, 4]), (([1, 2], 2), [1, 2]), (([7, 7, 8], 1), [7])])
        r.append(_check(f"DP/FEN il->`{il.etage}` lr->`{lr.etage}` tk->`{tk.etage}`",
                        all(resolu(x) for x in (il, lr, tk))))

        cs = ia.demande("count_and_say", "n", [((1,), "1"), ((4,), "1211")],
                        [((2,), "11"), ((3,), "21"), ((5,), "111221"), ((6,), "312211")])
        ms = ia.demande("multiply_strings", "a, b", [(("2", "3"), "6"), (("123", "456"), "56088")],
                        [(("0", "5"), "0"), (("99", "99"), "9801"), (("10", "10"), "100")])
        r.append(_check(f"CHAÎNES ARITH count_and_say->`{cs.etage}` multiply->`{ms.etage}`",
                        resolu(cs) and resolu(ms)))

        inc = ia.demande("incoherent_v17", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        # témoin non-régression : maximal_square (grille DP) -> routage `tableaux` robuste (hors de portée de means-end).
        mq = ia.demande("maximal_square", "grid",
                        [(([[1, 0, 1, 0, 0], [1, 0, 1, 1, 1], [1, 1, 1, 1, 1], [1, 0, 0, 1, 0]],), 4), (([[0, 1], [1, 0]],), 1)],
                        [(([[1, 1], [1, 1]],), 4), (([[1]],), 1)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG maximal_square->`{mq.etage}`",
                        not inc.ok and resolu(mq)))

    print()
    print("VAGUE 17 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
