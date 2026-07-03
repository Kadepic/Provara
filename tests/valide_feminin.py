"""FÉMININ (brique FORME du langage : accord en GENRE des adjectifs) — réglé donc vérifiable.
MUR : substrat ne minte pas le féminin en -euse/-ère/-ve. GÉNÉRAL ×2 : réguliers held-out ET familles (-eux/-er/-f).
HONNÊTE : ne résout pas un irrégulier (beau->belle). VIVANT : l'orchestrateur le route."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurFeminin, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"fm/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# réguliers (+e) : held-out = mots jamais vus -> niveau 0 généralise.
REG = _t("feminin", "adj",
    "def check(c):\n    assert c('grand') == 'grande'\n    assert c('petit') == 'petite'\ncheck(feminin)",
    "def check(c):\n    assert c('vert') == 'verte'\n    assert c('joli') == 'jolie'\ncheck(feminin)")
# familles -eux/-er/-f : seul le niveau 2 passe (held-out = mots jamais vus).
SPE = _t("feminin", "adj",
    "def check(c):\n    assert c('heureux') == 'heureuse'\n    assert c('actif') == 'active'\ncheck(feminin)",
    "def check(c):\n    assert c('joyeux') == 'joyeuse'\n    assert c('leger') == 'legère'\n    assert c('sportif') == 'sportive'\ncheck(feminin)")
# irrégulier = HORS portée.
HORS = _t("feminin", "adj",
    "def check(c):\n    assert c('beau') == 'belle'\ncheck(feminin)",
    "def check(c):\n    assert c('beau') == 'belle'\ncheck(feminin)")


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
    fm = GenerateurFeminin()
    r.append(_check("MUR : le substrat ne minte pas le féminin (familles -eux/-er/-f held-out)",
                    _resout(GenerateurSubstrat(), SPE) is None))
    r.append(_check("GÉNÉRAL ×2 : réguliers (+e held-out) ET familles (-eux->-euse, -er->-ère, -f->-ve held-out)",
                    _resout(fm, REG) is not None and _resout(fm, SPE) is not None))
    r.append(_check("HONNÊTE : ne résout pas `beau`->`belle` (irrégulier, hors portée)", _resout(fm, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), feminin=True)
        e, _, code, _ = resoudre(orch, SPE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (feminin=True) résout à l'étage `{e}`", code is not None and e == "feminin"))
    print()
    print("FÉMININ VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
