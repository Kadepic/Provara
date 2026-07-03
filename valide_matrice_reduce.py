"""MATRICE + REDUCE (brique puissante) — réduire les agrégats de lignes/colonnes en un scalaire.
MUR : matrice rend la LISTE des agrégats, pas le scalaire réduit. GÉNÉRAL ×2 : max_row_sum ET min_row_max. HONNÊTE : pas transpose. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMatrice2D, GenerateurMatriceReduce, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"mr/{fn}", point_entree=fn, prompt=f'def {fn}(m):\n    """..."""', tests=tests, tests_held_out=held)


MAXROW = _t("max_row_sum",
    "def check(c):\n    assert c([[1,2],[3,4]]) == 7\n    assert c([[1],[5]]) == 5\ncheck(max_row_sum)",
    "def check(c):\n    assert c([[1,2,3]]) == 6\n    assert c([[1],[2],[3]]) == 3\n    assert c([[5,5],[1,1]]) == 10\ncheck(max_row_sum)")
MINROWMAX = _t("min_row_max",
    "def check(c):\n    assert c([[1,5],[2,3]]) == 3\n    assert c([[9],[1]]) == 1\ncheck(min_row_max)",
    "def check(c):\n    assert c([[1,2],[3,4]]) == 2\n    assert c([[7,7]]) == 7\ncheck(min_row_max)")
TRANSP = _t("transpose",
    "def check(c):\n    assert c([[1,2],[3,4]]) == [[1,3],[2,4]]\ncheck(transpose)",
    "def check(c):\n    assert c([[1,2,3]]) == [[1],[2],[3]]\ncheck(transpose)")


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def _resout(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    r = []
    mr = GenerateurMatriceReduce()
    r.append(_check("MUR : matrice (rend la LISTE des agrégats) ne minte pas max_row_sum (scalaire réduit)",
                    _resout(GenerateurMatrice2D(), MAXROW) is None))
    r.append(_check("GÉNÉRAL ×2 : max_row_sum (max∘sum) ET min_row_max (min∘max) mintés + held-out adverse",
                    _resout(mr, MAXROW) is not None and _resout(mr, MINROWMAX) is not None))
    r.append(_check("HONNÊTE : ne résout pas `transpose` (sortie liste, pas scalaire ; domaine de matrice)",
                    _resout(mr, TRANSP) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), matrice_reduce=True)
        e, _, code, _ = resoudre(orch, MAXROW, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (matrice_reduce=True) résout max_row_sum à l'étage `{e}`", code is not None and e == "matrice-reduce"))
    print()
    print("MATRICE-REDUCE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
