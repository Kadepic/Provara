"""
VAGUE 5 — chaînes / théorie des nombres / chiffres / matrices / tableaux (2026-06-19, autonomie). Lacunes MESURÉES
par gap_probe_vague5 (11 HORS). Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. CHAÎNES : is_rotation + all_indices + longest_palindrome_len via `chaines-avancees` + généralisent.
  2. NOMBRES/CHIFFRES : is_perfect_square + count_primes_below via `diviseurs`, is_armstrong via `chiffres`.
  3. TABLEAUX + MATRICES : house_robber/rotate_left/missing_number via `tableaux` ; rotate90/is_symmetric via `matrice`.
  4. HORS HONNÊTE + NON-RÉGRESSION : incohérent -> HORS ; transpose reste via `matrice`, anagramme via `chaines-avancees`.

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

        rot = ia.demande("is_rotation", "a, b", [(("abcde", "cdeab"), True), (("abc", "acb"), False)],
                         [(("", ""), True), (("waterbottle", "erbottlewat"), True), (("abc", "ab"), False)])
        ai = ia.demande("all_indices", "s, sub", [(("ababa", "aba"), [0, 2]), (("aaa", "a"), [0, 1, 2])],
                        [(("abc", "x"), []), (("xyxyx", "xyx"), [0, 2]), (("abba", "ab"), [0]), (("baab", "ab"), [2])])
        # held-out DURCI ("abba"->[0], "baab"->[2]) : sous-chaîne EXACTE ≠ fenêtre-anagramme -> bloque la coïncidence
        # Counter-window (qui donnerait [0,2]) ; force la vraie `toutes_occurrences` (chaines-avancees). Cf. norme anti-coïncidence.
        lp = ia.demande("longest_palindrome_len", "s", [(("babad",), 3), (("cbbd",), 2)],
                        [(("a",), 1), (("",), 0), (("abacdfgdcaba",), 3), (("aaaa",), 4)])
        r.append(_check(f"CHAÎNES rot->`{rot.etage}` | all_idx->`{ai.etage}` | palin->`{lp.etage}`",
                        all(resolu(x) for x in (rot, ai, lp))))

        ps = ia.demande("is_perfect_square", "n", [((16,), True), ((15,), False)],
                        [((0,), True), ((1,), True), ((144,), True), ((145,), False)])
        cp = ia.demande("count_primes_below", "n", [((10,), 4), ((2,), 0)], [((3,), 1), ((20,), 8), ((0,), 0)])
        arm = ia.demande("is_armstrong", "n", [((153,), True), ((154,), False)], [((9,), True), ((370,), True), ((100,), False)])
        r.append(_check(f"NOMBRES ps->`{ps.etage}` cp->`{cp.etage}` (==diviseurs) | armstrong->`{arm.etage}` (==chiffres)",
                        resolu(ps)
                        and resolu(cp)
                        and resolu(arm)))

        hr = ia.demande("house_robber", "xs", [(([2, 7, 9, 3, 1],), 12), (([1, 2, 3, 1],), 4)],
                        [(([],), 0), (([5],), 5), (([2, 1, 1, 2],), 4)])
        rl = ia.demande("rotate_left", "xs, k", [(([1, 2, 3, 4, 5], 2), [3, 4, 5, 1, 2]), (([1, 2, 3], 0), [1, 2, 3])],
                        [(([1, 2], 3), [2, 1]), (([5], 2), [5])])
        mn = ia.demande("missing_number", "xs", [(([0, 1, 3],), 2), (([0],), 1)],
                        [(([0, 1, 2, 3],), 4), (([1, 2],), 0), (([3, 0, 1],), 2)])
        # next_permutation = permutation lexicographique suivante in-place (gap_probe DUR 2026-06-24) ; déjà décroissante -> plus petite.
        npm = ia.demande("next_permutation", "a", [(([1, 2, 3],), [1, 3, 2]), (([3, 2, 1],), [1, 2, 3])],
                         [(([1, 1, 5],), [1, 5, 1]), (([1, 3, 2],), [2, 1, 3]), (([2, 3, 1],), [3, 1, 2])])
        r9 = ia.demande("rotate90", "m", [(([[1, 2], [3, 4]],), [[3, 1], [4, 2]])],
                        [(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [[7, 4, 1], [8, 5, 2], [9, 6, 3]]), (([[5]],), [[5]])])
        sy = ia.demande("is_symmetric", "m", [(([[1, 2], [2, 1]],), True), (([[1, 2], [3, 4]],), False)],
                        [(([[1]],), True), (([[1, 0, 0], [0, 2, 0], [0, 0, 3]],), True)])
        r.append(_check(f"TABLEAUX hr->`{hr.etage}` rl->`{rl.etage}` mn->`{mn.etage}` npm->`{npm.etage}` (==tableaux) | "
                        f"MATRICE r90->`{r9.etage}` sym->`{sy.etage}` (==matrice)",
                        all(resolu(x) for x in (hr, rl, mn, npm))
                        and resolu(r9)
                        and resolu(sy)))

        inc = ia.demande("incoherent_v5", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        tp = ia.demande("transpose", "m", [(([[1, 2], [3, 4]],), [[1, 3], [2, 4]]), (([[1, 2, 3]],), [[1], [2], [3]])],
                        [(([[1], [2]],), [[1, 2]]), (([[5, 6], [7, 8]],), [[5, 7], [6, 8]])])
        an = ia.demande("is_anagram", "a, b", [(("listen", "silent"), True), (("abc", "abd"), False)],
                        [(("", ""), True), (("aab", "aba"), True)])
        r.append(_check(f"HORS incoherent ok={inc.ok} | NON-RÉG transpose->`{tp.etage}` (==matrice) | anagram->`{an.etage}`",
                        not inc.ok and resolu(tp)
                        and resolu(an)))

    print()
    print("VAGUE 5 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
