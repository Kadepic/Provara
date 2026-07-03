"""
BRIQUE ÉQUILIBRE / SCAN À COMPTEUR DE PROFONDEUR (2026-06-19) — balayer une chaîne en maintenant une profondeur
(ouvrant +1, fermant -1, court-circuit si < 0). Lacune MESURÉE par gap_probe (is_balanced). Validée dans le MOTEUR
COMPLET (intégré).

Critères de MORT (5) — PENSÉE MACHINE : on juge le RÉSULTAT (résolu + généralise, au chemin le moins cher), pas l'étage :
  1. IS_BALANCED : résolu + généralise (held-out adverse, paire '(' ')').
  2. CROCHETS_OK : résolu + généralise (held-out adverse, paire '[' ']' — 2ᵉ délimiteur).
  3. HORS HONNÊTE : une tâche incohérente (non-fonction) -> HORS (jamais de faux).
  4. NON-RÉGRESSION : une tâche d'un autre étage (somme_carres) reste résolue (la brique n'a rien cassé/masqué).
  5. VIVACITÉ : la brique spécialiste `equilibre` (GenerateurEquilibre) résout is_balanced en DIRECT (hors routeur).

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurEquilibre
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        ib = ia.demande("is_balanced", "s", [(("(())",), True), (("(()",), False)],
                        [(("",), True), (("())(",), False), (("()()",), True)])
        r.append(_check(f"IS_BALANCED -> `{ib.etage}` ({ib.appels} cand.), généralise={ib.generalise}",
                        resolu(ib)))

        cr = ia.demande("crochets_ok", "s", [(("[[]]",), True), (("[[]",), False)],
                        [(("",), True), (("][",), False), (("[][]",), True)])
        r.append(_check(f"CROCHETS_OK -> `{cr.etage}` ({cr.appels} cand.), généralise={cr.generalise}",
                        resolu(cr)))

        inc = ia.demande("incoherent", "s", [(("a",), 42), (("b",), 7)], [(("c",), 99), (("d",), 13)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        sc = ia.demande("somme_carres", "xs", [(([1, 2, 3],), 14), (([2, 3],), 13)], [(([5],), 25), (([0, 4],), 16)])
        r.append(_check(f"NON-RÉGRESSION : somme_carres -> `{sc.etage}` résolu={sc.ok}, généralise={sc.generalise}",
                        resolu(sc)))

        # VIVACITÉ (anti-code-mort) : appel DIRECT du spécialiste `equilibre`, hors routeur (remplace le pin d'étage).
        r.append(_check("VIVACITÉ : la brique `equilibre` résout is_balanced en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurEquilibre(), "is_balanced", "s",
                                       "def check(f):\n    assert f('(())')==True\n    assert f('(()')==False\ncheck(is_balanced)",
                                       "def check(f):\n    assert f('')==True\n    assert f('())(')==False\n    assert f('()()')==True\ncheck(is_balanced)")))

    print()
    print(f"BRIQUE ÉQUILIBRE VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
