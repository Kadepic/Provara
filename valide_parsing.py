"""
PARSING STRUCTURÉ (2026-06-17, faculté « analyse/retranscription ») — chaîne -> dict/liste. `GenerateurParsing`.

Critères de MORT (4) :
  1. MUR        : `mots` (split+join -> CHAÎNE) ne minte pas `paires_kv` (chaîne -> DICT structuré).
  2. GÉNÉRAL ×2 : `paires_kv` ('a=1,b=2'->dict) ET `entiers` ('1 2 3'->[1,2,3]) mintés + held-out adverse.
  3. HONNÊTE   : ne résout pas `reverse_words` (domaine de `mots`, pas du parsing structuré).
  4. VIVANT    : l'orchestrateur (parsing=True) résout `paires_kv` à l'étage `parsing`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMots, GenerateurOrchestre, GenerateurParsing
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"parse/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


KV = _t("paires_kv", "s",
    "def check(c):\n    assert c('a=1,b=2') == {'a':'1','b':'2'}\n    assert c('x=5') == {'x':'5'}\ncheck(paires_kv)",
    "def check(c):\n    assert c('k=v') == {'k':'v'}\n    assert c('p=1,q=2,r=3') == {'p':'1','q':'2','r':'3'}\ncheck(paires_kv)")
ENT = _t("entiers", "s",
    "def check(c):\n    assert c('1 2 3') == [1,2,3]\n    assert c('5') == [5]\ncheck(entiers)",
    "def check(c):\n    assert c('10 20') == [10,20]\n    assert c('7 8 9') == [7,8,9]\ncheck(entiers)")
REVW = _t("reverse_words", "s",
    "def check(c):\n    assert c('a b c') == 'c b a'\ncheck(reverse_words)",
    "def check(c):\n    assert c('x y') == 'y x'\ncheck(reverse_words)")


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def _resout(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    r = []
    ps = GenerateurParsing()
    r.append(_check("MUR : `mots` (-> chaîne) ne minte pas `paires_kv` (-> dict structuré)",
                    _resout(GenerateurMots(), KV) is None))
    r.append(_check("GÉNÉRAL ×2 : `paires_kv` (->dict) ET `entiers` (->liste) mintés + held-out adverse",
                    _resout(ps, KV) is not None and _resout(ps, ENT) is not None))
    r.append(_check("HONNÊTE : ne résout pas `reverse_words` (domaine de `mots`)", _resout(ps, REVW) is None))
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(store, predicteur=Predicteur(store, types=TYPES_RICHES), parsing=True)
        e, _, code, _ = resoudre(orch, KV, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (parsing=True) résout `paires_kv` à l'étage `{e}`",
                    code is not None and e == "parsing"))
    print()
    print("PARSING VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
