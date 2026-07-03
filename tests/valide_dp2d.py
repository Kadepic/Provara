"""
BRIQUE DP 2D / PROGRAMMATION DYNAMIQUE SUR DEUX SÉQUENCES (2026-06-19) — table dp[m+1][n+1] par récurrence
(diagonale/haut/gauche). Lacune MESURÉE par gap_probe (lcs_len, edit_distance — le plus dur : état 2D). Validée
dans le MOTEUR COMPLET (intégré).

Critères de MORT (4) :
  1. LCS_LEN : résolu via `dp2d` + généralise (held-out adverse — axes init=0, match=+1, sinon=max).
  2. EDIT_DISTANCE : résolu via `dp2d` + généralise (held-out adverse — axes init=index, match=copie, sinon=1+min).
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : une tâche d'un autre étage (somme_carres) reste résolue.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurDP2D
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        lcs = ia.demande("lcs_len", "a, b", [(("abcde", "ace"), 3), (("abc", "def"), 0)],
                         [(("aggtab", "gxtxayb"), 4), (("", "x"), 0), (("aaaa", "aa"), 2)])
        r.append(_check(f"LCS_LEN -> `{lcs.etage}` ({lcs.appels} cand.), généralise={lcs.generalise}",
                        resolu(lcs)))

        ed = ia.demande("edit_distance", "a, b", [(("kitten", "sitting"), 3), (("abc", "abc"), 0)],
                        [(("", "abc"), 3), (("ab", "ba"), 2), (("flaw", "lawn"), 2)])
        r.append(_check(f"EDIT_DISTANCE -> `{ed.etage}` ({ed.appels} cand.), généralise={ed.generalise}",
                        resolu(ed)))

        inc = ia.demande("incoherent", "a, b", [(("a", "b"), 42)], [(("c", "d"), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        sc = ia.demande("somme_carres", "xs", [(([1, 2, 3],), 14), (([2, 3],), 13)], [(([5],), 25), (([0, 4],), 16)])
        r.append(_check(f"NON-RÉGRESSION : somme_carres -> `{sc.etage}` résolu={sc.ok}, généralise={sc.generalise}",
                        resolu(sc)))

        r.append(_check("VIVACITÉ : la brique `dp2d` résout lcs_len en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurDP2D(), "lcs_len", "a, b",
                                       "def check(c):\n    assert c('abcde','ace')==3\n    assert c('abc','def')==0\ncheck(lcs_len)",
                                       "def check(c):\n    assert c('aggtab','gxtxayb')==4\n    assert c('','x')==0\n    assert c('aaaa','aa')==2\ncheck(lcs_len)")))

    print()
    print(f"BRIQUE DP 2D VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
