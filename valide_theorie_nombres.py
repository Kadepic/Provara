"""
BRIQUE THÉORIE DES NOMBRES — AGRÉGATS SUR 1..n (2026-06-19) — extension de GenerateurDiviseurs : somme des diviseurs,
primalité, perfection, indicatrice d'Euler. Lacunes MESURÉES par gap_probe 2ᵉ vague (sum_divisors, is_prime,
is_perfect, euler_totient — tous HORS avant). Validée dans le MOTEUR COMPLET (intégré, held-out adverse).

Critères de MORT (4) :
  1. SOMME_DIVISEURS + PRIMALITÉ : résolus via `diviseurs` + généralisent (held-out adverse).
  2. PERFECTION + EULER : résolus via `diviseurs` + généralisent (held-out adverse).
  3. HORS HONNÊTE : une tâche incohérente -> HORS (jamais de faux).
  4. NON-RÉGRESSION : count_divisors (déjà couvert) reste résolu via `diviseurs`.

SÉQUENTIEL + garde.
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

        # 1. somme des diviseurs (σ) + primalité.
        sd = ia.demande("sum_divisors", "n", [((6,), 12), ((4,), 7)],
                        [((1,), 1), ((12,), 28), ((28,), 56), ((10,), 18)])
        pr = ia.demande("is_prime", "n", [((7,), True), ((9,), False)],
                        [((2,), True), ((1,), False), ((97,), True), ((4,), False)])
        r.append(_check(f"SOMME_DIVISEURS -> `{sd.etage}` ({sd.appels} cand.), gen={sd.generalise} | "
                        f"PRIMALITÉ -> `{pr.etage}` ({pr.appels} cand.), gen={pr.generalise}",
                        resolu(sd) and resolu(pr)))

        # 2. perfection + indicatrice d'Euler.
        pf = ia.demande("is_perfect", "n", [((6,), True), ((10,), False)],
                        [((28,), True), ((1,), False), ((496,), True), ((12,), False)])
        eu = ia.demande("euler_totient", "n", [((9,), 6), ((10,), 4)],
                        [((1,), 1), ((7,), 6), ((12,), 4), ((8,), 4)])
        r.append(_check(f"PERFECTION -> `{pf.etage}` ({pf.appels} cand.), gen={pf.generalise} | "
                        f"EULER -> `{eu.etage}` ({eu.appels} cand.), gen={eu.generalise}",
                        resolu(pf) and resolu(eu)))

        # 3. HORS honnête (incohérent).
        inc = ia.demande("incoherent_nt", "n", [((4,), 7), ((5,), 7)], [((6,), 7), ((9,), 8)])
        r.append(_check(f"HORS HONNÊTE : incoherent -> ok={inc.ok} (doit être False)", not inc.ok))

        # 4. non-régression : count_divisors reste via `diviseurs`.
        cd = ia.demande("count_divisors", "n", [((12,), 6), ((7,), 2)], [((1,), 1), ((16,), 5), ((36,), 9)])
        r.append(_check(f"NON-RÉGRESSION : count_divisors -> `{cd.etage}` ok={cd.ok}, gen={cd.generalise}",
                        resolu(cd)))

    print()
    print("BRIQUE THÉORIE DES NOMBRES VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
