"""COMPRÉHENSION DE DÉFINITION (brique COMPRÉHENSION) — décomposer une définition en genre + différence.
MUR : substrat ne minte pas l'extraction genre/traits. GÉNÉRAL ×2 : genus (1er nom) ET differentia (adjectifs) sur des
définitions JAMAIS vues. HONNÊTE : hors famille -> rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurComprehensionDefinition, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

C = ("{'petit':'adjectif','grand':'adjectif','domestique':'adjectif','rapide':'adjectif','rouge':'adjectif',"
     "'mammifère':'nom','félin':'nom','animal':'nom','engin':'nom','transport':'nom','véhicule':'nom'}")


def _t(fn, sig, tests, held):
    return Tache(id=f"cd/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# GENUS : la catégorie = 1er nom. held-out = définitions neuves.
GENUS = _t("genus", "classes, definition",
    f"def check(c):\n    C={C}\n    assert c(C,'petit mammifère félin domestique') == 'mammifère'\ncheck(genus)",
    f"def check(c):\n    C={C}\n    assert c(C,'grand engin de transport') == 'engin'\n    assert c(C,'rapide véhicule rouge') == 'véhicule'\ncheck(genus)")
# DIFFERENTIA : les traits = adjectifs. held-out = définitions neuves.
DIFF = _t("differentia", "classes, definition",
    f"def check(c):\n    C={C}\n    assert c(C,'petit mammifère félin domestique') == ['petit','domestique']\ncheck(differentia)",
    f"def check(c):\n    C={C}\n    assert c(C,'grand véhicule rouge rapide') == ['grand','rouge','rapide']\ncheck(differentia)")
# HORS : compter les mots = hors famille.
HORS = _t("compte", "classes, definition",
    f"def check(c):\n    C={C}\n    assert c(C,'petit mammifère') == 2\ncheck(compte)",
    f"def check(c):\n    C={C}\n    assert c(C,'petit mammifère') == 2\ncheck(compte)")


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
    cd = GenerateurComprehensionDefinition()
    r.append(_check("MUR : le substrat ne minte pas l'extraction genre/traits (genus held-out)",
                    _resout(GenerateurSubstrat(), GENUS) is None))
    r.append(_check("GÉNÉRAL ×2 : genus (1er nom) ET differentia (adjectifs) sur définitions held-out",
                    _resout(cd, GENUS) is not None and _resout(cd, DIFF) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(cd, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), comprehension_definition=True)
        e, _, code, _ = resoudre(orch, GENUS, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (comprehension_definition=True) résout à l'étage `{e}`",
                    code is not None and e == "comprehension-definition"))
    print()
    print("COMPRÉHENSION DE DÉFINITION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
