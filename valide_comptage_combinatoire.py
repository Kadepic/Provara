"""
BRIQUE COMPTAGE COMBINATOIRE (2026-06-19) — GenerateurComptageCombinatoire : catalan, derangements, stars_bars,
partitions, subset_sum_count. Lacunes MESURÉES par gap_probe 2ᵉ vague (toutes HORS avant). `combinatoire` ÉNUMÈRE,
`math-avance` ne donne que C(n,k) atomique -> aucun masquage. Validée dans le MOTEUR COMPLET (held-out adverse).

Critères de MORT (5) — PENSÉE MACHINE : on juge le RÉSULTAT (résolu + généralise, au chemin le moins cher), pas l'étage :
  1. CATALAN + DERANGEMENTS : résolus + généralisent (étage libre = le moins cher).
  2. STARS_BARS + PARTITIONS + SUBSET_SUM_COUNT : résolus + généralisent.
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : factorial (déjà couvert par `pli`) reste résolu (la brique n'a rien cassé/masqué).
  5. VIVACITÉ : la brique spécialiste `comptage-combinatoire` (GenerateurComptageCombinatoire) résout catalan en DIRECT (hors routeur).

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurComptageCombinatoire
from valide_commun import brique_vivante, resolu

ET = "comptage-combinatoire"


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        ca = ia.demande("catalan", "n", [((3,), 5), ((0,), 1)], [((4,), 14), ((1,), 1), ((5,), 42), ((6,), 132)])
        de = ia.demande("derangements", "n", [((3,), 2), ((4,), 9)], [((0,), 1), ((1,), 0), ((5,), 44), ((6,), 265)])
        # PENSÉE MACHINE (2026-07-02) : on juge le RÉSULTAT (résolu + généralise), pas l'étage. catalan est résolu au
        # plus efficace (dp-int, moins cher, correct) — vouloir le forcer sur `comptage-combinatoire` serait un biais
        # humain. La vivacité de la brique comptage-combinatoire est prouvée EN DIRECT au dernier check (appel du
        # générateur hors routeur, sur SA tâche canonique catalan) — pas en imposant l'étage de catalan.
        r.append(_check(f"CATALAN -> `{ca.etage}` ({ca.appels} cand.), gen={ca.generalise} | "
                        f"DERANGEMENTS -> `{de.etage}` ({de.appels} cand.), gen={de.generalise}",
                        resolu(ca) and resolu(de)))

        sb = ia.demande("stars_bars", "n, k", [((5, 2), 6), ((3, 3), 10)], [((0, 4), 1), ((4, 1), 1), ((2, 3), 6)])
        pa = ia.demande("partitions", "n", [((4,), 5), ((3,), 3)], [((0,), 1), ((5,), 7), ((6,), 11), ((7,), 15)])
        ss = ia.demande("subset_sum_count", "xs, t", [(([1, 2, 3], 3), 2), (([2, 4], 6), 1)],
                        [(([1, 1, 1], 2), 3), (([5], 3), 0), (([1, 2, 3, 4], 5), 2)])
        r.append(_check(f"STARS_BARS -> `{sb.etage}` ({sb.appels}c), gen={sb.generalise} | "
                        f"PARTITIONS -> `{pa.etage}` ({pa.appels}c), gen={pa.generalise} | "
                        f"SUBSET_SUM -> `{ss.etage}` ({ss.appels}c), gen={ss.generalise}",
                        resolu(sb) and resolu(pa) and resolu(ss)))

        inc = ia.demande("incoherent_comb", "n", [((3,), 7), ((4,), 7)], [((5,), 8), ((6,), 9)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        fa = ia.demande("factorial", "n", [((4,), 24), ((0,), 1)], [((5,), 120), ((1,), 1), ((6,), 720)])
        r.append(_check(f"NON-RÉGRESSION : factorial -> `{fa.etage}` ok={fa.ok}, gen={fa.generalise}",
                        resolu(fa)))

        # VIVACITÉ (anti-code-mort) : appel DIRECT du spécialiste comptage-combinatoire, hors routeur (remplace le pin).
        r.append(_check("VIVACITÉ : la brique `comptage-combinatoire` résout catalan en direct (spécialiste vivant, hors routeur)",
                        brique_vivante(GenerateurComptageCombinatoire(), "catalan", "n",
                                       "def check(f):\n    assert f(3)==5\n    assert f(0)==1\ncheck(catalan)",
                                       "def check(f):\n    assert f(4)==14\n    assert f(5)==42\n    assert f(6)==132\ncheck(catalan)")))

    print()
    print(f"BRIQUE COMPTAGE COMBINATOIRE VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
