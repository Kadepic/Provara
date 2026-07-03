"""GRAPHES — voisins/degré/sommets/arête sur liste d'arêtes. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurGraphe, GenerateurGroupBy, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, sig, tests, held):
    return Tache(id=f"gr/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
VOIS = _t("voisins", "edges, n", "def check(c):\n    assert c([(1,2),(1,3),(2,3)],1)==[2,3]\n    assert c([(0,1),(2,1)],2)==[1]\ncheck(voisins)",
          "def check(c):\n    assert c([(1,2)],1)==[2]\n    assert c([(1,2),(1,3)],5)==[]\ncheck(voisins)")
NBS = _t("nb_sommets", "edges", "def check(c):\n    assert c([(1,2),(2,3)])==3\n    assert c([(0,1),(0,2),(0,3)])==4\ncheck(nb_sommets)",
         "def check(c):\n    assert c([(5,5)])==1\n    assert c([(1,2),(3,4)])==4\ncheck(nb_sommets)")
SC = _t("somme_carres", "xs", "def check(c):\n    assert c([1,2,3])==14\ncheck(somme_carres)", "def check(c):\n    assert c([2,3])==13\ncheck(somme_carres)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurGraphe()
    r.append(_ck("MUR : group-by (->dict) ne minte pas voisins (->liste filtrée par sommet)", _r(GenerateurGroupBy(), VOIS) is None))
    r.append(_ck("GÉNÉRAL ×2 : voisins ET nb_sommets + held-out", _r(G, VOIS) is not None and _r(G, NBS) is not None))
    r.append(_ck("HONNÊTE : ne résout pas somme_carres", _r(G, SC) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), graphe=True)
        e, _, code, _ = resoudre(orch, VOIS, LIM)
    r.append(_ck(f"VIVANT : résolu à `{e}`", code is not None and e == "graphe"))
    print(); print("GRAPHE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4."); return 0 if all(r) else 1
raise SystemExit(main())
