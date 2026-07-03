"""
EXECUTEURS DE NICHE — Prolog / R / SQL : trois PARADIGMES (logique, statistique, relationnel), même juge (2026-07-02).

Suite du chantier polyglotte (executeur.py) : « langage » = véhicule, le juge ne bouge pas. Ces trois-là ne sont
pas des langages impératifs de plus — chacun apporte un mode de calcul que Python n'offre pas nativement :
  • Prolog (swipl)  : résolution logique, unification, backtracking — tests = `test(<but>)` (préambule fourni).
  • R (Rscript)     : vecteurs/statistiques — tests = `ASSERT(<cond scalaire>)` (préambule fourni ; sur vecteur,
                      passer par all(...) : isTRUE(c(TRUE,TRUE)) est FAUX, donc un vecteur nu échoue honnêtement).
  • SQL (sqlite3)   : relationnel déclaratif — tests = `INSERT INTO _assert SELECT (<cond>);` contre la table
                      `_assert(ok CONSTRAINT AssertionError CHECK(ok IS 1))` fournie. `IS 1` (pas `= 1`) : un
                      NULL (sous-requête vide…) VIOLE la contrainte au lieu de passer silencieusement (piège
                      CHECK/NULL de SQL neutralisé — vérifié empiriquement sur sqlite 3.45).
CONVENTIONS PROUVÉES contre la réalité (2026-07-02) : PASS exit 0 + sentinelle ; test raté -> « AssertionError »
sur stderr + exit ≠ 0 -> FAIL ; source cassé/but inconnu -> ERROR. FAUX=0 : le verdict vient de l'exécution
réelle ; la sentinelle (imprimée APRÈS les tests) interdit un faux PASS ; un échec de chargement n'est jamais
confondu avec un test raté. La solution ne doit pas définir `main` (Prolog) ni toucher `_assert` (SQL).
"""
from __future__ import annotations

import shlex

from juge import ERROR, FAIL

_TEST_PROLOG = ("test(G) :- ( call(G) -> true ; "
                "( write(user_error, 'AssertionError'), nl(user_error), halt(1) ) ).\n")
_ASSERT_R = 'ASSERT <- function(c) if (!isTRUE(c)) { message("AssertionError"); quit(status=1) }\n'
_ASSERT_SQL = "CREATE TABLE _assert(ok INTEGER CONSTRAINT AssertionError CHECK(ok IS 1));\n"


class ExecuteurProlog:
    """Prolog (swipl). Tests = conjonction de buts `test(...)` ; `main` assemblé ici. Un but non prouvable ->
    AssertionError+halt(1) -> FAIL ; prédicat inconnu / erreur de chargement -> exit 2 sans AssertionError -> ERROR."""

    langage = "prolog"
    fichier = "candidat.pl"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        # jeton alphanumérique -> atome Prolog sûr entre quotes simples.
        return (_TEST_PROLOG + "\n" + solution + "\n\n"
                + f"main :- {tests}, write('{jeton}'), nl.\n")

    def commande(self, chemin: str) -> list[str]:
        # -q : silencieux ; -g main : lance les tests ; -t halt : termine au lieu du REPL (jamais interactif).
        return ["swipl", "-q", "-g", "main", "-t", "halt", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        return FAIL if "AssertionError" in stderr else ERROR


class ExecuteurR:
    """R (Rscript --vanilla : ni profil ni site ni sauvegarde — reproductible). Tests = ASSERT(cond scalaire)."""

    langage = "r"
    fichier = "candidat.R"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return _ASSERT_R + "\n" + solution + "\n\n" + tests + f'\ncat("{jeton}\\n")\n'

    def commande(self, chemin: str) -> list[str]:
        return ["Rscript", "--vanilla", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        return FAIL if "AssertionError" in stderr else ERROR


class ExecuteurSQL:
    """SQL (sqlite3, base :memory: jetable). Solution = DDL/DML/vues ; tests = INSERT INTO _assert SELECT (cond).
    -bail : stoppe à la 1re erreur (la sentinelle n'est jamais imprimée après un échec). Un test faux OU NUL ->
    « CHECK constraint failed: AssertionError » -> FAIL ; SQL invalide -> Parse error -> ERROR."""

    langage = "sql"
    fichier = "candidat.sql"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return _ASSERT_SQL + "\n" + solution + "\n\n" + tests + f"\nSELECT '{jeton}';\n"

    def commande(self, chemin: str) -> list[str]:
        return ["sh", "-c", f"sqlite3 -bail -batch :memory: < {shlex.quote(chemin)}"]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        return FAIL if "AssertionError" in stderr else ERROR


# Registre local (fusionné dans executeur.EXECUTEURS au câblage — ajouter un paradigme = une classe + une entrée).
NICHES = {
    "prolog": ExecuteurProlog(),
    "r": ExecuteurR(),
    "sql": ExecuteurSQL(),
}
