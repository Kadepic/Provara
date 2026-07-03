"""
VAGUE 40 — listes in-place / statistique d'ordre / greedy / chaînes (2026-06-20, reprise post-redémarrage, 1.5 Go).
gap_probe_vague40 = 8 tâches : 2 vrais trous bâtis (third_max via `statistiques` = 3ᵉ max distinct sinon max ;
can_place_flowers via `tableaux` = greedy bords vides) + 6 déjà couvertes réelles (move_zeroes, plus_one,
find_pivot_index->tableaux ; add_digits->iteration ; length_of_last_word, reverse_vowels->chaines-avancees).
Held-out ADVERSE frais, pré-vérifiés par référence pure (2 bugs de test attrapés : third_max([2,2,1])=2, [9,9,8,7]=7).

Critères de MORT (4) :
  1. BÂTIS : third_max via `statistiques` ; can_place_flowers via `tableaux`.
  2. TABLEAUX RÉELS : move_zeroes + plus_one + find_pivot_index via `tableaux`.
  3. NOMBRES/CHAÎNES RÉELS : add_digits via `iteration` ; length_of_last_word + reverse_vowels via `chaines-avancees`.
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

        # ---- 1. BÂTIS ------------------------------------------------------------------------------------------
        tm = ia.demande("third_max", "nums", [(([3, 2, 1],), 1), (([1, 2],), 2)],
                        [(([10, 5, 7, 7, 3],), 5), (([-1, -2, -3],), -3), (([2, 2, 1],), 2),
                         (([9, 9, 8, 7],), 7), (([0, 0, 0, 0],), 0)])
        cp = ia.demande("can_place_flowers", "flowerbed, n",
                        [(([1, 0, 0, 0, 1], 1), True), (([1, 0, 0, 0, 1], 2), False)],
                        [(([0, 0, 1, 0, 0], 2), True), (([1, 0, 0, 0, 0, 1], 1), True),
                         (([0, 0, 0, 0, 0], 3), True), (([1, 0, 0, 0, 1], 0), True), (([0, 1, 0], 1), False)])
        r.append(_check(f"BÂTIS third_max->`{tm.etage}` can_place->`{cp.etage}` (résolu, étage libre)",
                        resolu(tm) and resolu(cp)))

        # ---- 2. TABLEAUX RÉELS ---------------------------------------------------------------------------------
        mz = ia.demande("move_zeroes", "nums", [(([0, 1, 0, 3, 12],), [1, 3, 12, 0, 0]), (([0],), [0])],
                        [(([1, 0],), [1, 0]), (([0, 0, 1],), [1, 0, 0]), (([1, 2, 3],), [1, 2, 3]), (([0, 0],), [0, 0])])
        po = ia.demande("plus_one", "digits", [(([1, 2, 3],), [1, 2, 4]), (([9],), [1, 0])],
                        [(([1, 9],), [2, 0]), (([9, 9],), [1, 0, 0]), (([4, 3, 2, 1],), [4, 3, 2, 2]), (([0],), [1])])
        pv = ia.demande("find_pivot_index", "nums", [(([1, 7, 3, 6, 5, 6],), 3), (([1, 2, 3],), -1)],
                        [(([2, 1, -1],), 0), (([1],), 0), (([0, 0, 0],), 0), (([1, 2, 3, 4],), -1)])
        r.append(_check(f"TABLEAUX move_zeroes->`{mz.etage}` plus_one->`{po.etage}` pivot->`{pv.etage}` (résolu, étage libre)",
                        all(resolu(x) for x in (mz, po, pv))))

        # ---- 3. NOMBRES / CHAÎNES RÉELS ------------------------------------------------------------------------
        ad = ia.demande("add_digits", "num", [((38,), 2), ((0,), 0)],
                        [((9,), 9), ((199,), 1), ((10,), 1), ((99,), 9)])
        ll = ia.demande("length_of_last_word", "s", [(("Hello World",), 5), (("   fly me   ",), 2)],
                        [(("a",), 1), (("day",), 3), (("x y z",), 1), (("hello",), 5)])
        rv = ia.demande("reverse_vowels", "s", [(("hello",), "holle"), (("leetcode",), "leotcede")],
                        [(("aA",), "Aa"), (("bcd",), "bcd"), (("race",), "reca"), (("Ohe",), "ehO")])
        r.append(_check(f"NOMBRES/CHAÎNES add_digits->`{ad.etage}` last_word->`{ll.etage}` rev_vowels->`{rv.etage}` (résolu, étage libre)",
                        resolu(ad) and resolu(ll) and resolu(rv)))

        # ---- 4. HORS HONNÊTE -----------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v40", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 40 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
