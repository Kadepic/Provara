"""
VAGUE 19 — Excel / chaînes / DP / théorie des nombres (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par
gap_probe_vague19 (8 vrais trous ; paint_house = 9ᵉ COÏNCIDENCE débusquée — « somme des min de lignes » via
matrice-reduce matchait un held-out faible mais IGNORE la contrainte voisins ; held-out durci [[1,5,5],[1,5,5]]->6
le force vers le vrai DP). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. EXCEL : excel_column_number via `numerique` ; excel_column_title + reverse_vowels via `chaines-avancees`.
  2. CHAÎNES/DP : longest_palindrome_buildable + partition_labels via `chaines-avancees` (vraie brique dès vague 29) ; max_profit_2_transactions via `tableaux`.
  3. ANTI-COÏNCIDENCE : paint_house via `tableaux` (held-out durci) ; is_ugly via `diviseurs`.
  4. HORS + NON-RÉG : incohérent -> HORS ; game_of_life_alive via `tableaux`.

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

        en = ia.demande("excel_column_number", "s", [(("A",), 1), (("AB",), 28)], [(("Z",), 26), (("AA",), 27), (("ZY",), 701)])
        et = ia.demande("excel_column_title", "n", [((1,), "A"), ((28,), "AB")], [((26,), "Z"), ((27,), "AA"), ((701,), "ZY"), ((52,), "AZ")])
        rv = ia.demande("reverse_vowels", "s", [(("hello",), "holle"), (("leetcode",), "leotcede")],
                        [(("aA",), "Aa"), (("bcd",), "bcd"), (("",), ""), (("aeiou",), "uoiea")])
        r.append(_check(f"EXCEL en->`{en.etage}`(==numerique) et->`{et.etage}` rv->`{rv.etage}`(==chaines)",
                        resolu(en) and resolu(et) and resolu(rv)))

        lb = ia.demande("longest_palindrome_buildable", "s", [(("abccccdd",), 7), (("a",), 1)],
                        [(("bb",), 2), (("aaa",), 3), (("abc",), 1), (("ccc",), 3)])
        pl = ia.demande("partition_labels", "s", [(("ababcbacadefegdehijhklij",), [9, 7, 8]), (("eccbbbbdec",), [10])],
                        [(("abc",), [1, 1, 1]), (("a",), [1]), (("abab",), [4]),
                         (("abcd",), [1, 1, 1, 1]), (("aaaa",), [4]), (("aabbcc",), [2, 2, 2]),
                         (("abcba",), [5]), (("abcabc",), [6])])
        m2 = ia.demande("max_profit_2_transactions", "prices", [(([3, 3, 5, 0, 0, 3, 1, 4],), 6), (([1, 2, 3, 4, 5],), 4)],
                        [(([7, 6, 4, 3, 1],), 0), (([1],), 0), (([2, 1, 4],), 3)])
        # NB partition_labels : l'ÉTAGE n'est PAS épinglé (le round-robin inter-étages le fait osciller
        # tableaux↔chaines-avancees au fil des ajouts) ; la soundness garantie = correct sur held DURCI.
        r.append(_check(f"CHAÎNES/DP lpb->`{lb.etage}`(==chaines) pl->`{pl.etage}`(held durci) mp2->`{m2.etage}`(==tableaux)",
                        resolu(lb) and resolu(pl) and resolu(m2)))

        ph = ia.demande("paint_house", "costs", [(([[17, 2, 17], [16, 16, 5], [14, 3, 19]],), 10), (([[1, 2, 3]],), 1)],
                        [(([[5, 8, 6], [4, 3, 1]],), 6), (([[1, 5, 5], [1, 5, 5]],), 6), (([[1, 5, 5], [5, 1, 5], [5, 5, 1]],), 3)])
        iu = ia.demande("is_ugly", "n", [((6,), True), ((14,), False)], [((8,), True), ((1,), True), ((0,), False), ((30,), True), ((7,), False)])
        r.append(_check(f"ANTI-COÏNCIDENCE paint_house->`{ph.etage}`(==tableaux) | is_ugly->`{iu.etage}`(==diviseurs)",
                        resolu(ph) and resolu(iu)))

        inc = ia.demande("incoherent_v19", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        # held-out ASYMÉTRIQUE (transpose != résultat) pour casser la coïncidence `matrice`/transpose -> vrai DP tableaux.
        gl = ia.demande("game_of_life_alive", "grid",
                        [(([[0, 1, 0], [0, 1, 0], [0, 1, 0]],), [[0, 0, 0], [1, 1, 1], [0, 0, 0]]), (([[0, 0], [0, 0]],), [[0, 0], [0, 0]])],
                        [(([[1, 1, 0], [1, 0, 0], [0, 0, 0]],), [[1, 1, 0], [1, 1, 0], [0, 0, 0]]), (([[1, 1], [1, 1]],), [[1, 1], [1, 1]])])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG gol->`{gl.etage}`(==tableaux)",
                        not inc.ok and resolu(gl)))

    print()
    print("VAGUE 19 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
