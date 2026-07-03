"""
FENÊTRE GLISSANTE — agrégat sur les sous-séquences CONTIGUËS de taille k (front d'après, thème 1).

`GenerateurFenetre` admet le schéma général `REDUC(AGG(args[0][i:i+k]) for i in fenêtres)` avec k pris à
l'ENTRÉE (args[1]). REDUC ∈ {max,min,sum,list}, AGG ∈ {sum,max,min}. max_window = max des sommes de fenêtre ;
max_window_min = max des minimums de fenêtre (problème classique « sliding window minimum »). Held-out ADVERSE.

Critères de MORT :
  1. MUR ×2          : ni `comprehension-generale` (replie sur des ÉLÉMENTS filtrés, pas des TRANCHES) ni
                       `positionnel` (strie par parité xs[::2], pas de fenêtre contiguë) ne mintent max_window.
  2. GÉNÉRAL ×2      : `max_window` (max∘sum) ET `max_window_min` (max∘min) mintés + GÉNÉRALISENT au held-out
                       adverse (k=1, k=len, négatifs, fenêtre gagnante au DÉBUT, piège « = max(xs) »).
  3. HONNÊTE         : la brique ne résout PAS une tâche (xs,k) NON-fenêtre (`index_k` = xs[k]) -> pas de fourre-tout.
  4. VIVANT (modèle) : l'orchestrateur (fenetre=True) résout max_window à l'étage `fenetre`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurFenetre,
                        GenerateurOrchestre, GenerateurPositionnel)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


PRIMS = [_d("carre", "args[0] * args[0]"), _d("cube", "args[0] ** 3"), _d("double", "args[0] + args[0]")]
OPS = [_d("add", "args[0] + args[1]"), _d("sub", "args[0] - args[1]"), _d("mul", "args[0] * args[1]")]


def _t(fn, sig, tests, held):
    return Tache(id=f"fe/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


# (max ∘ sum) — max des sommes de fenêtre ; held-out adverse (k=1 -> max élément ; k=len -> somme ; négatifs ;
# fenêtre gagnante au DÉBUT ; piège « somme des k plus grands NON contigus » : [5,1,1,5],k=2 -> 6 (pas 10)).
MAX_WINDOW = _t("max_window", "xs, k",
    "def check(c):\n    assert c([1,2,3,4],2) == 7\n    assert c([5,1,1,5],2) == 6\ncheck(max_window)",
    "def check(c):\n    assert c([1,2,3,4],3) == 9\n    assert c([4,1,1,1],1) == 4\n    assert c([2,2,2],3) == 6\n    assert c([1,5,1,1,1],2) == 6\n    assert c([-3,-1,-2],2) == -3\ncheck(max_window)")

# (max ∘ min) — max des MINIMUMS de fenêtre ; held-out adverse (k=1 -> max élément ; k=len -> min ; piège
# « = max(xs) » : [1,9,1,9,1],k=2 -> 1, surtout pas 9, car aucune fenêtre de 2 n'a un min > 1).
MAX_WINDOW_MIN = _t("max_window_min", "xs, k",
    "def check(c):\n    assert c([1,3,2,4],2) == 2\n    assert c([5,1,5],2) == 1\ncheck(max_window_min)",
    "def check(c):\n    assert c([4,4,1,4],2) == 4\n    assert c([3,1,1],1) == 3\n    assert c([2,2,2],3) == 2\n    assert c([1,9,1,9,1],2) == 1\ncheck(max_window_min)")

# tâche (xs,k) NON-fenêtre : indexer par k. La brique fenêtre ne doit PAS la résoudre (honnêteté).
INDEX_K = _t("index_k", "xs, k",
    "def check(c):\n    assert c([10,20,30],1) == 20\n    assert c([5,6],0) == 5\ncheck(index_k)",
    "def check(c):\n    assert c([7,8,9],2) == 9\ncheck(index_k)")


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
    fe = GenerateurFenetre()

    cg = GenerateurComprehensionGenerale(PRIMS)
    po = GenerateurPositionnel(OPS)
    resultats.append(_check(
        "MUR ×2 : ni `comprehension-generale` (replie sur éléments) ni `positionnel` (strie par parité) ne mintent max_window",
        _resout_gen(cg, MAX_WINDOW) is None and _resout_gen(po, MAX_WINDOW) is None))

    g1 = _resout_gen(fe, MAX_WINDOW)
    g2 = _resout_gen(fe, MAX_WINDOW_MIN)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `max_window` (max∘sum) ET `max_window_min` (max∘min) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : la brique fenêtre ne résout PAS une tâche (xs,k) non-fenêtre (`index_k`)",
        _resout_gen(fe, INDEX_K) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), fenetre=True)
        etage, _, code, _ = resoudre(orch, MAX_WINDOW, LIM)
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (fenetre=True) résout max_window à l'étage `{etage}`",
        code is not None and etage == "fenetre"))

    print()
    if all(resultats):
        print(f"FENÊTRE VALIDÉE — {len(resultats)}/{len(resultats)}. Agrégat sur sous-séquences contiguës de taille k "
              f"(k à l'entrée) : max_window ET max_window_min, held-out adverse, honnête, utilisé par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
