"""CHEMIN / EXPLICATION (brique COMPRÉHENSION) — la chaîne qui relie x à y (le « parce que »).
MUR : substrat ne minte pas la reconstruction de chemin (BFS + parents). GÉNÉRAL ×2 : chemin (parcours complet) ET
intermediaires (étapes) sur des paires JAMAIS vues. HONNÊTE : pas de chemin -> None / []. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurChemin, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

E = ("[('chat','félin'),('félin','mammifère'),('mammifère','animal'),"
     "('chien','canidé'),('canidé','mammifère'),('voiture','véhicule')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"ch/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


CHEMIN = _t("chemin", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','animal') == ['chat','félin','mammifère','animal']\ncheck(chemin)",
    f"def check(c):\n    E={E}\n    assert c(E,'chien','animal') == ['chien','canidé','mammifère','animal']\n    assert c(E,'chat','voiture') is None\ncheck(chemin)")
INTER = _t("intermediaires", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','animal') == ['félin','mammifère']\ncheck(intermediaires)",
    f"def check(c):\n    E={E}\n    assert c(E,'chien','mammifère') == ['canidé']\n    assert c(E,'chat','félin') == []\ncheck(intermediaires)")
HORS = _t("distance", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','animal') == 3\ncheck(distance)",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','animal') == 3\ncheck(distance)")


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
    ch = GenerateurChemin()
    r.append(_check("MUR : le substrat ne minte pas la reconstruction de chemin (chemin held-out)",
                    _resout(GenerateurSubstrat(), CHEMIN) is None))
    r.append(_check("GÉNÉRAL ×2 : chemin (parcours complet) ET intermediaires (étapes) sur paires held-out",
                    _resout(ch, CHEMIN) is not None and _resout(ch, INTER) is not None))
    r.append(_check("HONNÊTE : ne renvoie pas la `distance` (autre famille)", _resout(ch, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), chemin=True)
        e, _, code, _ = resoudre(orch, CHEMIN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (chemin=True) résout à l'étage `{e}`",
                    code is not None and e == "chemin"))
    print()
    print("CHEMIN / EXPLICATION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
