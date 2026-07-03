#!/usr/bin/env python3
"""
VALIDATION du backend C (executeur.ExecuteurC) — premier langage COMPILÉ jugé par le MÊME juge (compile &&
exécute, sentinelle anti-sabotage). FAUX=0 : PASS seulement si le code compile, passe les tests ET imprime la
sentinelle ; test raté -> FAIL ; compilation échouée -> ERROR ; sortie propre sans tests -> SABOTAGE.
Nécessite gcc (sinon SKIP honnête). Léger (pas de lecteur).
"""
from __future__ import annotations

import shutil
import sys

from juge import juge, Limites, PASS, FAIL, ERROR, SABOTAGE
from executeur import ExecuteurC, EXECUTEURS

LIM = Limites(temps_s=30, cpu_s=20, memoire_mo=1024)   # large : gcc doit compiler avant d'exécuter
C = ExecuteurC()


def main() -> int:
    if shutil.which("gcc") is None:
        print("  [SKIP] gcc absent — backend C non testable dans cet environnement (honnête).")
        print("\n=== valide_executeur_c : 0/0 (skip) ===")
        return 0

    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    check("registre : 'c' présent dans EXECUTEURS", EXECUTEURS.get("c").__class__ is ExecuteurC)

    tests = "    ASSERT(carre(3)==9);\n    ASSERT(carre(0)==0);\n    ASSERT(carre(5)==25);"

    # 1. Solution C CORRECTE -> PASS (compile, tests passent, sentinelle imprimée)
    v = juge("int carre(int x){ return x*x; }", tests, LIM, executeur=C)
    check(f"C CORRECT -> PASS (statut={v.statut})", v.passe and v.statut == PASS)

    # 2. Solution C FAUSSE -> FAIL (compile et tourne, mais carre(3)=6 != 9)
    v = juge("int carre(int x){ return x+x; }", tests, LIM, executeur=C)
    check(f"C FAUX -> FAIL (statut={v.statut})", not v.passe and v.statut == FAIL)

    # 3. Solution C qui NE COMPILE PAS -> ERROR (jamais confondu avec un test raté)
    v = juge("int carre(int x){ return x*x }", tests, LIM, executeur=C)   # ; manquant
    check(f"C NON COMPILABLE -> ERROR (statut={v.statut})", not v.passe and v.statut == ERROR)

    # 4. SENTINELLE : sortie « propre » (exit 0) SANS exécuter les tests -> SABOTAGE (jamais un faux PASS)
    v = juge("int carre(int x){ exit(0); return 0; }", tests, LIM, executeur=C)
    check(f"C SABOTAGE (exit 0 avant sentinelle) -> jamais PASS (statut={v.statut})",
          not v.passe and v.statut == SABOTAGE)

    # 5. FAUX=0 transverse : sur une batterie, aucun mauvais code ne PASSE
    mauvais = [
        ("int carre(int x){ return x+1; }", tests),          # faux
        ("int carre(int x){ return x*x }", tests),           # ne compile pas
        ("int carre(int x){ return x*x; }", "    ASSERT(carre(2)==5);"),  # test qui doit rater
    ]
    faux_pass = [s for s, t in mauvais if juge(s, t, LIM, executeur=C).passe]
    check(f"FAUX=0 : aucun code fautif ne PASSE (faux_pass={len(faux_pass)})", not faux_pass)

    # 6. math.h disponible (perf native + calcul) : sqrt exact
    v = juge("#include <math.h>\nint racine(int x){ return (int)sqrt((double)x); }",
             "    ASSERT(racine(9)==3);\n    ASSERT(racine(16)==4);", LIM, executeur=C)
    check(f"C avec math.h -> PASS (sqrt)", v.passe)

    print(f"\n=== valide_executeur_c : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
