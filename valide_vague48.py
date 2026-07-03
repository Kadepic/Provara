"""
VAGUE 48 — GREEDY / HACHAGE / CHAÎNES / BITS (CONFIRMATION, 0 trou) (2026-06-22 nuit, autonomie).
gap_probe_vague48 = 8 tâches TOUTES déjà couvertes ; AUCUN générateur modifié. COLD-RETEST DURCI.

LEÇON de cette vague (held-out durci = garde-fou anti-coïncidence prouvé EN ACTION) :
  • `majority_element` : un solveur means-end coïncident (5 cand.) classait 1er sur held faible ; held durci
    (majorité ni premier/dernier/min/max) l'a TUÉ -> le vrai solveur `statistiques` (mode/vote) reste -> correct.
  • `is_subsequence` : une solution ENSEMBLISTE (ignore l'ordre) passait ; cas « ordre violé mais ensemble OK »
    (aec/cba/bca -> False) l'a TUÉE -> le vrai solveur `chaines-avancees` (deux-pointeurs, ordre) reste -> correct.
  => le moteur AVAIT la bonne brique ; le held faible laissait une mauvaise ranker 1er. La soundness exigée ici
     est « résout & généralise sur held-out ADVERSE », pas l'étage exact (qui dépend du ranking) -> on n'épingle pas.

Critères de MORT (4) :
  1. VOTE/CYCLE/INDEX : majority_element + find_duplicate + first_missing_positive (held durci).
  2. GREEDY/FENÊTRE : candy + subarray_product_less_k.
  3. CHAÎNES/BITS : str_str + is_subsequence (held ordre-violé) + counting_bits.
  4. HORS HONNÊTE : incohérent -> HORS.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        # ---- 1. VOTE / CYCLE / INDEX (held durci) -----------------------------------------------------------
        me = ia.demande("majority_element", "nums", [(([3, 2, 3],), 3), (([2, 2, 1, 1, 1, 2, 2],), 2)],
                        [(([1],), 1), (([4, 4, 4, 4],), 4), (([5, 5, 6, 5],), 5),
                         (([1, 5, 5, 5, 9],), 5), (([9, 5, 5, 5, 1],), 5), (([2, 7, 2, 7, 2],), 2), (([8, 8, 1, 1, 8],), 8)])
        fd = ia.demande("find_duplicate", "nums", [(([1, 3, 4, 2, 2],), 2), (([3, 1, 3, 4, 2],), 3)],
                        [(([1, 1],), 1), (([2, 2, 2, 2],), 2), (([1, 2, 3, 4, 4],), 4)])
        fm = ia.demande("first_missing_positive", "nums", [(([1, 2, 0],), 3), (([3, 4, -1, 1],), 2)],
                        [(([7, 8, 9, 11, 12],), 1), (([1, 2, 3],), 4), (([],), 1),
                         (([2, 3, 4],), 1), (([1, 2, 3, 4, 5],), 6), (([1, 3, 4],), 2), (([-5, -3],), 1), (([2, 1],), 3)])
        r.append(_check(f"VOTE/CYCLE/INDEX majority->`{me.etage}` find_dup->`{fd.etage}` first_missing->`{fm.etage}`",
                        all(x.ok and x.generalise for x in (me, fd, fm))))

        # ---- 2. GREEDY / FENÊTRE ----------------------------------------------------------------------------
        cy = ia.demande("candy", "ratings", [(([1, 0, 2],), 5), (([1, 2, 2],), 4)],
                        [(([1, 3, 2, 2, 1],), 7), (([5],), 1), (([1, 2, 3, 4],), 10), (([4, 3, 2, 1],), 10)])
        sp = ia.demande("subarray_product_less_k", "nums, k", [(([10, 5, 2, 6], 100), 8), (([1, 2, 3], 0), 0)],
                        [(([1, 1, 1], 2), 6), (([10], 5), 0), (([2, 3, 4], 50), 6), (([10, 5, 2, 6], 100), 8)])
        r.append(_check(f"GREEDY/FENÊTRE candy->`{cy.etage}` subarray_product->`{sp.etage}`",
                        all(x.ok and x.generalise for x in (cy, sp))))

        # ---- 3. CHAÎNES / BITS (is_subsequence held ORDRE-VIOLÉ) --------------------------------------------
        ss = ia.demande("str_str", "haystack, needle", [(("hello", "ll"), 2), (("aaaaa", "bba"), -1)],
                        [(("abc", ""), 0), (("mississippi", "issip"), 4), (("a", "a"), 0), (("ababab", "bab"), 1)])
        isq = ia.demande("is_subsequence", "s, t", [(("abc", "ahbgdc"), True), (("axc", "ahbgdc"), False)],
                         [(("", "abc"), True), (("abc", ""), False), (("ace", "abcde"), True),
                          (("aec", "abcde"), False), (("cba", "abc"), False), (("bca", "abcde"), False),
                          (("aaa", "aabaa"), True), (("xyz", "xyz"), True)])
        cb = ia.demande("counting_bits", "n", [((2,), [0, 1, 1]), ((5,), [0, 1, 1, 2, 1, 2])],
                        [((0,), [0]), ((8,), [0, 1, 1, 2, 1, 2, 2, 3, 1]), ((1,), [0, 1])])
        r.append(_check(f"CHAÎNES/BITS str_str->`{ss.etage}` is_subseq->`{isq.etage}` counting_bits->`{cb.etage}`",
                        all(x.ok and x.generalise for x in (ss, isq, cb))))

        # ---- 4. HORS HONNÊTE -------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v48", "nums", [(([1],), 42)], [(([2],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 48 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
