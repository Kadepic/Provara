"""
RUN-LENGTH ENCODE — compression stateful avec construction de sortie (front d'après, thème 7).

`GenerateurRunLength` parcourt la chaîne avec état (élément courant + compteur) et CONSTRUIT : format CHAÎNE
('aaabb' -> 'a3b2') ou PAIRES ('aaabb' -> [('a',3),('b',2)]). Distinct de `serie` (qui renvoie une LONGUEUR).

Critères de MORT :
  1. MUR ×2          : ni `serie` (longueur du plus long run) ni `mots` (split/join) ne mintent `compress`.
  2. GÉNÉRAL ×2      : `compress` (chaîne 'a3b2') ET `run_length_pairs` (liste de couples) mintés + GÉNÉRALISENT
                       au held-out adverse (vide -> ''/[], tout pareil 'aaaa'->'a4', alternance 'abab', singleton).
  3. HONNÊTE         : ne résout PAS `inverse` = s[::-1] (transformation hors-famille).
  4. VIVANT (modèle) : l'orchestrateur (run_length=True) résout compress à l'étage `run-length`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurMots, GenerateurOrchestre, GenerateurRunLength, GenerateurSerie)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"rl/{fn}", point_entree=fn, prompt=f'def {fn}(s):\n    """..."""',
                 tests=tests, tests_held_out=held)


# format CHAÎNE ; held-out adverse : vide, tout pareil, alternance (runs de 1), runs mixtes.
COMPRESS = _t("compress",
    "def check(c):\n    assert c('aaabb') == 'a3b2'\n    assert c('x') == 'x1'\ncheck(compress)",
    "def check(c):\n    assert c('') == ''\n    assert c('aaaa') == 'a4'\n    assert c('abab') == 'a1b1a1b1'\n    assert c('aabbbc') == 'a2b3c1'\ncheck(compress)")

# format PAIRES ; held-out adverse : vide -> [], singleton, runs mixtes.
PAIRS = _t("run_length_pairs",
    "def check(c):\n    assert c('aaabb') == [('a',3),('b',2)]\n    assert c('x') == [('x',1)]\ncheck(run_length_pairs)",
    "def check(c):\n    assert c('') == []\n    assert c('aabbbc') == [('a',2),('b',3),('c',1)]\n    assert c('zz') == [('z',2)]\ncheck(run_length_pairs)")

# tâche chaîne hors-famille : inverser. La brique (RLE) ne doit PAS la résoudre.
INVERSE = _t("inverse",
    "def check(c):\n    assert c('abc') == 'cba'\n    assert c('x') == 'x'\ncheck(inverse)",
    "def check(c):\n    assert c('abcd') == 'dcba'\ncheck(inverse)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout_gen(gen, tache, n=400):
    for code in gen.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out
                                                    or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    resultats = []
    rl = GenerateurRunLength()

    resultats.append(_check(
        "MUR ×2 : ni `serie` (longueur du run) ni `mots` (split/join) ne mintent compress",
        _resout_gen(GenerateurSerie(), COMPRESS) is None and _resout_gen(GenerateurMots(), COMPRESS) is None))

    g1 = _resout_gen(rl, COMPRESS)
    g2 = _resout_gen(rl, PAIRS)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `compress` (chaîne) ET `run_length_pairs` (paires) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : ne résout PAS `inverse` = s[::-1] (transformation hors-famille)",
        _resout_gen(rl, INVERSE) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), run_length=True)
        etage, _, code, _ = resoudre(orch, COMPRESS, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (run_length=True) résout compress à l'étage `{etage}`",
        code is not None and etage == "run-length"))

    print()
    if all(resultats):
        print(f"RUN-LENGTH VALIDÉE — {len(resultats)}/{len(resultats)}. Compression stateful avec sortie construite : "
              f"compress ET run_length_pairs, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
