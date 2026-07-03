#!/usr/bin/env python3
"""
VALIDATION des backends de NICHE Prolog/R/SQL (executeur_niches) — 3 PARADIGMES jugés par le MÊME juge,
sentinelle anti-sabotage. FAUX=0 par paradigme : correct -> PASS ; faux -> FAIL ; source cassé -> ERROR, jamais
PASS ; piège CHECK/NULL de SQL -> FAIL honnête (pas un PASS silencieux). SKIP honnête si runtime absent. Léger.
"""
from __future__ import annotations

import shutil
import sys

from juge import juge, Limites, PASS, FAIL
from executeur_niches import NICHES

LIM = Limites(temps_s=45, cpu_s=30, memoire_mo=1500)   # large : démarrage swipl/Rscript

# (langage, runtime requis, solution correcte, solution fausse, source cassé, tests)
CAS = {
    "prolog": ("swipl",
               "double(X, Y) :- Y is X * 2.",
               "double(X, Y) :- Y is X * 3.",
               "double(X Y) :- .",                      # syntaxe invalide -> but inconnu au lancement
               "test(double(2, 4)), test(double(3, 6)), test(\\+ double(2, 5))"),
    "r": ("Rscript",
          "double <- function(x) x * 2",
          "double <- function(x) x * 3",
          "double <- function(x) x * (2",               # parenthèse ouverte -> parse error
          "ASSERT(double(2) == 4)\nASSERT(all(double(c(1, 3)) == c(2, 6)))"),
    "sql": ("sqlite3",
            "CREATE TABLE t(x INT);\nINSERT INTO t VALUES(1),(2),(3);\n"
            "CREATE VIEW double_somme AS SELECT SUM(x)*2 AS v FROM t;",
            "CREATE TABLE t(x INT);\nINSERT INTO t VALUES(1),(2),(3);\n"
            "CREATE VIEW double_somme AS SELECT SUM(x)*3 AS v FROM t;",
            "CREATE TABL t(x INT);",                    # TABL -> parse error
            "INSERT INTO _assert SELECT (SELECT v FROM double_somme) = 12;"),
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

    for lang, (runtime, bon, faux, casse, tests) in CAS.items():
        if shutil.which(runtime) is None:
            print(f"  [SKIP] {lang} — runtime '{runtime}' absent (honnête).")
            continue
        testes += 1
        exe = NICHES[lang]
        vb = juge(bon, tests, LIM, executeur=exe)
        check(f"{lang} CORRECT -> PASS (statut={vb.statut})", vb.passe and vb.statut == PASS)
        vf = juge(faux, tests, LIM, executeur=exe)
        check(f"{lang} FAUX -> FAIL (statut={vf.statut})", not vf.passe and vf.statut == FAIL)
        vc = juge(casse, tests, LIM, executeur=exe)
        check(f"{lang} CASSÉ -> jamais PASS (statut={vc.statut})", not vc.passe)
        check(f"{lang} FAUX=0 : ni le faux ni le cassé ne PASSENT", not vf.passe and not vc.passe)

    # ── Pièges spécifiques aux paradigmes ──────────────────────────────────────────────────────
    if shutil.which("sqlite3"):
        exe = NICHES["sql"]
        # CHECK/NULL : une sous-requête VIDE donne NULL ; `= 1` laisserait passer, `IS 1` échoue honnêtement.
        v = juge("CREATE TABLE t(x INT);", "INSERT INTO _assert SELECT (SELECT MAX(x) FROM t) = 12;", LIM,
                 executeur=exe)
        check(f"sql PIÈGE NULL : condition sur table vide -> FAIL honnête, jamais PASS (statut={v.statut})",
              not v.passe and v.statut == FAIL)
    if shutil.which("swipl"):
        exe = NICHES["prolog"]
        # Exception (pas simple échec) : type_error dans `is` -> ERROR de chargement/appel, jamais PASS.
        v = juge("double(X, Y) :- Y is X * 2.", "test(double(foo, 4))", LIM, executeur=exe)
        check(f"prolog EXCEPTION (type_error) -> jamais PASS (statut={v.statut})", not v.passe)

    # ── CÂBLAGE (anti-orphelin) : registre executeur + portfolio routeur + environnement ──────
    import executeur, environnement, routeur_langage
    check("CÂBLAGE executeur.EXECUTEURS contient prolog/r/sql",
          all(l in executeur.EXECUTEURS for l in NICHES))
    presents = set(environnement.disponibles())
    attendus = {l for l, (rt, *_r) in CAS.items() if shutil.which(rt)}
    check("CÂBLAGE routeur_langage.backends_disponibles inclut les niches PRÉSENTES",
          attendus <= set(routeur_langage.backends_disponibles()) and attendus <= presents)
    check("CÂBLAGE environnement.executeurs_disponibles inclut les niches présentes (champ à jour)",
          attendus <= set(environnement.executeurs_disponibles()))
    if shutil.which("swipl"):
        lang_exe = routeur_langage.executeur_pour("prolog")
        check("CÂBLAGE routeur_langage.executeur_pour('prolog') -> backend réel",
              lang_exe is not None and lang_exe.langage == "prolog")

    if testes == 0:
        print("  [SKIP] aucun runtime prolog/R/sqlite3 présent — non testable ici (honnête).")
        print("\n=== valide_executeur_niches : 0/0 (skip) ===")
        return 0

    print(f"\n=== valide_executeur_niches : {ok}/{ok + len(fails)} ({testes} paradigme(s) testé(s)) ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
