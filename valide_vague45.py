"""
VAGUE 45 — ALGORITHMES À PILE (monotone & parsing) (2026-06-22 nuit, autonomie). gap_probe_vague45 = 8 tâches.
4 VRAIS TROUS bâtis + 4 confirmées (templates pile déjà présents, re-testés À FROID sur held-out durci).

Bâtis cette vague (-> `GenerateurPile.PILE`) :
  • `asteroid_collision`  — simulation à pile (signe=direction, |val|=taille).
  • `simplify_path`       — chemins Unix (.. remonte, . ignore) via pile de segments.
  • `score_parentheses`   — score de parenthésage imbriqué via pile d'accumulateurs.
  • `min_add_valid`       — ajouts minimaux pour un parenthésage valide.
Confirmées À FROID (held-out durci) : largest_rectangle, next_greater, daily_temperatures, decode_string (imbriqué).

Critères de MORT (4) :
  1. PILE MONOTONE : largest_rectangle + next_greater + daily_temperatures via `pile`.
  2. PARSING À PILE : decode_string (imbriqué) + simplify_path via `pile`.
  3. SCORING/SIMULATION : score_parentheses + asteroid_collision + min_add_valid via `pile`.
  4. HORS HONNÊTE : incohérent -> HORS.

SÉQUENTIEL + garde (ulimit -v 1.5 Go).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurPile
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        # ---- 1. PILE MONOTONE --------------------------------------------------------------------------------
        lr = ia.demande("largest_rectangle", "heights",
                        [(([2, 1, 5, 6, 2, 3],), 10), (([2, 4],), 4)],
                        [(([1, 1, 1],), 3), (([5],), 5), (([6, 2, 5, 4, 5, 1, 6],), 12), (([2, 1, 2],), 3)])
        ng = ia.demande("next_greater", "nums",
                        [(([2, 1, 2, 4, 3],), [4, 2, 4, -1, -1]), (([1, 2, 3],), [2, 3, -1])],
                        [(([3, 2, 1],), [-1, -1, -1]), (([5],), [-1]), (([1, 3, 2, 4],), [3, 4, 4, -1])])
        dt = ia.demande("daily_temperatures", "t",
                        [(([73, 74, 75, 71, 69, 72, 76, 73],), [1, 1, 4, 2, 1, 1, 0, 0]), (([30, 40, 50, 60],), [1, 1, 1, 0])],
                        [(([30, 60, 90],), [1, 1, 0]), (([90, 80, 70],), [0, 0, 0])])
        r.append(_check(f"PILE MONOTONE largest_rectangle->`{lr.etage}` next_greater->`{ng.etage}` daily->`{dt.etage}` (==pile)",
                        all(resolu(x) for x in (lr, ng, dt))))

        # ---- 2. PARSING À PILE -------------------------------------------------------------------------------
        ds = ia.demande("decode_string", "s",
                        [(("3[a]",), "aaa"), (("3[a]2[bc]",), "aaabcbc")],
                        [(("2[abc]3[cd]ef",), "abcabccdcdcdef"), (("abc",), "abc"), (("2[a3[b]]",), "abbbabbb")])
        sp = ia.demande("simplify_path", "p",
                        [(("/home/",), "/home"), (("/../",), "/")],
                        [(("/a/./b/../../c/",), "/c"), (("/a//b",), "/a/b"), (("/",), "/"),
                         (("/...",), "/..."), (("/a/../../b",), "/b")])
        r.append(_check(f"PARSING decode_string->`{ds.etage}` simplify_path->`{sp.etage}` (==pile)",
                        all(resolu(x) for x in (ds, sp))))

        # ---- 3. SCORING / SIMULATION -------------------------------------------------------------------------
        sc = ia.demande("score_parentheses", "s",
                        [(("()",), 1), (("(())",), 2)],
                        [(("()()",), 2), (("(()(()))",), 6), (("((()))",), 4), (("()(())",), 3)])
        ac = ia.demande("asteroid_collision", "a",
                        [(([5, 10, -5],), [5, 10]), (([8, -8],), [])],
                        [(([10, 2, -5],), [10]), (([-2, -1, 1, 2],), [-2, -1, 1, 2]), (([1, -2],), [-2]),
                         (([10, -10, 10, -5],), [10]), (([-5, 5],), [-5, 5])])
        mav = ia.demande("min_add_valid", "s",
                         [(("())",), 1), (("(((",), 3)],
                         [(("()",), 0), (("()))((",), 4), (("",), 0), ((")(",), 2)])
        r.append(_check(f"SCORING/SIM score->`{sc.etage}` asteroid->`{ac.etage}` min_add->`{mav.etage}` (==pile)",
                        all(resolu(x) for x in (sc, ac, mav))))

        # ---- 4. HORS HONNÊTE ---------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v45", "s", [(("a",), 42)], [(("b",), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        # ---- 5. VIVACITÉ (anti-code-mort) --------------------------------------------------------------------
        # La brique spécialiste `pile` résout SA tâche canonique largest_rectangle en DIRECT (hors routeur)
        # sur tests + held-out adverse — remplace le rôle du pin d'étage.
        r.append(_check("VIVACITÉ : la brique `pile` résout largest_rectangle en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurPile(), "largest_rectangle", "heights",
                                       "def check(c):\n    assert c([2,1,5,6,2,3])==10\n    assert c([2,4])==4\ncheck(largest_rectangle)",
                                       "def check(c):\n    assert c([1,1,1])==3\n    assert c([5])==5\n    assert c([6,2,5,4,5,1,6])==12\n    assert c([2,1,2])==3\ncheck(largest_rectangle)")))

    print()
    print(f"VAGUE 45 VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
