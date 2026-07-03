"""
BRIQUE ITÉRATION / POINT-FIXE (2026-06-19) — répéter un pas scalaire jusqu'à une condition. Lacune MESURÉE par
gap_probe (digital_root, collatz_steps hors de portée des autres étages). Validée dans le MOTEUR COMPLET (intégré).

Critères de MORT (4) :
  1. DIGITAL_ROOT : résolu via `iteration` + généralise (held-out adverse).
  2. COLLATZ_STEPS : résolu via `iteration` + généralise (held-out adverse).
  3. HORS HONNÊTE : une tâche incohérente (non-fonction) -> HORS (jamais de faux).
  4. NON-RÉGRESSION : une tâche d'un autre étage (somme_carres) reste résolue (la brique n'a rien cassé/masqué).

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurIteration
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        dr = ia.demande("digital_root", "n", [((38,), 2), ((9,), 9)], [((0,), 0), ((123,), 6), ((99,), 9)])
        r.append(_check(f"DIGITAL_ROOT -> `{dr.etage}` ({dr.appels} cand.), généralise={dr.generalise}",
                        resolu(dr)))

        cz = ia.demande("collatz_steps", "n", [((6,), 8), ((1,), 0)], [((7,), 16), ((2,), 1), ((3,), 7)])
        r.append(_check(f"COLLATZ_STEPS -> `{cz.etage}` ({cz.appels} cand.), généralise={cz.generalise}",
                        resolu(cz)))

        inc = ia.demande("incoherent", "n", [((3,), 42), ((1,), 7)], [((5,), 99), ((2,), 13)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        sc = ia.demande("somme_carres", "xs", [(([1, 2, 3],), 14), (([2, 3],), 13)], [(([5],), 25), (([0, 4],), 16)])
        r.append(_check(f"NON-RÉGRESSION : somme_carres -> `{sc.etage}` résolu={sc.ok}, généralise={sc.generalise}",
                        resolu(sc)))

        # VIVACITÉ (anti-code-mort) : la brique spécialiste `iteration` résout SA tâche canonique digital_root en
        # DIRECT (hors routeur) sur tests + held-out adverse — remplace le rôle du pin d'étage.
        r.append(_check("VIVACITÉ : la brique `iteration` résout digital_root en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurIteration(), "digital_root", "n",
                                       "def check(c):\n    assert c(38)==2\n    assert c(9)==9\ncheck(digital_root)",
                                       "def check(c):\n    assert c(0)==0\n    assert c(123)==6\n    assert c(99)==9\ncheck(digital_root)")))

    print()
    print(f"BRIQUE ITÉRATION VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
