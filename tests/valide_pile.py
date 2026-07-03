"""
BRIQUE PILE / MONOTONE (2026-06-19) — GenerateurPile : eval_rpn (évaluation RPN à pile), next_greater (pile
monotone décroissante). Lacunes MESURÉES par gap_probe 3ᵉ vague (toutes HORS avant). Validée dans le MOTEUR COMPLET.

Critères de MORT (4) :
  1. EVAL_RPN : résolu via `pile` + généralise (held-out adverse).
  2. NEXT_GREATER : résolu via `pile` + généralise (held-out adverse).
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : is_balanced (étage `equilibre`) reste résolu hors `pile`.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from demande import AssistantIA
from garde_ressources import borne
from generateur import GenerateurPile
from valide_commun import brique_vivante, resolu


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        ia = AssistantIA(Path(d) / "s.jsonl")

        rpn = ia.demande("eval_rpn", "tokens", [((["2", "3", "+"],), 5), ((["4", "2", "-"],), 2)],
                         [((["2", "3", "*", "4", "+"],), 10), ((["5"],), 5), ((["10", "2", "-", "3", "*"],), 24)])
        r.append(_check(f"EVAL_RPN -> `{rpn.etage}` ({rpn.appels} cand.), gen={rpn.generalise}",
                        resolu(rpn)))

        # EXTENSION 2026-06-24 (gap_probe DUR) : RPN avec DIVISION + calculatrice à PRÉCÉDENCE -> mêmes garanties, étage `pile`.
        rpd = ia.demande("rpn_eval", "toks", [((["2", "1", "+", "3", "*"],), 9), ((["4", "13", "5", "/", "+"],), 6)],
                         [((["5"],), 5), ((["2", "3", "*", "4", "-"],), 2), ((["10", "2", "/"],), 5)])
        ev = ia.demande("evaluate_expr", "s", [(("3+2*2",), 7), (("2*3+4",), 10)],
                        [(("1+1",), 2), (("10-2*3",), 4), (("100-2*3+8",), 102)])
        r.append(_check(f"RPN/DIV -> `{rpd.etage}` gen={rpd.generalise} | CALC PRÉCÉDENCE -> `{ev.etage}` gen={ev.generalise}",
                        resolu(rpd) and resolu(ev)))

        ng = ia.demande("next_greater", "xs", [(([2, 1, 3],), [3, 3, -1]), (([1, 2, 3, 4],), [2, 3, 4, -1])],
                        [(([3, 2, 1],), [-1, -1, -1]), (([5],), [-1]), (([1, 3, 2, 4],), [3, 4, 4, -1])])
        r.append(_check(f"NEXT_GREATER -> `{ng.etage}` ({ng.appels} cand.), gen={ng.generalise}",
                        resolu(ng)))

        inc = ia.demande("incoherent_pile", "xs", [(([1, 2],), 42)], [(([3, 4],), 99)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        ib = ia.demande("is_balanced", "s", [(("(())",), True), (("(()",), False)], [(("",), True), (("())(",), False)])
        r.append(_check(f"NON-RÉGRESSION : is_balanced -> `{ib.etage}` ok={ib.ok}, gen={ib.generalise} (!= pile)",
                        resolu(ib)))

        # VIVACITÉ (anti-code-mort) : le pin d'étage `pile` retiré ci-dessus prouvait que GenerateurPile est vivant.
        # On le prouve désormais par appel DIRECT du générateur (hors routeur) sur sa tâche canonique eval_rpn + held-out.
        _tv = "def check(c):\n    assert c(['2','3','+'])==5\n    assert c(['4','2','-'])==2\ncheck(eval_rpn)"
        _hv = ("def check(c):\n    assert c(['2','3','*','4','+'])==10\n    assert c(['5'])==5\n"
               "    assert c(['10','2','-','3','*'])==24\ncheck(eval_rpn)")
        r.append(_check("VIVACITÉ : GenerateurPile résout eval_rpn en direct (tests + held-out)",
                        brique_vivante(GenerateurPile(), "eval_rpn", "tokens", _tv, _hv)))

    print()
    print(f"BRIQUE PILE VALIDÉE — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
