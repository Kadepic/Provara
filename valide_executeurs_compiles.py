#!/usr/bin/env python3
"""
VALIDATION des backends COMPILÉS C++/Rust/Go (executeur) — le MÊME juge compile+exécute+juge chacun, sentinelle
anti-sabotage. FAUX=0 par langage : code correct -> PASS ; faux -> FAIL ; non compilable -> ERROR ; exit propre
sans sentinelle -> jamais PASS. Chaque langage est SKIP honnête si son runtime est absent. Léger (pas de lecteur).
"""
from __future__ import annotations

import shutil
import sys

from juge import juge, Limites, PASS, FAIL
from executeur import EXECUTEURS

LIM = Limites(temps_s=45, cpu_s=30, memoire_mo=1500)   # large : compilation (g++/rustc/go) avant exécution

# (langage, runtime requis, solution correcte, solution fausse, non-compilable, tests)
CAS = {
    "cpp": ("g++",
            "int carre(int x){ return x*x; }",
            "int carre(int x){ return x+x; }",
            "int carre(int x){ return x*x }",              # ; manquant
            "    ASSERT(carre(3)==9);\n    ASSERT(carre(4)==16);"),
    "rust": ("rustc",
             "fn carre(x: i64) -> i64 { x*x }",
             "fn carre(x: i64) -> i64 { x + x }",
             "fn carre(x: i64) -> i64 { x*x ",             # accolade manquante
             "    assert!(carre(3)==9);\n    assert_eq!(carre(4), 16);"),
    "go": ("go",
           "func carre(x int) int { return x*x }",
           "func carre(x int) int { return x + x }",
           "func carre(x int) int { return x*x ",          # accolade manquante
           '    if carre(3) != 9 { panic("AssertionError") }\n    if carre(4) != 16 { panic("AssertionError") }'),
}


def main() -> int:
    ok, fails, testes = 0, [], 0

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    for lang, (runtime, bon, faux, cassé, tests) in CAS.items():
        if shutil.which(runtime) is None:
            print(f"  [SKIP] {lang} — runtime '{runtime}' absent (honnête).")
            continue
        testes += 1
        exe = EXECUTEURS[lang]
        vb = juge(bon, tests, LIM, executeur=exe)
        check(f"{lang} CORRECT -> PASS (statut={vb.statut})", vb.passe and vb.statut == PASS)
        vf = juge(faux, tests, LIM, executeur=exe)
        check(f"{lang} FAUX -> FAIL (statut={vf.statut})", not vf.passe and vf.statut == FAIL)
        vc = juge(cassé, tests, LIM, executeur=exe)
        check(f"{lang} NON COMPILABLE -> jamais PASS (statut={vc.statut})", not vc.passe)
        # FAUX=0 transverse : aucun des deux mauvais ne PASSE
        check(f"{lang} FAUX=0 : ni le faux ni le cassé ne PASSENT", not vf.passe and not vc.passe)

    if testes == 0:
        print("  [SKIP] aucun compilateur C++/Rust/Go présent — non testable ici (honnête).")
        print("\n=== valide_executeurs_compiles : 0/0 (skip) ===")
        return 0

    print(f"\n=== valide_executeurs_compiles : {ok}/{ok + len(fails)} ({testes} langage(s) testé(s)) ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
