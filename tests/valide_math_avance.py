"""MATH AVANCÉ (faculté analyse/calcul) — isqrt/lcm/comb/pow_mod. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurMathAvance, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, sig, tests, held):
    return Tache(id=f"math/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
ISQRT = _t("isqrt", "n", "def check(c):\n    assert c(9)==3\n    assert c(16)==4\ncheck(isqrt)",
           "def check(c):\n    assert c(0)==0\n    assert c(99)==9\n    assert c(1)==1\ncheck(isqrt)")
LCM = _t("lcm", "a, b", "def check(c):\n    assert c(4,6)==12\n    assert c(3,5)==15\ncheck(lcm)",
         "def check(c):\n    assert c(2,8)==8\n    assert c(7,3)==21\ncheck(lcm)")
SC = _t("somme_carres", "xs", "def check(c):\n    assert c([1,2,3])==14\ncheck(somme_carres)",
        "def check(c):\n    assert c([2,3])==13\ncheck(somme_carres)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurMathAvance()
    r.append(_ck("MUR : comprehension-generale ne minte pas isqrt", _r(GenerateurComprehensionGenerale([]), ISQRT) is None))
    r.append(_ck("GÉNÉRAL ×2 : isqrt ET lcm + held-out", _r(G, ISQRT) is not None and _r(G, LCM) is not None))
    r.append(_ck("HONNÊTE : ne résout pas somme_carres", _r(G, SC) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), math_avance=True)
        e, _, code, _ = resoudre(orch, ISQRT, LIM)
    r.append(_ck(f"VIVANT : résolu à `{e}`", code is not None and e == "math-avance"))
    print(); print("MATH AVANCÉ VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4."); return 0 if all(r) else 1
raise SystemExit(main())
