"""SUBJONCTIF PRÉSENT (brique FORME, mode) — « que je parle », RÉGLÉ donc VÉRIFIABLE.
MUR : substrat ne minte pas la forme (held-out). GÉNÉRAL ×2 : -er (radical+[e,es,e,ions,iez,ent], verbe JAMAIS vu)
ET -ir 2ᵉ groupe (radical+[isse,...]). HONNÊTE : ne résout pas un irrégulier (être -> 'sois' ; la brique dit 'être'... faux). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurSubjonctif, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"sj/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


ER = _t("subjonctif", "inf, p",
    "def check(c):\n    assert c('parler',0) == 'parle'\n    assert c('parler',3) == 'parlions'\ncheck(subjonctif)",
    "def check(c):\n    assert c('donner',1) == 'donnes'\n    assert c('travailler',5) == 'travaillent'\ncheck(subjonctif)")
IR = _t("subjonctif", "inf, p",
    "def check(c):\n    assert c('finir',0) == 'finisse'\ncheck(subjonctif)",
    "def check(c):\n    assert c('choisir',3) == 'choisissions'\n    assert c('parler',0) == 'parle'\ncheck(subjonctif)")
# irrégulier (être -> sois) = HORS portée.
HORS = _t("subjonctif", "inf, p",
    "def check(c):\n    assert c('être',0) == 'sois'\ncheck(subjonctif)",
    "def check(c):\n    assert c('avoir',0) == 'aie'\ncheck(subjonctif)")


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
    sj = GenerateurSubjonctif()
    r.append(_check("MUR : le substrat ne minte pas le subjonctif (-er held-out)",
                    _resout(GenerateurSubstrat(), ER) is None))
    r.append(_check("GÉNÉRAL ×2 : -er (verbe held-out) ET -ir 2ᵉ groupe (choisissions, held-out)",
                    _resout(sj, ER) is not None and _resout(sj, IR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `être` (irrégulier, hors portée)", _resout(sj, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), subjonctif=True)
        e, _, code, _ = resoudre(orch, ER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (subjonctif=True) résout à l'étage `{e}`",
                    code is not None and e == "subjonctif"))
    print()
    print("SUBJONCTIF VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
