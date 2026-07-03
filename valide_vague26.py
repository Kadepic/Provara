"""
VAGUE 26 — tableaux / DP / pile / bits / chaîne (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par gap_probe_vague26
(7 vrais trous). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. TABLEAUX : plus_one + move_zeroes + find_pivot_index via `tableaux`.
  2. DP/PILE : min_falling_path_sum via `tableaux` ; remove_k_digits via `pile`.
  3. BITS/CHAÎNE + HORS : binary_gap via `bits` ; length_of_last_word via `chaines-avancees` ; incohérent -> HORS.
  4. NON-RÉG : third_max généralise.

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

        po = ia.demande("plus_one", "digits", [(([1, 2, 3],), [1, 2, 4]), (([9],), [1, 0])],
                        [(([1, 9, 9],), [2, 0, 0]), (([9, 9],), [1, 0, 0]), (([0],), [1])])
        mz = ia.demande("move_zeroes", "nums", [(([0, 1, 0, 3, 12],), [1, 3, 12, 0, 0]), (([0],), [0])],
                        [(([1, 2],), [1, 2]), (([0, 0, 1],), [1, 0, 0]), (([1, 0, 2, 0, 3],), [1, 2, 3, 0, 0])])
        fp = ia.demande("find_pivot_index", "nums", [(([1, 7, 3, 6, 5, 6],), 3), (([1, 2, 3],), -1)],
                        [(([2, 1, -1],), 0), (([1],), 0), (([0, 0, 0],), 0)])
        r.append(_check(f"TABLEAUX plus_one->`{po.etage}` move_zeroes->`{mz.etage}` pivot->`{fp.etage}` (==tableaux)",
                        all(resolu(x) for x in (po, mz, fp))))

        mf = ia.demande("min_falling_path_sum", "grid", [(([[2, 1, 3], [6, 5, 4], [7, 8, 9]],), 13), (([[7]],), 7)],
                        [(([[-19, 57], [-40, -5]],), -59), (([[1, 2], [3, 4]],), 4), (([[1], [2], [3]],), 6)])
        rk = ia.demande("remove_k_digits", "num, k", [(("1432219", 3), "1219"), (("10200", 1), "200")],
                        [(("10", 2), "0"), (("112", 1), "11"), (("1234", 1), "123")])
        r.append(_check(f"DP/PILE falling->`{mf.etage}`(==tableaux) remove_k->`{rk.etage}`(==pile)",
                        resolu(mf) and resolu(rk)))

        bg = ia.demande("binary_gap", "n", [((22,), 2), ((5,), 2)], [((8,), 0), ((6,), 1), ((1,), 0), ((3,), 1)])
        ll = ia.demande("length_of_last_word", "s", [(("Hello World",), 5), (("   fly me   ",), 2)],
                        [(("a",), 1), (("",), 0), (("word ",), 4), (("ab cd",), 2)])
        inc = ia.demande("incoherent_v26", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"BITS/CHAÎNE binary_gap->`{bg.etage}`(==bits) last_word->`{ll.etage}`(==chaines) | HORS ok={inc.ok}",
                        resolu(bg) and resolu(ll) and not inc.ok))

        tm = ia.demande("third_max", "nums", [(([3, 2, 1],), 1), (([1, 2],), 2)],
                        [(([2, 2, 3, 1],), 1), (([5],), 5), (([1, 2, 2, 5, 3, 5],), 2)])
        r.append(_check(f"NON-RÉG third_max->`{tm.etage}` (généralise={tm.generalise})", tm.ok and tm.generalise))

    print()
    print("VAGUE 26 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
