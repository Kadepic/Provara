"""
VAGUE 44 — GRILLES 2D & GÉOMÉTRIE ENTIÈRE (2026-06-22 nuit, autonomie). gap_probe_vague44 = 8 tâches.
2 VRAIS TROUS bâtis + 6 confirmées (templates de grille déjà présents, re-testés À FROID sur held-out DURCI).

Bâtis cette vague :
  • `max_island_area` -> `tableaux` (flood-fill + suivi de la plus grande composante ; sœur de count_islands).
  • `manhattan_diameter` -> `geometrie` (diamètre L1 d'un nuage de points ; aucun étage ne balayait les paires en L1).
Confirmées À FROID (held-out durci = anneaux/cycles, diagonales, grilles non-monotones — démasque les coïncidences) :
  num_islands, min_path_sum, maximal_square, island_perimeter (-> `tableaux`).

Critères de MORT (4) :
  1. FLOOD-FILL (composantes connexes) : num_islands + max_island_area via `tableaux`, held-out anneaux/diagonales.
  2. DP GRILLE : min_path_sum + maximal_square via `tableaux`, held-out non-monotone (glouton ≠ DP).
  3. GÉOMÉTRIE + TOPOLOGIE : manhattan_diameter via `geometrie` ; island_perimeter via `tableaux`.
  4. HORS HONNÊTE : incohérent -> HORS.

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

        # ---- 1. FLOOD-FILL / COMPOSANTES CONNEXES --------------------------------------------------------------
        ni = ia.demande("num_islands", "grid",
                        [(([[1, 1, 0], [0, 1, 0], [1, 0, 1]],), 3), (([[1, 1, 1], [1, 1, 1]],), 1)],
                        [(([[0, 0], [0, 0]],), 0), (([[1, 0, 1, 0, 1]],), 3), (([[1], [0], [1]],), 2),
                         (([[1, 1, 1], [1, 0, 1], [1, 1, 1]],), 1), (([[1, 0, 1], [0, 0, 0], [1, 0, 1]],), 4),
                         (([[1, 0], [0, 1]],), 2), (([[1, 1, 1, 1], [1, 0, 0, 1], [1, 1, 1, 1]],), 1)])
        mia = ia.demande("max_island_area", "grid",
                         [(([[1, 1, 0], [0, 1, 0], [1, 0, 1]],), 3), (([[1, 1], [1, 1]],), 4)],
                         [(([[0, 0], [0, 0]],), 0), (([[1, 0, 1, 1]],), 2), (([[1], [1], [0]],), 2),
                          (([[1, 1, 1], [1, 0, 1], [1, 1, 1]],), 8), (([[1, 0, 1], [0, 0, 0], [1, 0, 1]],), 1),
                          (([[1, 1, 0], [1, 0, 0], [0, 0, 1]],), 3), (([[1, 1, 1, 1], [1, 0, 0, 1], [1, 1, 1, 1]],), 10)])
        r.append(_check(f"FLOOD-FILL num_islands->`{ni.etage}` max_island_area->`{mia.etage}` (==tableaux)",
                        all(resolu(x) for x in (ni, mia))))

        # ---- 2. DP GRILLE (held-out non-monotone : glouton ≠ DP) ----------------------------------------------
        mps = ia.demande("min_path_sum", "grid",
                         [(([[1, 3, 1], [1, 5, 1], [4, 2, 1]],), 7), (([[1, 2], [3, 4]],), 7)],
                         [(([[5]],), 5), (([[1, 2, 3]],), 6), (([[1], [2], [3]],), 6),
                          (([[1, 2, 5], [3, 2, 1]],), 6), (([[1, 100, 1, 1], [1, 100, 1, 100], [1, 1, 1, 100]],), 105),
                          (([[5, 9, 1], [1, 9, 1], [1, 1, 1]],), 9)])
        msq = ia.demande("maximal_square", "grid",
                         [(([[1, 1], [1, 1]],), 4), (([[1, 0, 1], [1, 1, 1], [1, 1, 1]],), 4)],
                         [(([[0, 0], [0, 0]],), 0), (([[1]],), 1), (([[0, 1], [1, 0]],), 1),
                          (([[0, 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 1], [0, 1, 1, 0]],), 4),
                          (([[1, 1, 1], [1, 1, 1], [1, 1, 1]],), 9)])
        r.append(_check(f"DP GRILLE min_path_sum->`{mps.etage}` maximal_square->`{msq.etage}` (==tableaux)",
                        all(resolu(x) for x in (mps, msq))))

        # ---- 3. GÉOMÉTRIE (diamètre L1) + TOPOLOGIE (périmètre) ----------------------------------------------
        md = ia.demande("manhattan_diameter", "points",
                        [(([[0, 0], [1, 1], [3, 0]],), 3), (([[0, 0], [0, 5]],), 5)],
                        [(([[2, 2]],), 0), (([[1, 1], [1, 1]],), 0), (([[-1, -1], [2, 3]],), 7),
                         (([[0, 0], [4, 0], [0, 3], [4, 3]],), 7)])
        ip = ia.demande("island_perimeter", "grid",
                        [(([[0, 1, 0], [1, 1, 1], [0, 1, 0]],), 12), (([[1, 1], [1, 1]],), 8)],
                        [(([[1]],), 4), (([[1, 0, 1]],), 8), (([[1, 1, 0], [0, 1, 1]],), 10),
                         (([[1, 1, 1], [1, 0, 1], [1, 1, 1]],), 16), (([[1, 0, 1], [0, 0, 0], [1, 0, 1]],), 16)])
        r.append(_check(f"GÉO/TOPO manhattan_diameter->`{md.etage}`(==geometrie) island_perimeter->`{ip.etage}`(==tableaux)",
                        resolu(md) and resolu(ip)))

        # ---- 4. HORS HONNÊTE ---------------------------------------------------------------------------------
        inc = ia.demande("incoherent_v44", "g", [(([[1, 2]],), 42)], [(([[3, 4]],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

    print()
    print("VAGUE 44 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
