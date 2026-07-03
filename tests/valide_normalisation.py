"""NORMALISATION / ROBUSTESSE (brique SENS : le signal passe malgré le bruit) — variantes bruitées -> action canonique.
MUR : substrat ne minte pas la normalisation. GÉNÉRAL ×2 : casse/espaces (niveau 0) ET synonymes (niveau 1) sur des
variantes JAMAIS vues. HONNÊTE : verbe sans mapping canonique -> HORS. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurNormalisation, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"no/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# casse + espaces : held-out = variantes bruitées JAMAIS vues -> la règle strip+lower généralise (niveau 0).
BRUIT = _t("agir_robuste", "verbe, x",
    "def check(c):\n    assert c('trie',[3,1,2]) == [1,2,3]\n    assert c('  TRIE ',[3,1,2]) == [1,2,3]\ncheck(agir_robuste)",
    "def check(c):\n    assert c(' Trie  ',[9,5,7]) == [5,7,9]\n    assert c('INVERSE',[1,2,3]) == [3,2,1]\ncheck(agir_robuste)")
# synonymes : niveau 1 seul (ranger/inverser -> canonique). held-out = synonymes neufs.
SYN = _t("agir_robuste", "verbe, x",
    "def check(c):\n    assert c('ranger',[3,1,2]) == [1,2,3]\n    assert c('retourner',[1,2,3]) == [3,2,1]\ncheck(agir_robuste)",
    "def check(c):\n    assert c('Trier',[9,5,7]) == [5,7,9]\n    assert c('inverser',[4,5,6]) == [6,5,4]\ncheck(agir_robuste)")
# verbe sans mapping = HORS portée.
HORS = _t("agir_robuste", "verbe, x",
    "def check(c):\n    assert c('mediane',[1,2,3]) == 2\ncheck(agir_robuste)",
    "def check(c):\n    assert c('mediane',[1,2,3]) == 2\ncheck(agir_robuste)")


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
    no = GenerateurNormalisation()
    r.append(_check("MUR : le substrat ne minte pas la normalisation (casse/espaces held-out)",
                    _resout(GenerateurSubstrat(), BRUIT) is None))
    r.append(_check("GÉNÉRAL ×2 : casse/espaces (strip+lower) ET synonymes (ranger/inverser) sur variantes held-out",
                    _resout(no, BRUIT) is not None and _resout(no, SYN) is not None))
    r.append(_check("HONNÊTE : ne résout pas le verbe `mediane` (sans mapping canonique)", _resout(no, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), normalisation=True)
        e, _, code, _ = resoudre(orch, SYN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (normalisation=True) résout à l'étage `{e}`",
                    code is not None and e == "normalisation"))
    print()
    print("NORMALISATION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
