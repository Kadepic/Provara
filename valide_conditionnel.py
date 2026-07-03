"""CONDITIONNEL PRÉSENT (brique FORME, mode) — se bâtit sur l'infinitif + terminaisons d'imparfait, RÉGLÉ donc VÉRIFIABLE.
MUR : substrat ne minte pas la forme (held-out). GÉNÉRAL ×2 : -er (verbe JAMAIS vu) ET -ir réguliers (même règle).
HONNÊTE : ne résout pas un -re/irrégulier (prendre -> 'prendrais' ; la brique dit 'prendreais'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurConditionnel, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"cd/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


ER = _t("conditionnel", "inf, p",
    "def check(c):\n    assert c('parler',0) == 'parlerais'\n    assert c('parler',2) == 'parlerait'\ncheck(conditionnel)",
    "def check(c):\n    assert c('donner',4) == 'donneriez'\n    assert c('travailler',3) == 'travaillerions'\ncheck(conditionnel)")
IR = _t("conditionnel", "inf, p",
    "def check(c):\n    assert c('finir',2) == 'finirait'\ncheck(conditionnel)",
    "def check(c):\n    assert c('choisir',0) == 'choisirais'\n    assert c('grandir',5) == 'grandiraient'\ncheck(conditionnel)")
# -re / radical de futur irrégulier = HORS portée : la brique produit 'prendreais', rejeté par le juge.
HORS = _t("conditionnel", "inf, p",
    "def check(c):\n    assert c('prendre',0) == 'prendrais'\ncheck(conditionnel)",
    "def check(c):\n    assert c('être',0) == 'serais'\ncheck(conditionnel)")


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
    cd = GenerateurConditionnel()
    r.append(_check("MUR : le substrat ne minte pas le conditionnel (-er held-out)",
                    _resout(GenerateurSubstrat(), ER) is None))
    r.append(_check("GÉNÉRAL ×2 : -er (verbe held-out) ET -ir réguliers (choisir/grandir held-out)",
                    _resout(cd, ER) is not None and _resout(cd, IR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `prendre` (-re, radical futur irrégulier)", _resout(cd, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), conditionnel=True)
        e, _, code, _ = resoudre(orch, ER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (conditionnel=True) résout à l'étage `{e}`",
                    code is not None and e == "conditionnel"))
    print()
    print("CONDITIONNEL VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
