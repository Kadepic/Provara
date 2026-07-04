"""
LA COUTURE MULTI-LANGAGE — l'Executeur.

Tout ce qui est PROPRE À UN LANGAGE vit ici, et NULLE PART ailleurs. Le juge
(juge.py) devient agnostique : il orchestre la sandbox, les limites, la
sentinelle et la classification universelle, mais il ne sait pas écrire une
ligne de Python, de PHP ou de Rust — il demande à l'Executeur.

C'est l'application directe de la frontière étanche du PLAN-DE-CONSTRUCTION
(le « trait World » : le cœur ne sait pas dans quel monde il vit). Conséquence :

    Ajouter un langage (PHP pour Provara, JS, Rust...) = écrire UN nouvel
    Executeur. Le reste — boucle, store, générateur, observatoire — ne bouge pas.

Un Executeur dit trois choses au juge :
  1. assemble(solution, tests, jeton) -> le source complet à exécuter
     (solution + tests + impression de la sentinelle, dans la syntaxe du langage) ;
  2. commande(chemin) -> la commande qui exécute ce source en sandbox
     (peut compiler+exécuter via un shell pour les langages compilés) ;
  3. classe_echec(returncode, stderr) -> pour une sortie non nulle, traduit
     l'échec dans le vocabulaire UNIVERSEL du juge (test raté vs crash vs OOM),
     car « comment un test signale son échec » dépend du langage.
"""

from __future__ import annotations

import shlex
import sys
import textwrap
from typing import Protocol, runtime_checkable

# Statuts universels : définis par le juge, réutilisés ici pour parler son langage.
from juge import ERROR, FAIL, KILLED


@runtime_checkable
class Executeur(Protocol):
    """Le contrat qu'un backend de langage doit remplir pour que le juge l'utilise."""
    langage: str          # "python", "php", "rust"...
    fichier: str          # nom du fichier source à écrire (ex. "candidat.py")

    def assemble(self, solution: str, tests: str, jeton: str) -> str: ...
    def commande(self, chemin: str) -> list[str]: ...
    def classe_echec(self, returncode: int, stderr: str) -> str: ...


class ExecuteurPython:
    """Le premier backend : Python. Convention de tests = asserts (style HumanEval)."""

    langage = "python"
    fichier = "candidat.py"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        # solution, puis tests, puis la sentinelle imprimée APRÈS les tests.
        # dedent par sécurité si on reçoit du code indenté.
        return (
            textwrap.dedent(solution) + "\n\n"
            + textwrap.dedent(tests) + "\n"
            + f"print({jeton!r})\n"
        )

    def commande(self, chemin: str) -> list[str]:
        # -I : interpréteur isolé (ignore l'environnement, le site-user, les PYTHON*).
        # -S : ne charge PAS site.py -> (1) démarrage ~34 % plus rapide (mesuré : 12,4->8,2 ms/candidat,
        #      gain sur CHAQUE appel juge donc sur tout le système) ; (2) DURCISSEMENT sécurité : neutralise
        #      l'exécution automatique des fichiers .pth (vecteur d'exécution de code à l'import de site).
        # La stdlib reste importable (collections/math/itertools…) — vérifié. Vitesse ET sécurité, sans concession.
        return [sys.executable, "-I", "-S", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        # Sortie non nulle = exception. On traduit dans le vocabulaire du juge.
        if "AssertionError" in stderr:
            return FAIL          # un assert de test a sauté : le code tourne mais se trompe
        if "MemoryError" in stderr:
            return KILLED        # a heurté la limite mémoire de la sandbox
        return ERROR             # syntaxe invalide, exception imprévue, etc.


class ExecuteurJS:
    """JavaScript (node). Tests = module `assert`. Sentinelle = `console.log`. (~15 lignes : un langage = un backend.)"""

    langage = "javascript"
    fichier = "candidat.js"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return f"{solution}\n\n{tests}\n\nconsole.log({jeton!r});\n"

    def commande(self, chemin: str) -> list[str]:
        return ["node", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        return FAIL if "AssertionError" in stderr else ERROR


class ExecuteurPerl:
    """Perl. Convention de tests = `die "AssertionError\\n" unless <cond>;`. Sentinelle = `print`."""

    langage = "perl"
    fichier = "candidat.pl"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return f"{solution}\n\n{tests}\n\nprint {jeton!r}, \"\\n\";\n"

    def commande(self, chemin: str) -> list[str]:
        return ["perl", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        return FAIL if "AssertionError" in stderr else ERROR


class ExecuteurBash:
    """Bash. Convention de tests = `[ "$(f …)" = "<attendu>" ] || {{ echo AssertionError >&2; exit 1; }}`. Sentinelle = `echo`."""

    langage = "bash"
    fichier = "candidat.sh"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return f"{solution}\n\n{tests}\n\necho {jeton}\n"

    def commande(self, chemin: str) -> list[str]:
        return ["bash", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        return FAIL if "AssertionError" in stderr else ERROR


class ExecuteurC:
    """C (gcc) — premier backend COMPILÉ. Le langage de la PERFORMANCE NATIVE. Convention de tests = la macro
    `ASSERT(cond)` (fournie dans le préambule) : sur échec, imprime « AssertionError » sur stderr et `return 1`.
    `commande` COMPILE puis EXÉCUTE via un shell (recette prévue pour les langages compilés) ; un échec de
    compilation (gcc rend non-zéro, message « error: ») -> ERROR, un ASSERT sauté -> FAIL. La sentinelle est
    imprimée par le main APRÈS les tests. FAUX=0 : le verdict vient de l'exécution réelle, la sentinelle interdit
    un faux PASS (cf. juge)."""

    langage = "c"
    fichier = "candidat.c"
    _PREAMBULE = ("#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n"
                  "#define ASSERT(c) do{ if(!(c)){ fprintf(stderr,\"AssertionError\\n\"); return 1; } }while(0)\n")

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        # Le jeton est alphanumérique (JUGE_SENTINELLE_ + hex) -> sûr en littéral string C à guillemets DOUBLES
        # (⚠ jamais {jeton!r} : les quotes simples de Python feraient un char C, pas une string -> crash printf).
        return (self._PREAMBULE + "\n" + solution + "\n\n"
                + "int main(void){\n" + tests + "\n"
                + f'    printf("{jeton}\\n");\n    return 0;\n}}\n')

    def commande(self, chemin: str) -> list[str]:
        binaire = chemin + ".bin"
        # -O0 : compilation rapide ; -std=c11 ; -lm pour math.h. Compile PUIS exécute ; `&&` -> si la compilation
        # échoue le binaire n'est pas lancé (returncode = celui de gcc, stderr = ses « error: »). Chemins quotés.
        cmd = (f"gcc -std=c11 -O0 -w -o {shlex.quote(binaire)} {shlex.quote(chemin)} -lm "
               f"&& {shlex.quote(binaire)}")
        return ["sh", "-c", cmd]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        if "AssertionError" in stderr:
            return FAIL          # un ASSERT de test a sauté : compile et tourne, mais se trompe
        if "error:" in stderr:
            return ERROR         # échec de COMPILATION gcc (jamais confondu avec un test raté)
        return ERROR             # crash à l'exécution / autre


class ExecuteurCpp:
    """C++ (g++). Patron ExecuteurC : macro `ASSERT`, sentinelle via printf, compile && exécute. STL disponible."""

    langage = "cpp"
    fichier = "candidat.cpp"
    _PREAMBULE = ("#include <cstdio>\n#include <cstdlib>\n#include <cmath>\n#include <cstring>\n"
                  "#include <string>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n"
                  "#define ASSERT(c) do{ if(!(c)){ fprintf(stderr,\"AssertionError\\n\"); return 1; } }while(0)\n")

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return (self._PREAMBULE + "\n" + solution + "\n\nint main(){\n" + tests + "\n"
                + f'    printf("{jeton}\\n");\n    return 0;\n}}\n')

    def commande(self, chemin: str) -> list[str]:
        binaire = chemin + ".bin"
        cmd = (f"g++ -std=c++17 -O0 -w -o {shlex.quote(binaire)} {shlex.quote(chemin)} "
               f"&& {shlex.quote(binaire)}")
        return ["sh", "-c", cmd]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        if "AssertionError" in stderr:
            return FAIL
        return ERROR                 # "error:" de g++ ou crash


class ExecuteurRust:
    """Rust (rustc). Tests = `assert!`/`assert_eq!` NATIFS (panic sur échec). La sentinelle est println! après les
    tests ; un assert raté panique -> stderr « panicked » -> FAIL ; erreur de compilation « error[…] » -> ERROR."""

    langage = "rust"
    fichier = "candidat.rs"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return (solution + "\n\nfn main(){\n" + tests + "\n"
                + f'    println!("{jeton}");\n}}\n')

    def commande(self, chemin: str) -> list[str]:
        binaire = chemin + ".bin"
        cmd = (f"rustc -A warnings -O -o {shlex.quote(binaire)} {shlex.quote(chemin)} "
               f"&& {shlex.quote(binaire)}")
        return ["sh", "-c", cmd]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        if "panicked" in stderr:
            return FAIL              # assert! raté = test échoué (le code compile et tourne)
        return ERROR                 # error[E…] de rustc, ou crash


class ExecuteurGo:
    """Go (go run : compile+exécute en une commande). Tests = `if <faux> { panic("AssertionError") }`. Sentinelle
    = fmt.Println après les tests. Panic -> FAIL ; erreur de compilation -> ERROR."""

    langage = "go"
    fichier = "candidat.go"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        return ('package main\n\nimport "fmt"\n\n' + solution + "\n\nfunc main(){\n" + tests + "\n"
                + f'    fmt.Println("{jeton}")\n}}\n')

    def commande(self, chemin: str) -> list[str]:
        # go run compile dans GOCACHE puis exécute. Un import inutilisé est une ERREUR de compil (Go strict) ;
        # `fmt` est toujours utilisé par la sentinelle -> pas de faux positif de ce côté.
        return ["sh", "-c", f"go run {shlex.quote(chemin)}"]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        if "panic" in stderr and "AssertionError" in stderr:
            return FAIL              # panic("AssertionError") = test échoué
        return ERROR                 # erreur de compilation / autre panic


# Registre des backends. Ajouter un langage = une classe ci-dessus + une entrée ici. Le juge ne bouge pas.
# (PHP/Ruby… : même recette ; les compilés suivent le patron ExecuteurC — compile && exécute.)
from executeur_niches import ExecuteurProlog, ExecuteurR, ExecuteurSQL   # 3 PARADIGMES (logique/stats/relationnel)

EXECUTEURS = {
    "python": ExecuteurPython(),
    "javascript": ExecuteurJS(),
    "perl": ExecuteurPerl(),
    "bash": ExecuteurBash(),
    "c": ExecuteurC(),
    "cpp": ExecuteurCpp(),
    "rust": ExecuteurRust(),
    "go": ExecuteurGo(),
    "prolog": ExecuteurProlog(),
    "r": ExecuteurR(),
    "sql": ExecuteurSQL(),
}

# Le backend par défaut (Python). On passe un autre executeur au juge pour changer de langage.
DEFAUT = EXECUTEURS["python"]
