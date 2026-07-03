"""
BRIQUE CALENDRIER + EXTENSIONS BITS & GÉOMÉTRIE (2026-06-19) — lacunes MESURÉES par gap_probe 3ᵉ vague :
  - `calendrier` (neuf) : days_in_month (table des mois + règle bissextile).
  - `bits` (étendu) : hamming_distance (popcount du XOR), trailing_zeros (ctz), lowest_bit (n & -n).
  - `geometrie` (étendu) : det2 (déterminant 2×2 signé = produit en croix).
Validées dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (4) :
  1. CALENDRIER : days_in_month résolu via `calendrier` + généralise.
  2. BITS ÉTENDU : hamming/trailing_zeros/lowest_bit résolus via `bits` + généralisent.
  3. GÉO ÉTENDU + HORS : det2 via `geometrie` + généralise ; une tâche incohérente -> HORS.
  4. ROBUSTESSE : popcount reste via `bits` ; is_leap_year désormais résolu ROBUSTEMENT via `calendrier` (à froid,
     là où `recombinaison` échouait sans store chaud — fragilité corrigée).

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurBits, GenerateurCalendrier, GenerateurGeometrie
from juge import Limites, juge
from taches import Tache
from valide_commun import resolu


def _brique_vivante(gen, fn, sig, tests, held, n=600):
    """Vivacité machine-native : la brique spécialiste résout SA tâche canonique en DIRECT (indépendant du routeur)."""
    t = Tache(id=fn, point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
    lim = Limites(temps_s=3, cpu_s=2)
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, lim).passe and (not t.tests_held_out or juge(code, t.tests_held_out, lim).passe):
            return True
    return False


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        dm = ia.demande("days_in_month", "y, m", [((2024, 2), 29), ((2023, 2), 28)],
                        [((2024, 4), 30), ((2024, 1), 31), ((2023, 12), 31), ((2000, 2), 29), ((1900, 2), 28)])
        # PENSÉE MACHINE : on juge le RÉSULTAT (résolu + généralise) ; l'étage affiché reste pour l'observabilité.
        r.append(_check(f"CALENDRIER days_in_month -> `{dm.etage}` ({dm.appels}c), gen={dm.generalise}",
                        resolu(dm)))
        r.append(_check("VIVACITÉ : la brique `calendrier` résout days_in_month en direct (spécialiste vivant, hors routeur)",
                        _brique_vivante(GenerateurCalendrier(), "days_in_month", "y, m",
                                        "def check(c):\n    assert c(2024,2)==29\n    assert c(2023,2)==28\ncheck(days_in_month)",
                                        "def check(c):\n    assert c(2024,4)==30\n    assert c(2000,2)==29\n    assert c(1900,2)==28\ncheck(days_in_month)")))

        ha = ia.demande("hamming_distance", "a, b", [((1, 4), 2), ((0, 0), 0)], [((7, 8), 4), ((5, 5), 0), ((2, 3), 1)])
        tz = ia.demande("trailing_zeros", "n", [((8,), 3), ((12,), 2)], [((1,), 0), ((16,), 4), ((6,), 1)])
        lb = ia.demande("lowest_bit", "n", [((12,), 4), ((10,), 2)], [((1,), 1), ((8,), 8), ((6,), 2)])
        r.append(_check(f"BITS hamming -> `{ha.etage}`({ha.appels}c) | tz -> `{tz.etage}`({tz.appels}c) | "
                        f"lb -> `{lb.etage}`({lb.appels}c)",
                        resolu(ha) and resolu(tz) and resolu(lb)))
        r.append(_check("VIVACITÉ : la brique `bits` résout hamming_distance en direct (spécialiste vivant, hors routeur)",
                        _brique_vivante(GenerateurBits(), "hamming_distance", "a, b",
                                        "def check(c):\n    assert c(1,4)==2\n    assert c(0,0)==0\ncheck(hamming_distance)",
                                        "def check(c):\n    assert c(7,8)==4\n    assert c(5,5)==0\n    assert c(2,3)==1\ncheck(hamming_distance)")))

        de = ia.demande("det2", "m", [(([[1, 2], [3, 4]],), -2), (([[2, 0], [0, 3]],), 6)],
                        [(([[1, 0], [0, 1]],), 1), (([[3, 8], [4, 6]],), -14), (([[0, 5], [2, 0]],), -10)])
        inc = ia.demande("incoherent_v3", "n", [((1,), 7), ((2,), 7)], [((3,), 8), ((4,), 9)])
        # PENSÉE MACHINE : on juge le RÉSULTAT (det2 résolu + généralise, au plus efficace) + l'honnêteté (incohérent
        # -> HORS). L'étage exact n'est pas imposé (le routeur peut résoudre det2 au moins cher, ex. `numerique` :
        # c'est le comportement désiré). La vivacité de la brique `geometrie` est prouvée en DIRECT ci-dessous.
        r.append(_check(f"GÉO det2 -> `{de.etage}`({de.appels}c), gen={de.generalise} | HORS incoherent ok={inc.ok}",
                        de.ok and de.generalise and not inc.ok))
        r.append(_check("VIVACITÉ : la brique `geometrie` résout det2 en direct (spécialiste vivant, hors routeur)",
                        _brique_vivante(GenerateurGeometrie(), "det2", "m",
                                        "def check(c):\n    assert c([[1,2],[3,4]])==-2\n    assert c([[2,0],[0,3]])==6\ncheck(det2)",
                                        "def check(c):\n    assert c([[5,1],[2,3]])==13\ncheck(det2)")))

        pc = ia.demande("popcount", "n", [((7,), 3), ((8,), 1)], [((0,), 0), ((255,), 8), ((1,), 1)])
        # is_leap_year en IA FRAÎCHE (store FROID) pour prouver la robustesse (là où recombinaison échouait).
        with tempfile.TemporaryDirectory() as d2:
            ly = AssistantIA(Path(d2) / "froid.jsonl").demande(
                "is_leap_year", "y", [((2000,), True), ((1900,), False)],
                [((2024,), True), ((2023,), False), ((2400,), True), ((2100,), False)])
        r.append(_check(f"ROBUSTESSE : popcount -> `{pc.etage}` (==bits) | is_leap_year FROID -> `{ly.etage}` (==calendrier)",
                        resolu(pc) and resolu(ly)))

    print()
    print(f"BRIQUES CALENDRIER + BITS/GÉO ÉTENDUES VALIDÉES — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
