#!/usr/bin/env python3
"""
VALIDATION de profilage.py — classification de complexité empirique (déterministe, sur coûts d'opérations comptés).
FAUX=0 : classe rendue seulement si exposants cohérents ; incohérent -> INDETERMINE ; temps/mémoire = factuels.
Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import profilage as P


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

    tailles = [16, 32, 64, 128, 256]

    check("CONSTANTE : coût plat", P.classe_croissance(tailles, [5, 5, 5, 5, 5]) == P.CONSTANTE)
    check("LINÉAIRE : coût ∝ n", P.classe_croissance(tailles, [16, 32, 64, 128, 256]) == P.LINEAIRE)
    check("QUADRATIQUE : coût ∝ n²",
          P.classe_croissance(tailles, [n * n for n in tailles]) == P.QUADRATIQUE)
    check("CUBIQUE : coût ∝ n³",
          P.classe_croissance(tailles, [n ** 3 for n in tailles]) == P.CUBIQUE)
    check("LOGARITHMIQUE : coût ∝ log n",
          P.classe_croissance(tailles, [__import__("math").log(n) for n in tailles]) == P.LOG)
    check("n·log n : classé LINEAIRE (indistinguable du linéaire sur plage bornée — honnête)",
          P.classe_croissance(tailles, [n * __import__("math").log(n) for n in tailles]) == P.LINEAIRE)
    check("EXPONENTIELLE : coût ∝ 2^n (exposant explose)",
          P.classe_croissance([4, 8, 12, 16, 20], [2 ** k for k in [4, 8, 12, 16, 20]]) == P.EXPONENTIELLE)

    # ── FAUX=0 : abstention ────────────────────────────────────────────────────────────────────
    check("FAUX=0 : trop peu de points -> INDETERMINE", P.classe_croissance([1, 2], [1, 2]) == P.INDETERMINE)
    check("FAUX=0 : coûts incohérents (bruit fort) -> INDETERMINE",
          P.classe_croissance(tailles, [10, 3, 90, 4, 250]) == P.INDETERMINE)

    # ── Cas RÉEL : comparer deux algos par comptage d'opérations (déterministe) ────────────────
    # somme naïve O(n) vs somme de paires O(n²), coûts = nb d'opérations comptées
    def cout_lineaire(n):
        c = 0
        for _ in range(n):
            c += 1
        return c

    def cout_quadratique(n):
        c = 0
        for _ in range(n):
            for _ in range(n):
                c += 1
        return c

    cl = [cout_lineaire(n) for n in tailles]
    cq = [cout_quadratique(n) for n in tailles]
    check("RÉEL : boucle simple classée LINEAIRE", P.classe_croissance(tailles, cl) == P.LINEAIRE)
    check("RÉEL : double boucle classée QUADRATIQUE", P.classe_croissance(tailles, cq) == P.QUADRATIQUE)

    # ── Utilitaires factuels : temps médian et mémoire (valeurs réelles, non nulles) ──────────
    t = P.mesure_temps(lambda n: sum(range(n)), 10000, repetitions=3)
    check("mesure_temps : valeur réelle >= 0", isinstance(t, float) and t >= 0)
    m = P.mesure_memoire(lambda n: [0] * n, 100000)
    check("mesure_memoire : une grosse liste alloue de la mémoire", m > 0)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.complexite_empirique : double boucle -> QUADRATIQUE",
          ia.complexite_empirique(tailles, cq) == P.QUADRATIQUE)

    print(f"\n=== valide_profilage : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
