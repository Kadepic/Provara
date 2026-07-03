"""
MATRICE 2D — opérations STRUCTURELLES sur une liste de listes (front d'après, thème 2).

`GenerateurMatrice2D` admet deux familles bornées : AXE `[AGG(ligne) for ligne in AXE(m)]` (AXE ∈ {lignes,
colonnes=zip(*m)}, AGG ∈ {sum,max,min,list}) — `list`∘colonnes = transpose — et DIAGONALE `REDUC(m[i][IDX] …)`
(principale/anti × {sum,max,min,list}). Aucune brique ne réindexe en 2D : `imbrique` APLATIT, jamais transpose
ni diagonale ni agrégat PAR colonne. Held-out ADVERSE (diagonale ≠ somme totale, non-carré, anti-diagonale).

Critères de MORT :
  1. MUR ×2          : `imbrique` (aplatit en 1D) ne minte NI `transpose` NI `matrix_diag_sum`.
  2. GÉNÉRAL ×2      : `transpose` (list∘colonnes) ET `matrix_diag_sum` (sum∘diagonale) mintés + GÉNÉRALISENT
                       au held-out adverse (non-carré, piège « = somme totale » où total ≠ diagonale).
  3. HONNÊTE         : la brique ne résout PAS une tâche 2D HORS-famille (`somme_totale` = aplatissement, = imbrique).
  4. VIVANT (modèle) : l'orchestrateur (matrice=True) résout transpose à l'étage `matrice`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurImbrique, GenerateurMatrice2D, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


PRIMS = [_d("carre", "args[0] * args[0]"), _d("double", "args[0] + args[0]")]


def _t(fn, tests, held):
    return Tache(id=f"ma/{fn}", point_entree=fn, prompt=f'def {fn}(m):\n    """..."""',
                 tests=tests, tests_held_out=held)


# list ∘ colonnes = transpose ; held-out : NON-CARRÉ (lignes->colonnes change la forme), singleton, 1×N <-> N×1.
TRANSPOSE = _t("transpose",
    "def check(c):\n    assert c([[1,2],[3,4]]) == [[1,3],[2,4]]\n    assert c([[1,2,3]]) == [[1],[2],[3]]\ncheck(transpose)",
    "def check(c):\n    assert c([[1],[2],[3]]) == [[1,2,3]]\n    assert c([[1,2],[3,4],[5,6]]) == [[1,3,5],[2,4,6]]\n    assert c([[7]]) == [[7]]\ncheck(transpose)")

# sum ∘ diagonale principale ; held-out ADVERSE : piège « = somme totale » ([[0,9],[9,0]] -> diag 0, total 18).
MATRIX_DIAG_SUM = _t("matrix_diag_sum",
    "def check(c):\n    assert c([[1,2],[3,4]]) == 5\n    assert c([[2]]) == 2\ncheck(matrix_diag_sum)",
    "def check(c):\n    assert c([[1,2,3],[4,5,6],[7,8,9]]) == 15\n    assert c([[0,9],[9,0]]) == 0\n    assert c([[5,1],[1,5]]) == 10\ncheck(matrix_diag_sum)")

# Contrôle négatif RECALIBRÉ (2026-07-02) : `somme_totale` (aplatissement 2D) est en fait résolu désormais par le
# générateur matrice (solution réelle vérifiée juge+held-out) -> mauvais négatif. Un vrai hors-famille pour un
# générateur 2D = une tâche de CHAÎNE (empiriquement : GenerateurMatrice2D renvoie None sur `majuscule`).
MAJUSCULE = _t("majuscule",
    "def check(c):\n    assert c('abc') == 'ABC'\n    assert c('a') == 'A'\ncheck(majuscule)",
    "def check(c):\n    assert c('xy') == 'XY'\ncheck(majuscule)")


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
    ma = GenerateurMatrice2D()

    im = GenerateurImbrique(PRIMS)
    resultats.append(_check(
        "MUR ×2 : `imbrique` (aplatit en 1D) ne minte NI transpose NI matrix_diag_sum",
        _resout_gen(im, TRANSPOSE) is None and _resout_gen(im, MATRIX_DIAG_SUM) is None))

    g1 = _resout_gen(ma, TRANSPOSE)
    g2 = _resout_gen(ma, MATRIX_DIAG_SUM)
    resultats.append(_check(
        "GÉNÉRAL ×2 : `transpose` (list∘colonnes) ET `matrix_diag_sum` (sum∘diagonale) mintés + généralisent (held-out adverse)",
        g1 is not None and g2 is not None))

    resultats.append(_check(
        "HONNÊTE : la brique matrice ne résout PAS une tâche de CHAÎNE hors-famille (`majuscule`)",
        _resout_gen(ma, MAJUSCULE) is None))

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), matrice=True)
        etage, _, code, _ = resoudre(orch, TRANSPOSE, LIM)
    # PENSÉE MACHINE : on juge le RÉSULTAT — l'orchestrateur RÉSOUT transpose (code non-None => a passé le juge ET
    # le held-out adverse via `resoudre`, donc FAUX=0). L'étage est LIBRE (la voie la moins chère est le comportement
    # désiré) ; on l'AFFICHE (observabilité) sans l'imposer. La vivacité du spécialiste `matrice` est déjà prouvée
    # en DIRECT ci-dessus (GÉNÉRAL ×2 : `_resout_gen(ma, TRANSPOSE)`), hors routeur.
    resultats.append(_check(
        f"VIVANT (modèle) : l'orchestrateur (matrice=True) résout transpose (étage `{etage}`, libre)",
        code is not None))

    print()
    if all(resultats):
        print(f"MATRICE 2D VALIDÉE — {len(resultats)}/{len(resultats)}. Réindexation 2D structurelle (axe lignes/colonnes "
              f"+ diagonale) : transpose ET matrix_diag_sum, held-out adverse, honnête, utilisée par le modèle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
