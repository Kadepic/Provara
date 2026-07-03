"""
VAGUE 28 — tableaux / unique / stats / numération (2026-06-20, nuit, 1.5 Go). gap_probe_vague28 = 8 tâches : 2 vrais
trous bâtis (h_index, first_missing_positive via `tableaux`) + 6 DÉJÀ couvertes, CONFIRMÉES RÉELLES par cold-retest
durci (single_number_ii->premier-unique, find_duplicate->statistiques, happy_number->diviseurs,
excel_column_title->chaines-avancees, roman_to_int->conversion, summary_ranges->tableaux). Held-out ADVERSE frais.

Critères de MORT (4) :
  1. TABLEAUX (neuf+couvert) : h_index + first_missing_positive + summary_ranges via `tableaux`.
  2. UNIQUE/STATS (non-coïncidence) : single_number_ii via `premier-unique` ; find_duplicate via `statistiques`.
  3. NUMÉRATION (non-coïncidence) : happy_number via `diviseurs` ; excel_column_title via `chaines-avancees` ;
     roman_to_int via `conversion`.
  4. HORS HONNÊTE : incohérent -> HORS.

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

        hi = ia.demande("h_index", "citations", [(([3, 0, 6, 1, 5],), 3), (([1, 3, 1],), 1)],
                        [(([0],), 0), (([100],), 1), (([4, 4, 4, 4],), 4), (([10, 8, 5, 3, 1],), 3),
                         (([25, 8, 5, 3, 3],), 3), (([6, 6, 6, 6, 6, 6],), 6)])  # durci : force le vrai tri (tableaux), bloque la coïncidence means-end
        fm = ia.demande("first_missing_positive", "nums", [(([1, 2, 0],), 3), (([3, 4, -1, 1],), 2)],
                        [(([2, 3, 4],), 1), (([1, 2, 3, 4, 5],), 6), (([-1, -2],), 1), (([1, 3],), 2)])
        sr = ia.demande("summary_ranges", "nums",
                        [(([0, 1, 2, 4, 5, 7],), ["0->2", "4->5", "7"]), (([0, 2, 3, 4, 6, 8, 9],), ["0", "2->4", "6", "8->9"])],
                        [(([5],), ["5"]), (([1, 2, 3, 4],), ["1->4"]), (([0, 2, 4],), ["0", "2", "4"]), (([],), [])])
        r.append(_check(f"TABLEAUX h_index->`{hi.etage}` first_missing->`{fm.etage}` summary->`{sr.etage}` (==tableaux)",
                        all(resolu(x) for x in (hi, fm, sr))))

        sn = ia.demande("single_number_ii", "nums", [(([2, 2, 3, 2],), 3), (([0, 1, 0, 1, 0, 1, 99],), 99)],
                        [(([9, 9, 9, 4],), 4), (([1, 1, 1, 7, 7, 7, 2],), 2), (([-3, -3, -3, 8],), 8)])
        fd = ia.demande("find_duplicate", "nums", [(([1, 3, 4, 2, 2],), 2), (([3, 1, 3, 4, 2],), 3)],
                        [(([1, 1],), 1), (([3, 2, 3, 1],), 3), (([1, 5, 2, 5, 3, 4],), 5)])
        r.append(_check(f"UNIQUE/STATS single->`{sn.etage}`(==premier-unique) find_dup->`{fd.etage}`(==statistiques)",
                        resolu(sn) and resolu(fd)))

        hp = ia.demande("happy_number", "n", [((19,), True), ((2,), False)],
                        [((7,), True), ((10,), True), ((4,), False), ((20,), False), ((13,), True)])
        ec = ia.demande("excel_column_title", "n", [((1,), "A"), ((28,), "AB")],
                        [((26,), "Z"), ((27,), "AA"), ((701,), "ZY")])
        ro = ia.demande("roman_to_int", "s", [(("III",), 3), (("MCMXCIV",), 1994)],
                        [(("IX",), 9), (("LVIII",), 58), (("XL",), 40), (("MMXXIII",), 2023)])
        r.append(_check(f"NUMÉRATION happy->`{hp.etage}`(==diviseurs) excel->`{ec.etage}`(==chaines) roman->`{ro.etage}`(==conversion)",
                        resolu(hp) and resolu(ec) and resolu(ro)))

        inc = ia.demande("incoherent_v28", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 28 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
