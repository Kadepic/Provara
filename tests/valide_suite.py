"""
BRIQUE SUITES & MOTIFS (2026-06-19) — GenerateurSuite : tribonacci (récurrence ordre 3), is_arithmetic (différences
consécutives constantes). Lacunes MESURÉES par gap_probe 3ᵉ vague (HORS avant ; `recurrence` est figé à 2 états).
Validée dans le MOTEUR COMPLET.

Critères de MORT (4) :
  1. TRIBONACCI : résolu via `suite` + généralise (held-out adverse).
  2. IS_ARITHMETIC : résolu via `suite` + généralise (held-out adverse).
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : lucas (ordre 2, étage `recurrence`) reste résolu hors `suite`.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurSuite
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        tr = ia.demande("tribonacci", "n", [((4,), 2), ((5,), 4)], [((0,), 0), ((2,), 1), ((6,), 7), ((9,), 44)])
        r.append(_check(f"TRIBONACCI -> `{tr.etage}` ({tr.appels} cand.), gen={tr.generalise}",
                        resolu(tr)))

        ar = ia.demande("is_arithmetic", "xs", [(([1, 3, 5],), True), (([1, 2, 4],), False)],
                        [(([5, 5, 5],), True), (([10, 7, 4],), True), (([1],), True), (([2, 4, 6, 9],), False)])
        r.append(_check(f"IS_ARITHMETIC -> `{ar.etage}` ({ar.appels} cand.), gen={ar.generalise}",
                        resolu(ar)))

        inc = ia.demande("incoherent_suite", "n", [((3,), 7), ((4,), 7)], [((5,), 8), ((6,), 9)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        lu = ia.demande("lucas", "n", [((2,), 3), ((5,), 11)], [((0,), 2), ((1,), 1), ((6,), 18)])
        r.append(_check(f"NON-RÉGRESSION : lucas -> `{lu.etage}` ok={lu.ok}, gen={lu.generalise} (!= suite)",
                        resolu(lu)))

        # VIVACITÉ (anti-code-mort) : la brique spécialiste `suite` résout SA tâche canonique tribonacci en
        # DIRECT (hors routeur) sur tests + held-out adverse — remplace le rôle du pin d'étage.
        r.append(_check("VIVACITÉ : la brique `suite` résout tribonacci en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurSuite(), "tribonacci", "n",
                                       "def check(c):\n    assert c(4)==2\n    assert c(5)==4\ncheck(tribonacci)",
                                       "def check(c):\n    assert c(0)==0\n    assert c(2)==1\n    assert c(6)==7\n    assert c(9)==44\ncheck(tribonacci)")))

    print()
    print(f"BRIQUE SUITES VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
