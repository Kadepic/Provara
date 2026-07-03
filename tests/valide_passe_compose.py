"""PASSÉ COMPOSÉ (brique FORME COMPOSÉE) — temps composé = auxiliaire avoir + participe passé, RÉGLÉ donc VÉRIFIABLE.
MUR : substrat ne minte pas le passé composé (held-out). GÉNÉRAL ×2 : -er réguliers (verbe JAMAIS vu) ET -ir (2ᵉ groupe)
held-out. HONNÊTE : ne résout pas un verbe à auxiliaire ÊTRE (aller -> 'suis allé' ; la brique dit 'ai allé'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurPasseCompose, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"pc/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# -er réguliers : VISIBLE = parler ; HELD-OUT = verbe jamais vu (donner) + autre personne -> niveau 0 (-er) suffit.
REG = _t("passe_compose", "inf, p",
    "def check(c):\n    assert c('parler',0) == 'ai parlé'\n    assert c('parler',3) == 'avons parlé'\ncheck(passe_compose)",
    "def check(c):\n    assert c('donner',2) == 'a donné'\n    assert c('manger',4) == 'avez mangé'\ncheck(passe_compose)")
# -ir (2ᵉ groupe) : seul le niveau 1 (ajoute participe -i) passe -> le juge sélectionne le plus large nécessaire.
IR = _t("passe_compose", "inf, p",
    "def check(c):\n    assert c('finir',0) == 'ai fini'\ncheck(passe_compose)",
    "def check(c):\n    assert c('choisir',2) == 'a choisi'\n    assert c('grandir',5) == 'ont grandi'\ncheck(passe_compose)")
# auxiliaire ÊTRE (aller) = HORS portée : la brique applique avoir -> 'ai allé' ≠ 'suis allé', rejeté par le juge.
HORS = _t("passe_compose", "inf, p",
    "def check(c):\n    assert c('aller',0) == 'suis allé'\ncheck(passe_compose)",
    "def check(c):\n    assert c('aller',2) == 'est allé'\ncheck(passe_compose)")


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
    pc = GenerateurPasseCompose()
    r.append(_check("MUR : le substrat ne minte pas le passé composé (-er réguliers held-out)",
                    _resout(GenerateurSubstrat(), REG) is None))
    r.append(_check("GÉNÉRAL ×2 : -er réguliers (verbe held-out) ET -ir 2ᵉ groupe (choisir/grandir held-out)",
                    _resout(pc, REG) is not None and _resout(pc, IR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `aller` (auxiliaire être, hors portée)", _resout(pc, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), passe_compose=True)
        e, _, code, _ = resoudre(orch, REG, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (passe_compose=True) résout à l'étage `{e}`",
                    code is not None and e == "passe_compose"))
    print()
    print("PASSÉ COMPOSÉ VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
