"""DÉDUP ORDONNÉE (brique puissante) — état ensembliste (déjà-vus).
MUR : comprehension-generale (réduit, sans état) ne minte pas dedup_preserve. GÉNÉRAL ×2 : dedup_preserve ET nb_distinct. HONNÊTE : pas trie. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurDedup, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _d(n, c):
    return (n, f"def {n}(*args, **kwargs):\n    return {c}\n")


def _t(fn, tests, held):
    return Tache(id=f"dd/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests, tests_held_out=held)


DEDUP = _t("dedup_preserve",
    "def check(c):\n    assert c([1,2,1,3]) == [1,2,3]\n    assert c([5,5]) == [5]\ncheck(dedup_preserve)",
    "def check(c):\n    assert c([3,1,3,1,2]) == [3,1,2]\n    assert c([]) == []\n    assert c([1,2,3]) == [1,2,3]\ncheck(dedup_preserve)")
NDIST = _t("nb_distinct",
    "def check(c):\n    assert c([1,2,1,3]) == 3\n    assert c([5,5]) == 1\ncheck(nb_distinct)",
    "def check(c):\n    assert c([]) == 0\n    assert c([1,2,3]) == 3\ncheck(nb_distinct)")
TRIE = _t("trier",
    "def check(c):\n    assert c([3,1,2]) == [1,2,3]\ncheck(trier)",
    "def check(c):\n    assert c([2,1]) == [1,2]\ncheck(trier)")


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
    dd = GenerateurDedup()
    r.append(_check("MUR : comprehension-generale (sans état) ne minte pas dedup_preserve",
                    _resout(GenerateurComprehensionGenerale([_d("carre", "args[0]*args[0]")]), DEDUP) is None))
    r.append(_check("GÉNÉRAL ×2 : dedup_preserve (liste ordonnée) ET nb_distinct (compte) mintés + held-out adverse",
                    _resout(dd, DEDUP) is not None and _resout(dd, NDIST) is not None))
    r.append(_check("HONNÊTE : ne résout pas `trier` (sorted, hors-famille)", _resout(dd, TRIE) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), dedup=True)
        e, _, code, _ = resoudre(orch, DEDUP, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (dedup=True) résout dedup_preserve à l'étage `{e}`", code is not None and e == "dedup"))
    print()
    print("DEDUP VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
