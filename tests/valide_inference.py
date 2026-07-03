"""INFÉRENCE LOGIQUE (brique COMPRÉHENSION — logique) — déduction 3 valeurs (oui/non/inconnu) sur prémisses.
MUR : substrat ne minte pas la déduction transitive + faits négatifs. GÉNÉRAL ×2 : déduction POSITIVE (oui transitif)
ET NÉGATIVE (non par contradiction) sur prémisses held-out. HONNÊTE : conclusion non dérivable -> 'inconnu'. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurInference, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

P = ("[('chat','est','félin'),('félin','est','mammifère'),('mammifère','est','animal'),"
     "('félin','nest_pas','reptile'),('reptile','est','animal')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"if/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# déduction POSITIVE : oui transitif. held-out = conclusion jamais directe (chat->animal).
OUI = _t("deduit", "premisses, x, y",
    f"def check(c):\n    P={P}\n    assert c(P,'chat','mammifère') == 'oui'\ncheck(deduit)",
    f"def check(c):\n    P={P}\n    assert c(P,'chat','animal') == 'oui'\n    assert c(P,'félin','animal') == 'oui'\ncheck(deduit)")
# déduction NÉGATIVE : non par contradiction (chat est félin, félin n'est pas reptile -> chat n'est pas reptile).
NON = _t("deduit", "premisses, x, y",
    f"def check(c):\n    P={P}\n    assert c(P,'chat','reptile') == 'non'\ncheck(deduit)",
    f"def check(c):\n    P={P}\n    assert c(P,'félin','reptile') == 'non'\ncheck(deduit)")
# HONNÊTE : conclusion non dérivable -> 'inconnu' (ne ment jamais).
INCONNU = _t("deduit", "premisses, x, y",
    f"def check(c):\n    P={P}\n    assert c(P,'chat','oiseau') == 'inconnu'\ncheck(deduit)",
    f"def check(c):\n    P={P}\n    assert c(P,'animal','chat') == 'inconnu'\ncheck(deduit)")


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
    inf = GenerateurInference()
    r.append(_check("MUR : le substrat ne minte pas la déduction transitive + négation",
                    _resout(GenerateurSubstrat(), OUI) is None))
    r.append(_check("GÉNÉRAL ×2 : déduction POSITIVE (oui transitif) ET NÉGATIVE (non par contradiction) held-out",
                    _resout(inf, OUI) is not None and _resout(inf, NON) is not None))
    r.append(_check("HONNÊTE : conclusion non dérivable -> 'inconnu' (ne conclut jamais à tort)",
                    _resout(inf, INCONNU) is not None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), inference=True)
        e, _, code, _ = resoudre(orch, OUI, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (inference=True) résout à l'étage `{e}`",
                    code is not None and e == "inference"))
    print()
    print("INFÉRENCE LOGIQUE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
