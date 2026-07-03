"""CONJUGAISON GROUPE 2 (-ir en -iss-) — abat le mur `finir` ; réglé donc vérifiable.
MUR : substrat ne minte pas le 2ᵉ groupe. GÉNÉRAL ×2 : présent held-out (verbe jamais vu) ET imparfait/futur.
HONNÊTE & LIMITE : ne résout pas un -ir du 3ᵉ groupe (`partir`) — info lexicale non réglée. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurConjugaison2, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"c2/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# 2ᵉ groupe régulier : VISIBLE = présent `finir` ; HELD-OUT = verbe jamais vu (`choisir`) + imparfait/futur.
REG = _t("conjugue", "inf, t, p",
    "def check(c):\n    assert c('finir','present',0) == 'finis'\n    assert c('finir','present',3) == 'finissons'\ncheck(conjugue)",
    "def check(c):\n    assert c('choisir','present',5) == 'choisissent'\n    assert c('finir','imparfait',3) == 'finissions'\n    assert c('finir','futur',0) == 'finirai'\ncheck(conjugue)")
IMP = _t("conjugue", "inf, t, p",
    "def check(c):\n    assert c('grandir','imparfait',0) == 'grandissais'\ncheck(conjugue)",
    "def check(c):\n    assert c('grandir','imparfait',4) == 'grandissiez'\n    assert c('grandir','futur',2) == 'grandira'\ncheck(conjugue)")
# 3ᵉ groupe (partir) = HORS portée : la finale -ir ne dit PAS le groupe (frontière lexicale du model-free).
HORS = _t("conjugue", "inf, t, p",
    "def check(c):\n    assert c('partir','present',0) == 'pars'\ncheck(conjugue)",
    "def check(c):\n    assert c('partir','present',3) == 'partons'\ncheck(conjugue)")


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
    c2 = GenerateurConjugaison2()
    r.append(_check("MUR : le substrat ne minte pas le 2ᵉ groupe (-iss- held-out)",
                    _resout(GenerateurSubstrat(), REG) is None))
    r.append(_check("GÉNÉRAL ×2 : présent (verbe held-out + imparfait/futur) ET imparfait/futur d'un autre verbe",
                    _resout(c2, REG) is not None and _resout(c2, IMP) is not None))
    r.append(_check("HONNÊTE/LIMITE : ne résout pas `partir` (3ᵉ groupe — la finale -ir ne dit pas le groupe)",
                    _resout(c2, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), conjugaison2=True)
        e, _, code, _ = resoudre(orch, REG, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (conjugaison2=True) résout à l'étage `{e}`",
                    code is not None and e == "conjugaison2"))
    print()
    print("CONJUGAISON GROUPE 2 VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
