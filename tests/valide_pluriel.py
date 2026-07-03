"""PLURIEL (brique FORME du langage : accord en NOMBRE) — réglé donc vérifiable.
MUR : substrat ne minte pas le pluriel en -aux/-x. GÉNÉRAL ×2 : réguliers held-out ET familles (-al/-eau/-eu).
HONNÊTE : ne résout pas un irrégulier (oeil->yeux). VIVANT : l'orchestrateur le route."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, GenerateurPluriel, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"pl/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# réguliers (+s) : held-out = mots jamais vus -> niveau 0 généralise.
REG = _t("pluriel", "mot",
    "def check(c):\n    assert c('chat') == 'chats'\n    assert c('table') == 'tables'\ncheck(pluriel)",
    "def check(c):\n    assert c('ami') == 'amis'\n    assert c('mur') == 'murs'\ncheck(pluriel)")
# familles -al/-eau/-eu : seul le niveau 2 passe (held-out = mots jamais vus).
SPE = _t("pluriel", "mot",
    "def check(c):\n    assert c('journal') == 'journaux'\n    assert c('cheveu') == 'cheveux'\ncheck(pluriel)",
    "def check(c):\n    assert c('cheval') == 'chevaux'\n    assert c('tuyau') == 'tuyaux'\ncheck(pluriel)")
# irrégulier total = HORS portée.
HORS = _t("pluriel", "mot",
    "def check(c):\n    assert c('oeil') == 'yeux'\ncheck(pluriel)",
    "def check(c):\n    assert c('oeil') == 'yeux'\ncheck(pluriel)")


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
    pl = GenerateurPluriel()
    r.append(_check("MUR : le substrat ne minte pas le pluriel (familles -al/-eau/-eu held-out)",
                    _resout(GenerateurSubstrat(), SPE) is None))
    r.append(_check("GÉNÉRAL ×2 : réguliers (+s held-out) ET familles (-al->-aux, -eau/-eu->+x held-out)",
                    _resout(pl, REG) is not None and _resout(pl, SPE) is not None))
    r.append(_check("HONNÊTE : ne résout pas `oeil`->`yeux` (irrégulier, hors portée)", _resout(pl, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), pluriel=True)
        e, _, code, _ = resoudre(orch, SPE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (pluriel=True) résout à l'étage `{e}`", code is not None and e == "pluriel"))
    print()
    print("PLURIEL VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
