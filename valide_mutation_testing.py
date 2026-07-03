#!/usr/bin/env python3
"""
VALIDATION de mutation_testing.py. FAUX=0 : mutant équivalent filtré (pas compté survivant) ; survivant = mutant
PROUVÉ différent et non détecté (lacune réelle) ; score = tués/(non équivalents). Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import mutation_testing as M


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    reference = lambda x: x * 2
    domaine = range(-20, 21)

    # Mutants : un équivalent (x+x), deux fautifs (x*3, x+1)
    equivalent = lambda x: x + x
    faux1 = lambda x: x * 3
    faux2 = lambda x: x + 1
    mutants = [equivalent, faux1, faux2]

    # ── Suite FORTE : détecte les deux fautifs (teste sur des points discriminants) ───────────
    def suite_forte(fn):
        return fn(3) == 6 and fn(-2) == -4 and fn(1) == 2      # tue x*3 (3->9) et x+1 (3->4)
    r = M.analyse(reference, mutants, suite_forte, domaine)
    check("MUTATION : l'équivalent (x+x) est filtré (compté EQUIVALENT, pas survivant)", r["equivalents"] == 1)
    check("MUTATION : suite forte tue les 2 fautifs (score=1.0, 0 survivant)",
          r["score"] == 1.0 and r["survivants"] == 0 and r["tues"] == 2)
    check("ADÉQUATE : suite forte -> adéquate", M.suite_adequate(reference, mutants, suite_forte, domaine))

    # ── Suite FAIBLE : ne teste que fn(0) -> ne détecte pas x*3 (0->0) : SURVIVANT ─────────────
    def suite_faible(fn):
        return fn(0) == 0                                       # x*2, x+x, x*3 donnent tous 0 ; x+1 donne 1 (tué)
    r2 = M.analyse(reference, mutants, suite_faible, domaine)
    check("MUTATION : suite faible laisse x*3 SURVIVRE (lacune réelle)", r2["survivants"] >= 1)
    check("MUTATION FAUX=0 : le survivant est PROUVÉ différent de la référence",
          any(st == M.SURVIVANT for _m, st in r2["verdicts"]))
    check("MUTATION : score faible < 1.0 (suite inadéquate)", r2["score"] < 1.0)
    check("INADÉQUATE : suite faible -> NON adéquate (lacune démontrée)",
          not M.suite_adequate(reference, mutants, suite_faible, domaine))

    # ── FAUX=0 : que des mutants équivalents -> score None (rien à tuer), pas un faux 100% ─────
    r3 = M.analyse(reference, [equivalent, lambda x: x + x], suite_forte, domaine)
    check("FAUX=0 : que des équivalents -> score None (aucun mutant fautif à tuer)",
          r3["score"] is None and r3["equivalents"] == 2)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    ri = ia.mutation_score(reference, mutants, suite_forte, domaine)
    check("CÂBLAGE ia.mutation_score : suite forte -> score 1.0", ri["score"] == 1.0)

    print(f"\n=== valide_mutation_testing : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
