"""INTRUS / CATÉGORIE COMMUNE (brique COMPRÉHENSION) — logique de catégorie sur le graphe de sens.
MUR : substrat ne minte pas l'intersection des remontées. GÉNÉRAL ×2 : intrus (position variable) ET categorie_commune
sur listes JAMAIS vues. HONNÊTE : pas de catégorie commune -> None. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurIntrus, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

E = ("[('chat','félin'),('félin','mammifère'),('mammifère','animal'),"
     "('chien','canidé'),('canidé','mammifère'),('voiture','véhicule')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"in/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# INTRUS : voiture n'est pas un animal. held-out = intrus en 1re position + autre liste.
INTRUS = _t("intrus", "aretes, mots",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien','voiture']) == 'voiture'\ncheck(intrus)",
    f"def check(c):\n    E={E}\n    assert c(E,['voiture','chat','chien']) == 'voiture'\n    assert c(E,['véhicule','voiture','félin']) == 'félin'\ncheck(intrus)")
# CATÉGORIE COMMUNE : le plus proche ancêtre de tous. held-out = listes neuves.
CAT = _t("categorie_commune", "aretes, mots",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien']) == 'mammifère'\ncheck(categorie_commune)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','félin']) == 'félin'\n    assert c(E,['félin','canidé']) == 'mammifère'\ncheck(categorie_commune)")
# HORS : « compte » des mots = hors famille.
HORS = _t("compte", "aretes, mots",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien']) == 2\ncheck(compte)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','chien']) == 2\ncheck(compte)")


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
    it = GenerateurIntrus()
    r.append(_check("MUR : le substrat ne minte pas l'intersection des remontées (intrus held-out)",
                    _resout(GenerateurSubstrat(), INTRUS) is None))
    r.append(_check("GÉNÉRAL ×2 : intrus (position variable) ET categorie_commune sur listes held-out",
                    _resout(it, INTRUS) is not None and _resout(it, CAT) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(it, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), intrus=True)
        e, _, code, _ = resoudre(orch, INTRUS, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (intrus=True) résout à l'étage `{e}`",
                    code is not None and e == "intrus"))
    print()
    print("INTRUS VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
