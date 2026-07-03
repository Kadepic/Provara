"""
BRIQUE PREMIER-UNIQUE / FRÉQUENCE PUIS PREMIER SATISFAISANT (2026-06-19) — deux passes : compter puis rendre le 1er
élément de fréquence 1 (avec défaut « rien »). Lacune MESURÉE par gap_probe (first_unique_char). Validée dans le
MOTEUR COMPLET (intégré).

Critères de MORT (5) :
  1. FIRST_UNIQUE_CHAR : RÉSOLU + généralise (held-out adverse, schéma A : l'élément) — étage LIBRE (voie la moins chère).
  2. FIRST_UNIQUE_INDEX : RÉSOLU + généralise (held-out adverse, schéma B : l'index) — étage LIBRE.
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : une tâche d'un autre étage (somme_carres) reste résolue.
  5. VIVACITÉ : la brique spécialiste `premier-unique` résout first_unique_char en DIRECT (hors routeur, anti-code-mort).

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurPremierUnique
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        fc = ia.demande("first_unique_char", "s", [(("leetcode",), "l"), (("aabb",), "")],
                        [(("loveleetcode",), "v"), (("x",), "x"), (("aabbc",), "c")])
        r.append(_check(f"FIRST_UNIQUE_CHAR -> `{fc.etage}` ({fc.appels} cand.), généralise={fc.generalise}",
                        resolu(fc)))

        fi = ia.demande("first_unique_index", "s", [(("leetcode",), 0), (("aabb",), -1)],
                        [(("loveleetcode",), 2), (("x",), 0), (("aabbc",), 4)])
        r.append(_check(f"FIRST_UNIQUE_INDEX -> `{fi.etage}` ({fi.appels} cand.), généralise={fi.generalise}",
                        resolu(fi)))

        inc = ia.demande("incoherent", "s", [(("a",), 42), (("b",), 7)], [(("c",), 99), (("d",), 13)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        sc = ia.demande("somme_carres", "xs", [(([1, 2, 3],), 14), (([2, 3],), 13)], [(([5],), 25), (([0, 4],), 16)])
        r.append(_check(f"NON-RÉGRESSION : somme_carres -> `{sc.etage}` résolu={sc.ok}, généralise={sc.generalise}",
                        resolu(sc)))

        r.append(_check("VIVACITÉ : la brique `premier-unique` résout first_unique_char en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurPremierUnique(), "first_unique_char", "s",
                                       "def check(c):\n    assert c('leetcode')=='l'\n    assert c('aabb')==''\ncheck(first_unique_char)",
                                       "def check(c):\n    assert c('loveleetcode')=='v'\n    assert c('x')=='x'\n    assert c('aabbc')=='c'\ncheck(first_unique_char)")))

    print()
    print(f"BRIQUE PREMIER-UNIQUE VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
