"""FILTRE PARAMÉTRÉ (brique puissante) — filtrer/réduire par un seuil VENANT DE L'ENTRÉE (args[1]).
MUR : multipasse ne filtre que par un agrégat du tout. GÉNÉRAL ×2 : count_above ET somme_above. HONNÊTE : pas index_k. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurFiltreSeuil, GenerateurMultiPasse, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"fs/{fn}", point_entree=fn, prompt=f'def {fn}(xs, t):\n    """..."""', tests=tests, tests_held_out=held)


COUNT = _t("count_above",
    "def check(c):\n    assert c([1,5,3],2) == 2\n    assert c([1,2],5) == 0\ncheck(count_above)",
    "def check(c):\n    assert c([5,5,5],4) == 3\n    assert c([1],1) == 0\n    assert c([-1,0,1],0) == 1\ncheck(count_above)")
SOMME = _t("somme_above",
    "def check(c):\n    assert c([1,5,3],2) == 8\n    assert c([1,2],5) == 0\ncheck(somme_above)",
    "def check(c):\n    assert c([10,1],5) == 10\n    assert c([3,3],2) == 6\ncheck(somme_above)")
INDEX = _t("index_k",
    "def check(c):\n    assert c([10,20,30],1) == 20\ncheck(index_k)",
    "def check(c):\n    assert c([7,8,9],2) == 9\ncheck(index_k)")


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
    fs = GenerateurFiltreSeuil()
    r.append(_check("MUR : multipasse (filtre par agrégat du tout) ne minte pas count_above (seuil = args[1])",
                    _resout(GenerateurMultiPasse(), COUNT) is None))
    r.append(_check("GÉNÉRAL ×2 : count_above ET somme_above mintés + held-out adverse",
                    _resout(fs, COUNT) is not None and _resout(fs, SOMME) is not None))
    r.append(_check("HONNÊTE : ne résout pas `index_k` = xs[t] (hors-famille)", _resout(fs, INDEX) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), filtre_seuil=True)
        e, _, code, _ = resoudre(orch, COUNT, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (filtre_seuil=True) résout count_above à l'étage `{e}`", code is not None and e == "filtre-seuil"))
    print()
    print("FILTRE-SEUIL VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
