"""CONJUGAISON (brique FORME du langage) — conjuguer est RÉGLÉ donc VÉRIFIABLE (le SENS, lui, n'a pas de juge).
MUR : substrat ne minte pas la conjugaison. GÉNÉRAL ×2 : -er réguliers held-out (verbes JAMAIS vus) ET irréguliers
(être/avoir). HONNÊTE : ne résout pas un groupe-2 (finir). VIVANT : l'orchestrateur le route."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurConjugaison, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"cj/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# -er réguliers : VISIBLE = présent ; HELD-OUT = verbe jamais vu (donner) + autres temps (imparfait, futur).
# -> niveau 0 (présent seul) PASSE le visible mais ÉCHOUE le held -> le juge sélectionne niveau 1 (généralise).
REG = _t("conjugue", "inf, t, p",
    "def check(c):\n    assert c('parler','present',0) == 'parle'\n    assert c('parler','present',3) == 'parlons'\ncheck(conjugue)",
    "def check(c):\n    assert c('donner','present',2) == 'donne'\n    assert c('parler','imparfait',4) == 'parliez'\n    assert c('parler','futur',0) == 'parlerai'\ncheck(conjugue)")
# irréguliers : seul le niveau 2 (table) passe.
IRR = _t("conjugue", "inf, t, p",
    "def check(c):\n    assert c('être','present',0) == 'suis'\n    assert c('être','present',2) == 'est'\ncheck(conjugue)",
    "def check(c):\n    assert c('être','present',4) == 'êtes'\n    assert c('avoir','present',0) == 'ai'\ncheck(conjugue)")
# groupe-2 (finir) = HORS portée : aucun niveau ne le résout.
HORS = _t("conjugue", "inf, t, p",
    "def check(c):\n    assert c('finir','present',0) == 'finis'\ncheck(conjugue)",
    "def check(c):\n    assert c('finir','present',3) == 'finissons'\ncheck(conjugue)")


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
    cj = GenerateurConjugaison()
    r.append(_check("MUR : le substrat ne minte pas la conjugaison (-er réguliers held-out)",
                    _resout(GenerateurSubstrat(), REG) is None))
    r.append(_check("GÉNÉRAL ×2 : -er réguliers (verbe held-out + imparfait/futur) ET irréguliers (être/avoir)",
                    _resout(cj, REG) is not None and _resout(cj, IRR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `finir` (groupe-2, hors portée)", _resout(cj, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), conjugaison=True)
        e, _, code, _ = resoudre(orch, REG, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (conjugaison=True) résout à l'étage `{e}`", code is not None and e == "conjugaison"))
    print()
    print("CONJUGAISON VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
