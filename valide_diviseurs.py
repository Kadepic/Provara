"""THÉORIE DES DIVISEURS — diviseurs/nb/facteurs premiers. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurDiviseurs, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, tests, held):
    return Tache(id=f"div/{fn}", point_entree=fn, prompt=f'def {fn}(n):\n    """..."""', tests=tests, tests_held_out=held)
DIV = _t("diviseurs", "def check(c):\n    assert c(6)==[1,2,3,6]\n    assert c(12)==[1,2,3,4,6,12]\ncheck(diviseurs)",
         "def check(c):\n    assert c(1)==[1]\n    assert c(7)==[1,7]\ncheck(diviseurs)")
FAC = _t("facteurs_premiers", "def check(c):\n    assert c(12)==[2,2,3]\n    assert c(17)==[17]\ncheck(facteurs_premiers)",
         "def check(c):\n    assert c(8)==[2,2,2]\n    assert c(100)==[2,2,5,5]\ncheck(facteurs_premiers)")
SC = _t("somme_carres", "def check(c):\n    assert c([1,2,3])==14\ncheck(somme_carres)", "def check(c):\n    assert c([2,3])==13\ncheck(somme_carres)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurDiviseurs()
    r.append(_ck("MUR : comprehension-generale ne minte pas diviseurs (itère range(1,n+1))", _r(GenerateurComprehensionGenerale([]), DIV) is None))
    r.append(_ck("GÉNÉRAL ×2 : diviseurs ET facteurs_premiers + held-out", _r(G, DIV) is not None and _r(G, FAC) is not None))
    r.append(_ck("HONNÊTE : ne résout pas somme_carres", _r(G, SC) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), diviseurs=True)
        e, _, code, _ = resoudre(orch, DIV, LIM)
    r.append(_ck(f"VIVANT : résolu à `{e}`", code is not None))
    print(); print("DIVISEURS VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4."); return 0 if all(r) else 1
raise SystemExit(main())
