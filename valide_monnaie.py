"""RENDU DE MONNAIE (brique puissante) — DP d'optimisation (min pièces).
MUR : generer-tester (compter) ne minte pas coin_change. GÉNÉRAL ×2 : coin_change (min) ET peut_rendre (bool). HONNÊTE : pas somme. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurGenererTester, GenerateurMonnaie, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"mo/{fn}", point_entree=fn, prompt=f'def {fn}(coins, montant):\n    """..."""', tests=tests, tests_held_out=held)


COIN = _t("coin_change",
    "def check(c):\n    assert c([1,2,5],11) == 3\n    assert c([2],3) == -1\ncheck(coin_change)",
    "def check(c):\n    assert c([1],5) == 5\n    assert c([3,5],9) == 3\n    assert c([2,5],0) == 0\ncheck(coin_change)")
PEUT = _t("peut_rendre",
    "def check(c):\n    assert c([2,5],9) is True\n    assert c([2],3) is False\ncheck(peut_rendre)",
    "def check(c):\n    assert c([1],5) is True\n    assert c([5],0) is True\n    assert c([4,6],7) is False\ncheck(peut_rendre)")
SOMME = _t("somme",
    "def check(c):\n    assert c([1,2,3],0) == 6\ncheck(somme)",
    "def check(c):\n    assert c([4,4],0) == 8\ncheck(somme)")


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
    mo = GenerateurMonnaie()
    r.append(_check("MUR : generer-tester (compter) ne minte pas coin_change (DP min)",
                    _resout(GenerateurGenererTester([]), COIN) is None))
    r.append(_check("GÉNÉRAL ×2 : coin_change (min pièces) ET peut_rendre (bool) mintés + held-out adverse",
                    _resout(mo, COIN) is not None and _resout(mo, PEUT) is not None))
    r.append(_check("HONNÊTE : ne résout pas `somme` (réduction simple, hors-famille)", _resout(mo, SOMME) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), monnaie=True)
        e, _, code, _ = resoudre(orch, COIN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (monnaie=True) résout coin_change à l'étage `{e}`", code is not None and e == "monnaie"))
    print()
    print("MONNAIE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
