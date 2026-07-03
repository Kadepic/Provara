#!/usr/bin/env python3
"""
VALIDATION de allen.py — les 13 relations d'intervalles d'Allen. FAUX=0 : exactement UNE relation par paire
(mutuellement exclusives + exhaustives), inverse involutif exact, intervalle mal formé -> ValueError.
Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys
from itertools import product

import allen as A


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

    def leve(fn):
        try:
            fn(); return False
        except ValueError:
            return True

    # ── Les 13 relations sur des cas explicites ──────────────────────────────────────────────
    cas = {
        A.BEFORE: ((0, 1), (2, 3)), A.AFTER: ((2, 3), (0, 1)),
        A.MEETS: ((0, 1), (1, 2)), A.MET_BY: ((1, 2), (0, 1)),
        A.OVERLAPS: ((0, 2), (1, 3)), A.OVERLAPPED_BY: ((1, 3), (0, 2)),
        A.STARTS: ((0, 1), (0, 2)), A.STARTED_BY: ((0, 2), (0, 1)),
        A.DURING: ((1, 2), (0, 3)), A.CONTAINS: ((0, 3), (1, 2)),
        A.FINISHES: ((1, 2), (0, 2)), A.FINISHED_BY: ((0, 2), (1, 2)),
        A.EQUALS: ((0, 2), (0, 2)),
    }
    for rel_attendue, (a, b) in cas.items():
        check(f"relation {rel_attendue}", A.relation(a, b) == rel_attendue)

    # ── EXCLUSIVITÉ + EXHAUSTIVITÉ : sur un balayage de paires, TOUJOURS exactement une des 13 ──
    bornes = range(0, 6)
    intervalles = [(x, y) for x, y in product(bornes, bornes) if x < y]
    exactement_une = True
    for a in intervalles:
        for b in intervalles:
            r = A.relation(a, b)
            if r not in A.RELATIONS:
                exactement_une = False
    check(f"EXHAUSTIF : {len(intervalles)**2} paires, chacune rend une relation ∈ RELATIONS", exactement_une)
    check("EXCLUSIF : exactement 13 relations distinctes possibles", len(set(A.RELATIONS)) == 13)

    # ── INVERSE involutif exact : relation(a,b) == inverse(relation(b,a)) ─────────────────────
    inverse_ok = all(A.relation(a, b) == A.inverse(A.relation(b, a))
                     for a in intervalles for b in intervalles)
    check("INVERSE : relation(a,b) == inverse(relation(b,a)) sur tout le balayage", inverse_ok)
    check("INVERSE involutif : inverse(inverse(r)) == r", all(A.inverse(A.inverse(r)) == r for r in A.RELATIONS))
    check("INVERSE : equals est son propre inverse", A.inverse(A.EQUALS) == A.EQUALS)

    # ── FAUX=0 : intervalle mal formé -> ValueError (jamais un verdict sur un intervalle dégénéré) ──
    check("FAUX=0 : intervalle début==fin -> ValueError", leve(lambda: A.relation((1, 1), (0, 2))))
    check("FAUX=0 : intervalle début>fin -> ValueError", leve(lambda: A.relation((0, 2), (3, 2))))
    check("FAUX=0 : relation inconnue à inverse -> ValueError", leve(lambda: A.inverse("bidon")))

    # ── Helpers sémantiques ──────────────────────────────────────────────────────────────────
    check("avant : [0,1] avant [2,3]", A.avant((0, 1), (2, 3)) and not A.avant((0, 2), (1, 3)))
    check("chevauche : intervalles à instant intérieur commun", A.chevauche((0, 2), (1, 3))
          and not A.chevauche((0, 1), (2, 3)) and not A.chevauche((0, 1), (1, 2)))
    check("contient : [0,3] contient [1,2]", A.contient((0, 3), (1, 2)) and not A.contient((1, 2), (0, 3)))

    # ── Bornes non numériques : dates ISO comparables comme chaînes (usage temporel réel) ─────
    check("DATES : mandats qui se chevauchent (ISO str)",
          A.relation(("2010-01-01", "2015-01-01"), ("2012-01-01", "2018-01-01")) == A.OVERLAPS)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.relation_temporelle : before", ia.relation_temporelle((0, 1), (2, 3)) == A.BEFORE)
    check("CÂBLAGE ia.relation_temporelle : dates qui se chevauchent",
          ia.relation_temporelle(("2010-01-01", "2015-01-01"), ("2012-01-01", "2018-01-01")) == A.OVERLAPS)

    print(f"\n=== valide_allen : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
