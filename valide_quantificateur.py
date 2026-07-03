"""QUANTIFICATEURS (brique COMPRÉHENSION — logique) — tous / certains / aucun sur un ensemble, via closure is-a.
MUR : substrat ne minte pas la quantification sur closure. GÉNÉRAL ×2 : tous (universel) ET certains (existentiel)
sur des ensembles JAMAIS vus. HONNÊTE : ne calcule pas une autre quantification hors famille. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurQuantificateur, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

E = ("[('chat','félin'),('lion','félin'),('tigre','félin'),('félin','mammifère'),('mammifère','animal'),"
     "('voiture','véhicule')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"qu/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# TOUS (universel) : tous les membres atteignent la catégorie. held-out = ensembles neufs + cas faux.
TOUS = _t("tous", "aretes, membres, cat",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','lion','tigre'],'félin') == True\ncheck(tous)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','lion'],'animal') == True\n    assert c(E,['chat','voiture'],'animal') == False\ncheck(tous)")
# CERTAINS (existentiel). held-out = au moins un / aucun.
CERTAINS = _t("certains", "aretes, membres, cat",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','voiture'],'animal') == True\ncheck(certains)",
    f"def check(c):\n    E={E}\n    assert c(E,['voiture'],'animal') == False\n    assert c(E,['tigre','voiture'],'mammifère') == True\ncheck(certains)")
# HORS : « combien » (compte) n'est pas dans la famille booléenne.
HORS = _t("combien", "aretes, membres, cat",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','lion'],'félin') == 2\ncheck(combien)",
    f"def check(c):\n    E={E}\n    assert c(E,['chat','lion'],'félin') == 2\ncheck(combien)")


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
    qu = GenerateurQuantificateur()
    r.append(_check("MUR : le substrat ne minte pas la quantification sur closure (tous held-out)",
                    _resout(GenerateurSubstrat(), TOUS) is None))
    r.append(_check("GÉNÉRAL ×2 : tous (universel) ET certains (existentiel) sur ensembles held-out",
                    _resout(qu, TOUS) is not None and _resout(qu, CERTAINS) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `combien` (hors famille booléenne)", _resout(qu, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), quantificateur=True)
        e, _, code, _ = resoudre(orch, TOUS, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (quantificateur=True) résout à l'étage `{e}`",
                    code is not None and e == "quantificateur"))
    print()
    print("QUANTIFICATEURS VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
