import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import verax_boot  # noqa: F401  -- chemins Provara (src/, ...)
"""
PREUVE que la couture multi-langage tient : le MÊME juge juge du JavaScript.

On définit ici un Executeur JS de ~15 lignes (tout ce qu'il faut pour un 2e
langage), et on montre que le juge — INCHANGÉ — produit les bons verdicts, y
compris que la SENTINELLE attrape `process.exit(0)` en JS comme `sys.exit(0)`
en Python. C'est la démonstration que le langage ne vit QUE dans l'executeur.

Pré-requis : node installé. (Sinon le test s'auto-saute.)
"""

from __future__ import annotations

import shutil

from juge import ERROR, FAIL, Limites, juge


# --- Un 2e backend, écrit en entier ici (la preuve qu'un langage = ~15 lignes) ---

class ExecuteurJS:
    langage = "javascript"
    fichier = "candidat.js"

    def assemble(self, solution: str, tests: str, jeton: str) -> str:
        # solution + tests + sentinelle (console.log), dans la syntaxe JS.
        return f"{solution}\n\n{tests}\n\nconsole.log({jeton!r});\n"

    def commande(self, chemin: str) -> list[str]:
        return ["node", chemin]

    def classe_echec(self, returncode: int, stderr: str) -> str:
        # Node lève une AssertionError (module assert) -> test raté = FAIL.
        return FAIL if "AssertionError" in stderr else ERROR


# --- Les candidats JS ---

SOL_JS = '''
function has_close_elements(numbers, threshold) {
  for (let i = 0; i < numbers.length; i++)
    for (let j = 0; j < numbers.length; j++)
      if (i !== j && Math.abs(numbers[i] - numbers[j]) < threshold) return true;
  return false;
}
'''

TESTS_JS = '''
const assert = require('assert');
assert.strictEqual(has_close_elements([1.0, 2.0, 3.0], 0.5), false);
assert.strictEqual(has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3), true);
assert.strictEqual(has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05), false);
'''


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    if not shutil.which("node"):
        print("node absent : preuve polyglotte sautée (mais la couture est en place).")
        return 0

    js = ExecuteurJS()
    # V8 réserve beaucoup de mémoire virtuelle -> on desserre RLIMIT_AS pour node.
    lim = Limites(temps_s=5, cpu_s=4, memoire_mo=4096)
    resultats = []

    print("Le MÊME juge, sur du JavaScript (executeur JS branché) :\n")

    v = juge(SOL_JS, TESTS_JS, lim, executeur=js)
    resultats.append(_check(f"solution JS correcte -> pass (vu: {v.statut})", v.passe))

    faux = SOL_JS.replace("return true;", "return false;")
    v = juge(faux, TESTS_JS, lim, executeur=js)
    resultats.append(_check(f"solution JS fausse -> fail (vu: {v.statut})", v.statut == FAIL))

    boucle = SOL_JS + "\nwhile (true) {}\n"
    v = juge(boucle, TESTS_JS, Limites(temps_s=3, cpu_s=2, memoire_mo=4096), executeur=js)
    resultats.append(_check(f"boucle infinie JS -> timeout (vu: {v.statut})", v.statut == "timeout"))

    # LE point : la sentinelle est agnostique. process.exit(0) avant les tests.
    exploit = "process.exit(0);\n" + SOL_JS
    v = juge(exploit, TESTS_JS, lim, executeur=js)
    resultats.append(_check(f"exploit JS (process.exit(0)) -> sabotage (vu: {v.statut})",
                            v.statut == "sabotage"))

    print()
    if all(resultats):
        print(f"PREUVE FAITE — {len(resultats)}/{len(resultats)}. Le juge est polyglotte : "
              f"un langage = un executeur, le reste ne bouge pas. (PHP pour Kadepic = pareil.)")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
