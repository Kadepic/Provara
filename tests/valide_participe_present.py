"""PARTICIPE PRÉSENT (brique FORME, -ant) — forme verbale RÉGLÉE donc VÉRIFIABLE.
MUR : substrat ne minte pas la forme (held-out). GÉNÉRAL ×2 : -er (radical+ant, verbe JAMAIS vu) ET -ir 2ᵉ groupe
(radical+issant). HONNÊTE : ne résout pas un irrégulier (avoir -> 'ayant' ; la brique dit 'avissant'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurParticipePresent, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"pp/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# -er : VISIBLE = parler ; HELD-OUT = verbe jamais vu (donner) -> niveau 0 suffit.
ER = _t("participe_present", "inf",
    "def check(c):\n    assert c('parler') == 'parlant'\ncheck(participe_present)",
    "def check(c):\n    assert c('donner') == 'donnant'\n    assert c('travailler') == 'travaillant'\ncheck(participe_present)")
# -ir 2ᵉ groupe : seul le niveau 1 (-> radical+issant) passe.
IR = _t("participe_present", "inf",
    "def check(c):\n    assert c('finir') == 'finissant'\ncheck(participe_present)",
    "def check(c):\n    assert c('choisir') == 'choisissant'\n    assert c('parler') == 'parlant'\ncheck(participe_present)")
# irrégulier (avoir -> ayant) = HORS portée : la brique produit 'avissant', rejeté par le juge.
HORS = _t("participe_present", "inf",
    "def check(c):\n    assert c('avoir') == 'ayant'\ncheck(participe_present)",
    "def check(c):\n    assert c('savoir') == 'sachant'\ncheck(participe_present)")


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
    pp = GenerateurParticipePresent()
    r.append(_check("MUR : le substrat ne minte pas le participe présent (-er held-out)",
                    _resout(GenerateurSubstrat(), ER) is None))
    r.append(_check("GÉNÉRAL ×2 : -er (verbe held-out) ET -ir 2ᵉ groupe (choisissant, held-out)",
                    _resout(pp, ER) is not None and _resout(pp, IR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `avoir` (radical irrégulier, hors portée)", _resout(pp, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), participe_present=True)
        e, _, code, _ = resoudre(orch, ER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (participe_present=True) résout à l'étage `{e}`",
                    code is not None and e == "participe_present"))
    print()
    print("PARTICIPE PRÉSENT VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
