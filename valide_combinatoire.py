"""COMBINATOIRE GÉNÉRATIVE — permutations/sous-ensembles/produit. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurCombinatoire, GenerateurComprehensionGenerale, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, sig, tests, held):
    return Tache(id=f"cb/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
PERM = _t("permutations", "xs", "def check(c):\n    assert c([1,2])==[[1,2],[2,1]]\n    assert c([1])==[[1]]\ncheck(permutations)",
          "def check(c):\n    assert c([])==[[]]\n    assert c([1,2,3])==[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]\ncheck(permutations)")
SE = _t("sous_ensembles", "xs", "def check(c):\n    assert c([1,2])==[[],[1],[2],[1,2]]\n    assert c([1])==[[],[1]]\ncheck(sous_ensembles)",
        "def check(c):\n    assert c([])==[[]]\ncheck(sous_ensembles)")
SC = _t("somme_carres", "xs", "def check(c):\n    assert c([1,2,3])==14\ncheck(somme_carres)", "def check(c):\n    assert c([2,3])==13\ncheck(somme_carres)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurCombinatoire()
    r.append(_ck("MUR : comprehension-generale ne minte pas permutations (énumération structurelle)", _r(GenerateurComprehensionGenerale([]), PERM) is None))
    r.append(_ck("GÉNÉRAL ×2 : permutations ET sous_ensembles + held-out", _r(G, PERM) is not None and _r(G, SE) is not None))
    r.append(_ck("HONNÊTE : ne résout pas somme_carres", _r(G, SC) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), combinatoire=True)
        e, _, code, _ = resoudre(orch, PERM, LIM)
    r.append(_ck(f"VIVANT : résolu à `{e}`", code is not None and e == "combinatoire"))
    print(); print("COMBINATOIRE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4."); return 0 if all(r) else 1
raise SystemExit(main())
