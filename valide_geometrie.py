"""
BRIQUE GÉOMÉTRIE COMPUTATIONNELLE ENTIÈRE (2026-06-19) — GenerateurGeometrie : distance de Manhattan, DOUBLE de
l'aire d'un triangle (produit en croix), DOUBLE de l'aire d'un polygone (shoelace). Lacunes MESURÉES par gap_probe
2ᵉ vague (manhattan, triangle_area2, polygon_area2 — tous HORS avant ; chebyshev déjà couvert par multi-entrée,
PAS dans cette brique -> zéro masquage). Validée dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. MANHATTAN : résolu via `geometrie` + généralise (held-out adverse, coords négatives).
  2. AIRE² TRIANGLE + POLYGONE : résolus via `geometrie` + généralisent (held-out adverse).
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : chebyshev reste résolu (via son étage habituel, pas géométrie).

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurGeometrie
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        mh = ia.demande("manhattan", "x1, y1, x2, y2", [((0, 0, 3, 4), 7), ((1, 1, 1, 1), 0)],
                        [((-1, -1, 2, 3), 7), ((5, 0, 0, 5), 10), ((-2, -3, -2, 1), 4)])
        r.append(_check(f"MANHATTAN -> `{mh.etage}` ({mh.appels} cand.), gen={mh.generalise}",
                        resolu(mh)))

        tr = ia.demande("triangle_area2", "x1, y1, x2, y2, x3, y3",
                        [((0, 0, 4, 0, 0, 3), 12), ((0, 0, 2, 0, 0, 2), 4)],
                        [((1, 1, 4, 1, 1, 5), 12), ((0, 0, 6, 0, 3, 4), 24), ((-1, -1, 1, -1, 0, 2), 6)])
        pg = ia.demande("polygon_area2", "pts",
                        [(([(0, 0), (4, 0), (4, 3), (0, 3)],), 24), (([(0, 0), (2, 0), (0, 2)],), 4)],
                        [(([(0, 0), (4, 0), (4, 4), (0, 4)],), 32), (([(1, 0), (2, 0), (2, 1), (1, 1)],), 2),
                         (([(0, 0), (5, 0), (5, 2), (0, 2)],), 20)])
        r.append(_check(f"AIRE² TRIANGLE -> `{tr.etage}` ({tr.appels} cand.), gen={tr.generalise} | "
                        f"POLYGONE -> `{pg.etage}` ({pg.appels} cand.), gen={pg.generalise}",
                        resolu(tr) and resolu(pg)))

        inc = ia.demande("incoherent_geo", "x1, y1, x2, y2", [((0, 0, 1, 1), 42)], [((2, 2, 3, 3), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        ch = ia.demande("chebyshev", "x1, y1, x2, y2", [((0, 0, 3, 4), 4), ((1, 1, 2, 5), 4)],
                        [((-1, -1, 2, 3), 4), ((5, 5, 5, 0), 5)])
        r.append(_check(f"NON-RÉGRESSION : chebyshev -> `{ch.etage}` ok={ch.ok}, gen={ch.generalise} "
                        f"(résolu, étage libre)",
                        resolu(ch)))

        r.append(_check("VIVACITÉ : la brique `geometrie` résout manhattan en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurGeometrie(), "manhattan", "x1, y1, x2, y2",
                                       "def check(c):\n    assert c(0,0,3,4)==7\n    assert c(1,1,1,1)==0\ncheck(manhattan)",
                                       "def check(c):\n    assert c(-1,-1,2,3)==7\n    assert c(5,0,0,5)==10\n    assert c(-2,-3,-2,1)==4\ncheck(manhattan)")))

    print()
    print(f"BRIQUE GÉOMÉTRIE VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
