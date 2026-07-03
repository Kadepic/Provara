"""
BRIQUE CHEVAUCHEMENT / BALAYAGE D'INTERVALLES (sweep-line) (2026-06-19) — événements ±1 aux bornes, tri, max courant
du compte simultané. Lacune MESURÉE par gap_probe (max_overlap). Validée dans le MOTEUR COMPLET (intégré).

Critères de MORT (4) :
  1. MAX_OVERLAP : résolu via `chevauchement` + généralise (held-out adverse).
  2. MAX_OVERLAP (jeu disjoint) : résolu via `chevauchement` + généralise (robustesse : bornes éloignées/empilées).
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : une tâche d'un autre étage (somme_carres) reste résolue.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurChevauchement
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        mo = ia.demande("max_overlap", "intervals", [(([(1, 3), (2, 5), (4, 6)],), 2)],
                        [(([(1, 2), (3, 4)],), 1), (([(1, 10), (2, 3), (2, 4)],), 3)])
        r.append(_check(f"MAX_OVERLAP -> `{mo.etage}` ({mo.appels} cand.), généralise={mo.generalise}",
                        resolu(mo)))

        mo2 = ia.demande("pic_simultane", "intervals", [(([(0, 5), (1, 2), (3, 8)],), 2)],
                         [(([(1, 1), (2, 2)],), 1), (([(1, 9), (2, 9), (3, 9), (4, 9)],), 4)])
        r.append(_check(f"PIC_SIMULTANE -> `{mo2.etage}` ({mo2.appels} cand.), généralise={mo2.generalise}",
                        resolu(mo2)))

        inc = ia.demande("incoherent", "intervals", [(([(1, 2)],), 42)], [(([(3, 4)],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        sc = ia.demande("somme_carres", "xs", [(([1, 2, 3],), 14), (([2, 3],), 13)], [(([5],), 25), (([0, 4],), 16)])
        r.append(_check(f"NON-RÉGRESSION : somme_carres -> `{sc.etage}` résolu={sc.ok}, généralise={sc.generalise}",
                        resolu(sc)))

        r.append(_check("VIVACITÉ : la brique `chevauchement` résout max_overlap en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurChevauchement(), "max_overlap", "intervals",
                                       "def check(c):\n    assert c([(1,3),(2,5),(4,6)])==2\ncheck(max_overlap)",
                                       "def check(c):\n    assert c([(1,2),(3,4)])==1\n    assert c([(1,10),(2,3),(2,4)])==3\ncheck(max_overlap)")))

    print()
    print(f"BRIQUE CHEVAUCHEMENT VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
