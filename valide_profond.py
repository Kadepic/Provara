"""RÉCURSION SUR STRUCTURE (brique puissante) — réduire les feuilles d'une imbrication de profondeur ARBITRAIRE.
MUR : imbrique n'aplatit qu'UN niveau. GÉNÉRAL ×2 : flatten_deep (list) ET somme_deep (sum). HONNÊTE : pas reverse. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurImbrique, GenerateurOrchestre, GenerateurProfond
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _d(n, c):
    return (n, f"def {n}(*args, **kwargs):\n    return {c}\n")


def _t(fn, tests, held):
    return Tache(id=f"pf/{fn}", point_entree=fn, prompt=f'def {fn}(x):\n    """..."""', tests=tests, tests_held_out=held)


FLAT = _t("flatten_deep",
    "def check(c):\n    assert c([1,[2,[3]]]) == [1,2,3]\n    assert c([1,2]) == [1,2]\ncheck(flatten_deep)",
    "def check(c):\n    assert c([[1,[2]],3]) == [1,2,3]\n    assert c([]) == []\n    assert c([[[5]]]) == [5]\ncheck(flatten_deep)")
SOMME = _t("somme_deep",
    "def check(c):\n    assert c([1,[2,[3]]]) == 6\n    assert c([1,2]) == 3\ncheck(somme_deep)",
    "def check(c):\n    assert c([[1],[2,[3]]]) == 6\n    assert c([10]) == 10\ncheck(somme_deep)")
REVERSE = _t("inverse",
    "def check(c):\n    assert c([1,2,3]) == [3,2,1]\ncheck(inverse)",
    "def check(c):\n    assert c([1,2]) == [2,1]\ncheck(inverse)")


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
    pf = GenerateurProfond()
    r.append(_check("MUR : imbrique (1 niveau) ne minte pas flatten_deep (profondeur arbitraire)",
                    _resout(GenerateurImbrique([_d("carre", "args[0]*args[0]")]), FLAT) is None))
    r.append(_check("GÉNÉRAL ×2 : flatten_deep (list) ET somme_deep (sum) mintés + held-out adverse",
                    _resout(pf, FLAT) is not None and _resout(pf, SOMME) is not None))
    r.append(_check("HONNÊTE : ne résout pas `inverse` (hors-famille)", _resout(pf, REVERSE) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), profond=True)
        e, _, code, _ = resoudre(orch, FLAT, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (profond=True) résout flatten_deep à l'étage `{e}`", code is not None and e == "profond"))
    print()
    print("PROFOND VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
