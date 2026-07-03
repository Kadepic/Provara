"""IMPÉRATIF (brique FORME, mode) — forme RÉGLÉE donc VÉRIFIABLE (-er : le -s tombe à la 2ᵉ sing.).
MUR : substrat ne minte pas la forme (held-out). GÉNÉRAL ×2 : -er (radical+[e,ons,ez], verbe JAMAIS vu) ET -ir 2ᵉ
groupe (radical+[is,issons,issez]). HONNÊTE : ne résout pas un irrégulier (être -> 'sois' ; la brique dit 'ête'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurImperatif, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"im/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# -er : VISIBLE = parler (les 3 personnes) ; HELD-OUT = verbe jamais vu (donner) -> niveau 0 suffit.
ER = _t("imperatif", "inf, p",
    "def check(c):\n    assert c('parler',0) == 'parle'\n    assert c('parler',1) == 'parlons'\n    assert c('parler',2) == 'parlez'\ncheck(imperatif)",
    "def check(c):\n    assert c('donner',0) == 'donne'\n    assert c('travailler',2) == 'travaillez'\ncheck(imperatif)")
# -ir 2ᵉ groupe : seul le niveau 1 passe.
IR = _t("imperatif", "inf, p",
    "def check(c):\n    assert c('finir',0) == 'finis'\ncheck(imperatif)",
    "def check(c):\n    assert c('choisir',1) == 'choisissons'\n    assert c('parler',0) == 'parle'\ncheck(imperatif)")
# irrégulier (être -> sois) = HORS portée : la brique produit 'ête', rejeté par le juge.
HORS = _t("imperatif", "inf, p",
    "def check(c):\n    assert c('être',0) == 'sois'\ncheck(imperatif)",
    "def check(c):\n    assert c('avoir',0) == 'aie'\ncheck(imperatif)")


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
    im = GenerateurImperatif()
    r.append(_check("MUR : le substrat ne minte pas l'impératif (-er held-out)",
                    _resout(GenerateurSubstrat(), ER) is None))
    r.append(_check("GÉNÉRAL ×2 : -er (verbe held-out) ET -ir 2ᵉ groupe (choisissons, held-out)",
                    _resout(im, ER) is not None and _resout(im, IR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `être` (irrégulier, hors portée)", _resout(im, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), imperatif=True)
        e, _, code, _ = resoudre(orch, ER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (imperatif=True) résout à l'étage `{e}`",
                    code is not None and e == "imperatif"))
    print()
    print("IMPÉRATIF VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
