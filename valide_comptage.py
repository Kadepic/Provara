"""COMPTAGE (brique COMPRÉHENSION — quantitatif) — combien / lesquels d'un ensemble sont d'une catégorie.
MUR : substrat ne minte pas le comptage sur closure. GÉNÉRAL ×2 : combien (nombre) ET lesquels (sous-liste) sur des
ensembles JAMAIS vus. HONNÊTE : membres non-collection -> None (hors famille rejeté). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurComptage, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

E = ("[('chat','félin'),('lion','félin'),('félin','mammifère'),('mammifère','animal'),"
     "('chien','canidé'),('canidé','mammifère'),('voiture','véhicule')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"cb/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


COMBIEN = _t("combien", "aretes, membres, cat",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien','voiture'],'animal') == 2\ncheck(combien)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','lion','chien'],'félin') == 2\n    assert c(E,['voiture'],'animal') == 0\ncheck(combien)")
LESQUELS = _t("lesquels", "aretes, membres, cat",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien','voiture'],'animal') == ['chat','chien']\ncheck(lesquels)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','lion','voiture'],'félin') == ['chat','lion']\ncheck(lesquels)")
HORS = _t("moyenne", "aretes, membres, cat",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien'],'animal') == 1.0\ncheck(moyenne)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien'],'animal') == 1.0\ncheck(moyenne)")


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
    cb = GenerateurComptage()
    r.append(_check("MUR : le substrat ne minte pas le comptage sur closure (combien held-out)",
                    _resout(GenerateurSubstrat(), COMBIEN) is None))
    r.append(_check("GÉNÉRAL ×2 : combien (nombre) ET lesquels (sous-liste) sur ensembles held-out",
                    _resout(cb, COMBIEN) is not None and _resout(cb, LESQUELS) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `moyenne` (hors famille)", _resout(cb, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), comptage=True)
        e, _, code, _ = resoudre(orch, COMBIEN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (comptage=True) résout à l'étage `{e}`",
                    code is not None and e == "comptage"))
    print()
    print("COMPTAGE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
