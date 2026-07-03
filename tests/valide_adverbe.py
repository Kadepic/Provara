"""ADVERBE EN -MENT (brique FORME DÉRIVATION) — dériver un adverbe depuis un adjectif est RÉGLÉ donc VÉRIFIABLE.
MUR : substrat ne minte pas la dérivation (held-out). GÉNÉRAL ×2 : consonne finale (adj+ement, mot JAMAIS vu) ET
-eux (-eusement). HONNÊTE : ne résout pas un adjectif à élision (vrai -> 'vraiment' ; la brique dit 'vraiement'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAdverbe, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"adv/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# consonne finale : VISIBLE = grand/lent ; HELD-OUT = adjectif jamais vu (fort) -> niveau 0 (adj+ement) suffit.
CONS = _t("adverbe", "adj",
    "def check(c):\n    assert c('grand') == 'grandement'\n    assert c('lent') == 'lentement'\ncheck(adverbe)",
    "def check(c):\n    assert c('fort') == 'fortement'\n    assert c('petit') == 'petitement'\ncheck(adverbe)")
# -eux : seul le niveau 1 (-> -eusement) passe -> le juge sélectionne le plus large nécessaire.
EUX = _t("adverbe", "adj",
    "def check(c):\n    assert c('heureux') == 'heureusement'\ncheck(adverbe)",
    "def check(c):\n    assert c('dangereux') == 'dangereusement'\n    assert c('lent') == 'lentement'\ncheck(adverbe)")
# élision du e (vrai -> vraiment) = HORS portée : la brique produit 'vraiement', rejeté par le juge.
HORS = _t("adverbe", "adj",
    "def check(c):\n    assert c('vrai') == 'vraiment'\ncheck(adverbe)",
    "def check(c):\n    assert c('poli') == 'poliment'\ncheck(adverbe)")


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
    adv = GenerateurAdverbe()
    r.append(_check("MUR : le substrat ne minte pas la dérivation (consonne finale held-out)",
                    _resout(GenerateurSubstrat(), CONS) is None))
    r.append(_check("GÉNÉRAL ×2 : consonne finale (adj held-out) ET -eux (-eusement, held-out)",
                    _resout(adv, CONS) is not None and _resout(adv, EUX) is not None))
    r.append(_check("HONNÊTE : ne résout pas `vrai` (élision du e, hors portée)", _resout(adv, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), adverbe=True)
        e, _, code, _ = resoudre(orch, CONS, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (adverbe=True) résout à l'étage `{e}`",
                    code is not None and e == "adverbe"))
    print()
    print("ADVERBE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
