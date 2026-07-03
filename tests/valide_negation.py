"""NÉGATION (brique COMPRÉHENSION — phrase) — comprendre « ne…pas » : détecter et neutraliser.
MUR : substrat ne minte pas la détection des deux marqueurs. GÉNÉRAL ×2 : est_negative (booléen) ET enleve_negation
(noyau affirmatif, « n'est » -> « est ») sur des phrases JAMAIS vues. HONNÊTE : hors famille -> rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurNegation, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"ng/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# EST_NEGATIVE : ne...pas / n'...pas. held-out = phrases neuves + affirmative (False).
EST = _t("est_negative", "phrase",
    "def check(c):\n    assert c('le chat ne mange pas la souris') == True\n    assert c('le chat mange la souris') == False\ncheck(est_negative)",
    "def check(c):\n    assert c(\"le chat n'est pas un oiseau\") == True\n    assert c('le chien ne dort jamais') == True\n    assert c('le chien dort') == False\ncheck(est_negative)")
# ENLEVE_NEGATION : noyau affirmatif. held-out = phrases neuves, « n'est » -> « est ».
ENLEVE = _t("enleve_negation", "phrase",
    "def check(c):\n    assert c('le chat ne mange pas la souris') == 'le chat mange la souris'\ncheck(enleve_negation)",
    "def check(c):\n    assert c(\"le chat n'est pas un oiseau\") == 'le chat est un oiseau'\n    assert c('le chien ne dort plus') == 'le chien dort'\ncheck(enleve_negation)")
# HORS : compter les mots = hors famille.
HORS = _t("compte", "phrase",
    "def check(c):\n    assert c('le chat ne dort pas') == 4\ncheck(compte)",
    "def check(c):\n    assert c('le chat ne dort pas') == 4\ncheck(compte)")


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
    ng = GenerateurNegation()
    r.append(_check("MUR : le substrat ne minte pas la détection des deux marqueurs (est_negative held-out)",
                    _resout(GenerateurSubstrat(), EST) is None))
    r.append(_check("GÉNÉRAL ×2 : est_negative (booléen) ET enleve_negation (noyau affirmatif) sur phrases held-out",
                    _resout(ng, EST) is not None and _resout(ng, ENLEVE) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(ng, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), negation=True)
        e, _, code, _ = resoudre(orch, EST, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (negation=True) résout à l'étage `{e}`",
                    code is not None and e == "negation"))
    print()
    print("NÉGATION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
