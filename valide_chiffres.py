"""DÉCOMPOSITION DÉCIMALE — somme/nb/inverse des chiffres. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurChiffres, GenerateurComprehensionGenerale, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, tests, held):
    return Tache(id=f"chif/{fn}", point_entree=fn, prompt=f'def {fn}(n):\n    """..."""', tests=tests, tests_held_out=held)
SOM = _t("somme_chiffres", "def check(c):\n    assert c(123)==6\n    assert c(45)==9\ncheck(somme_chiffres)",
         "def check(c):\n    assert c(0)==0\n    assert c(999)==27\n    assert c(10)==1\ncheck(somme_chiffres)")
INV = _t("inverse_chiffres", "def check(c):\n    assert c(123)==321\n    assert c(45)==54\ncheck(inverse_chiffres)",
         "def check(c):\n    assert c(100)==1\n    assert c(7)==7\ncheck(inverse_chiffres)")
SC = _t("somme_carres", "def check(c):\n    assert c([1,2,3])==14\ncheck(somme_carres)", "def check(c):\n    assert c([2,3])==13\ncheck(somme_carres)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurChiffres()
    r.append(_ck("MUR : comprehension-generale ne minte pas somme_chiffres", _r(GenerateurComprehensionGenerale([]), SOM) is None))
    r.append(_ck("GÉNÉRAL ×2 : somme_chiffres ET inverse_chiffres + held-out", _r(G, SOM) is not None and _r(G, INV) is not None))
    r.append(_ck("HONNÊTE : ne résout pas somme_carres", _r(G, SC) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), chiffres=True)
        e, _, code, _ = resoudre(orch, SOM, LIM)
    r.append(_ck(f"VIVANT : résolu à `{e}`", code is not None and e == "chiffres"))
    print(); print("CHIFFRES VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4."); return 0 if all(r) else 1
raise SystemExit(main())
