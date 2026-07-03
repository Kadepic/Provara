"""
VAGUE 20 — dénombrement / numération / chaîne (2026-06-20, nuit, 1.5 Go). Lacunes MESURÉES par gap_probe_vague20
(3 vrais trous ; 5 déjà couverts dont search_sorted_matrix=membership via graphe). Validées dans le MOTEUR COMPLET.

Critères de MORT (4) :
  1. DP/NUMÉRATION : subset_sum_exists via `comptage-combinatoire` ; digit_sum_base via `conversion`.
  2. CHAÎNE : longest_alternating_binary via `chaines-avancees` ; run_length_encode via `run-length`.
  3. HORS : incohérent -> HORS.
  4. NON-RÉG : rotate_90_clockwise via `matrice`, count_set_bits_int via `bits`.

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

        ss = ia.demande("subset_sum_exists", "nums, target", [(([1, 2, 3], 5), True), (([1, 2, 3], 7), False)],
                        [(([2, 4, 6], 5), False), (([5], 5), True), (([], 0), True), (([3, 34, 4, 12, 5, 2], 9), True)])
        db = ia.demande("digit_sum_base", "n, b", [((10, 2), 2), ((255, 16), 30)],
                        [((0, 10), 0), ((7, 2), 3), ((100, 10), 1), ((8, 8), 1)])
        r.append(_check(f"DP/NUM subset->`{ss.etage}` dsb->`{db.etage}` (résolu, étage libre)",
                        resolu(ss) and resolu(db)))

        la = ia.demande("longest_alternating_binary", "s", [(("010101",), 6), (("0011",), 2)],
                        [(("1",), 1), (("",), 0), (("0101001",), 5), (("111",), 1)])
        re = ia.demande("run_length_encode", "s", [(("aaabbc",), "a3b2c1"), (("abc",), "a1b1c1")],
                        [(("",), ""), (("a",), "a1"), (("aaaa",), "a4"), (("aabbaa",), "a2b2a2")])
        r.append(_check(f"CHAÎNE lab->`{la.etage}` rle->`{re.etage}` (résolu, étage libre)",
                        resolu(la) and resolu(re)))

        inc = ia.demande("incoherent_v20", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS incoherent ok={inc.ok}", not inc.ok))

        ro = ia.demande("rotate_90_clockwise", "m", [(([[1, 2], [3, 4]],), [[3, 1], [4, 2]]), (([[1]],), [[1]])],
                        [(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [[7, 4, 1], [8, 5, 2], [9, 6, 3]])])
        cb = ia.demande("count_set_bits_int", "n", [((7,), 3), ((8,), 1)], [((0,), 0), ((255,), 8), ((1023,), 10)])
        r.append(_check(f"NON-RÉG rotate->`{ro.etage}` popcount->`{cb.etage}` (résolu, étage libre)",
                        resolu(ro) and resolu(cb)))

    print()
    print("VAGUE 20 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
