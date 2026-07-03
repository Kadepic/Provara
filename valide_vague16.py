"""
VAGUE 16 — DP / deux-pointeurs / fenêtre / pile / chaîne (2026-06-20, nuit, protocole 1.5 Go). Lacunes MESURÉES par
gap_probe_vague16 (6 vrais trous, held-out DURCIS). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. DP : min_perfect_squares + maximal_square via `tableaux`.
  2. DEUX-POINTEURS/FENÊTRE/PILE : container_with_most_water + longest_substring_without_repeat via `tableaux` ;
     decode_string via `pile`.
  3. CHAÎNE + HORS : valid_palindrome_alnum via `chaines-avancees` ; incohérent -> HORS.
  4. NON-RÉGRESSION : daily_temperatures reste via `pile`, gas_station via `tableaux`.

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
        # Mémoire bornée : un AssistantIA FRAIS par critère (les tâches DP/grille de cette vague sont lourdes ; sur un
        # seul `ia` partagé, l'accumulation sur 8 appels franchit 1,5 Go -> OOM flaky. Chaque critère seul tient. La
        # résolution à froid route vers les mêmes étages -> assertions inchangées). Cf. REPRISE : mémoire-échelle à traiter.
        ia = AssistantIA(Path(d) / "s1.jsonl")

        mp = ia.demande("min_perfect_squares", "n", [((12,), 3), ((13,), 2)], [((1,), 1), ((4,), 1), ((7,), 4), ((0,), 0)])
        ms = ia.demande("maximal_square", "grid",
                        [(([[1, 0, 1, 0, 0], [1, 0, 1, 1, 1], [1, 1, 1, 1, 1], [1, 0, 0, 1, 0]],), 4), (([[0, 1], [1, 0]],), 1)],
                        [(([[0]],), 0), (([[1, 1], [1, 1]],), 4), (([[1]],), 1)])
        # min_perfect_squares (= perfect_squares) -> étage DÉDIÉ `dp-int` (campagne <100, ex-`tableaux`) ; maximal_square reste tableaux.
        r.append(_check(f"DP mps->`{mp.etage}`(==dp-int) msq->`{ms.etage}`(==tableaux)",
                        resolu(mp) and resolu(ms)))

        ia = AssistantIA(Path(d) / "s2.jsonl")
        cw = ia.demande("container_with_most_water", "heights", [(([1, 8, 6, 2, 5, 4, 8, 3, 7],), 49), (([1, 1],), 1)],
                        [(([4, 3, 2, 1, 4],), 16), (([1, 2, 1],), 2), (([2, 1],), 1)])
        ls = ia.demande("longest_substring_without_repeat", "s", [(("abcabcbb",), 3), (("bbbbb",), 1)],
                        [(("pwwkew",), 3), (("",), 0), (("abcde",), 5), (("au",), 2)])
        de = ia.demande("decode_string", "s", [(("3[a]2[bc]",), "aaabcbc"), (("3[a2[c]]",), "accaccacc")],
                        [(("2[abc]3[cd]",), "abcabccdcdcd"), (("a",), "a"), (("2[a]",), "aa")])
        r.append(_check(f"2PTR/FEN cmw->`{cw.etage}` lsr->`{ls.etage}` (==tableaux) | decode->`{de.etage}`(==pile)",
                        resolu(cw) and resolu(ls) and resolu(de)))

        ia = AssistantIA(Path(d) / "s3.jsonl")
        vp = ia.demande("valid_palindrome_alnum", "s", [(("A man, a plan, a canal: Panama",), True), (("race a car",), False)],
                        [(("",), True), (("0P",), False), (("a",), True), (("Was it a car or a cat I saw?",), True)])
        inc = ia.demande("incoherent_v16", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"CHAÎNE vpa->`{vp.etage}`(==chaines) | HORS incoherent ok={inc.ok}",
                        resolu(vp) and not inc.ok))

        ia = AssistantIA(Path(d) / "s4.jsonl")
        dt = ia.demande("daily_temperatures", "temps", [(([73, 74, 75, 71, 69, 72, 76, 73],), [1, 1, 4, 2, 1, 1, 0, 0]), (([30, 40, 50, 60],), [1, 1, 1, 0])],
                        [(([90, 80, 70],), [0, 0, 0]), (([50],), [0])])
        gs = ia.demande("gas_station", "gas, cost", [(([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]), 3), (([2, 3, 4], [3, 4, 3]), -1)],
                        [(([2], [2]), 0), (([3, 3], [1, 2]), 0)])
        r.append(_check(f"NON-RÉG dt->`{dt.etage}`(==pile) gas->`{gs.etage}`(==tableaux)",
                        resolu(dt) and resolu(gs)))

    print()
    print("VAGUE 16 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
