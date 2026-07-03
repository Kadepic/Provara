"""SENS EXÉCUTABLE (brique SENS niv.3, cœur du défi) — un VERBE (mot) -> une ACTION que le juge LANCE (grounding canin).
MUR : substrat ne minte pas la dispatch sur le verbe. GÉNÉRAL ×2 : verbes de base ET max/min (complétude croissante)
appliqués à des arguments JAMAIS vus. HONNÊTE : verbe hors vocabulaire (`mediane`) -> HORS. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, GenerateurSensExecutable, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"se/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# verbes de base {trie, somme} : held-out = MÊMES verbes, arguments JAMAIS vus -> c'est l'action qui est apprise.
BASE = _t("agir", "verbe, x",
    "def check(c):\n    assert c('trie',[3,1,2]) == [1,2,3]\n    assert c('somme',[1,2,3]) == 6\ncheck(agir)",
    "def check(c):\n    assert c('trie',[9,5,7]) == [5,7,9]\n    assert c('somme',[4,5,6]) == 15\ncheck(agir)")
# max/min = niveau 2 seul : force la complétude croissante (niv.0/1 -> KeyError sur 'max').
MAXMIN = _t("agir", "verbe, x",
    "def check(c):\n    assert c('max',[3,1,2]) == 3\n    assert c('min',[3,1,2]) == 1\ncheck(agir)",
    "def check(c):\n    assert c('max',[9,5,7]) == 9\n    assert c('min',[9,5,7]) == 5\ncheck(agir)")
# verbe hors vocabulaire = HORS portée : KeyError, jamais résolu.
HORS = _t("agir", "verbe, x",
    "def check(c):\n    assert c('mediane',[1,2,3,4,5]) == 3\ncheck(agir)",
    "def check(c):\n    assert c('mediane',[1,2,3,4,5]) == 3\ncheck(agir)")


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
    se = GenerateurSensExecutable()
    r.append(_check("MUR : le substrat ne minte pas la dispatch verbe->action (trie + somme)",
                    _resout(GenerateurSubstrat(), BASE) is None))
    r.append(_check("GÉNÉRAL ×2 : verbes de base ET max/min (complétude croissante) sur arguments held-out",
                    _resout(se, BASE) is not None and _resout(se, MAXMIN) is not None))
    r.append(_check("HONNÊTE : ne résout pas le verbe `mediane` (hors vocabulaire)", _resout(se, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), sens_executable=True)
        e, _, code, _ = resoudre(orch, BASE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (sens_executable=True) résout à l'étage `{e}`",
                    code is not None and e == "sens-executable"))
    print()
    print("SENS EXÉCUTABLE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
