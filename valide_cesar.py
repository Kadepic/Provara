"""CHIFFRE DE CÉSAR (brique puissante) — décalage mod 26 (ord/chr).
MUR : substrat (méthodes/littéraux) ne minte pas caesar. GÉNÉRAL ×2 : caesar (encode) ET caesar_decode. HONNÊTE : pas majuscule. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurCesar, GenerateurOrchestre, GenerateurSubstrat
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"ce/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


ENC = _t("caesar", "s, k",
    "def check(c):\n    assert c('abc',1) == 'bcd'\n    assert c('az',1) == 'ba'\ncheck(caesar)",
    "def check(c):\n    assert c('xyz',2) == 'zab'\n    assert c('a',25) == 'z'\n    assert c('',5) == ''\ncheck(caesar)")
DEC = _t("caesar_decode", "s, k",
    "def check(c):\n    assert c('bcd',1) == 'abc'\n    assert c('ba',1) == 'az'\ncheck(caesar_decode)",
    "def check(c):\n    assert c('zab',2) == 'xyz'\n    assert c('z',25) == 'a'\ncheck(caesar_decode)")
MAJ = _t("majuscule", "s, k",
    "def check(c):\n    assert c('abc',0) == 'ABC'\ncheck(majuscule)",
    "def check(c):\n    assert c('xy',0) == 'XY'\ncheck(majuscule)")


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
    ce = GenerateurCesar()
    r.append(_check("MUR : substrat (méthodes/littéraux) ne minte pas caesar (ord/chr + modulo)",
                    _resout(GenerateurSubstrat(), ENC) is None))
    r.append(_check("GÉNÉRAL ×2 : caesar (encode) ET caesar_decode mintés + held-out adverse (wrap, k=25, vide)",
                    _resout(ce, ENC) is not None and _resout(ce, DEC) is not None))
    r.append(_check("HONNÊTE : ne résout pas `majuscule` (hors-famille)", _resout(ce, MAJ) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), cesar=True)
        e, _, code, _ = resoudre(orch, ENC, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (cesar=True) résout caesar à l'étage `{e}`", code is not None and e == "cesar"))
    print()
    print("CÉSAR VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
