"""TRANSFORMS DE LISTE — rotation/blocs/entrelace. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurFenetre, GenerateurListeTransforms, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, sig, tests, held):
    return Tache(id=f"lt/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
ROT = _t("rotation", "xs, k", "def check(c):\n    assert c([1,2,3,4],1)==[2,3,4,1]\n    assert c([1,2,3],2)==[3,1,2]\ncheck(rotation)",
         "def check(c):\n    assert c([5,6],1)==[6,5]\n    assert c([1,2,3,4,5],0)==[1,2,3,4,5]\ncheck(rotation)")
BLO = _t("blocs", "xs, k", "def check(c):\n    assert c([1,2,3,4],2)==[[1,2],[3,4]]\n    assert c([1,2,3],2)==[[1,2],[3]]\ncheck(blocs)",
         "def check(c):\n    assert c([1,2,3,4,5,6],3)==[[1,2,3],[4,5,6]]\n    assert c([7],1)==[[7]]\ncheck(blocs)")
SC = _t("somme_carres", "xs", "def check(c):\n    assert c([1,2,3])==14\ncheck(somme_carres)", "def check(c):\n    assert c([2,3])==13\ncheck(somme_carres)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurListeTransforms()
    r.append(_ck("MUR : fenetre (agrégat contigu) ne minte pas rotation", _r(GenerateurFenetre(), ROT) is None))
    r.append(_ck("GÉNÉRAL ×2 : rotation ET blocs + held-out", _r(G, ROT) is not None and _r(G, BLO) is not None))
    r.append(_ck("HONNÊTE : ne résout pas somme_carres", _r(G, SC) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), liste_transforms=True)
        e, _, code, _ = resoudre(orch, ROT, LIM)
    r.append(_ck(f"VIVANT : résolu à `{e}`", code is not None and e == "liste-transforms"))
    print(); print("LISTE-TRANSFORMS VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4."); return 0 if all(r) else 1
raise SystemExit(main())
