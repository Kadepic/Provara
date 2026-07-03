"""LOGIQUE TEMPORELLE (brique COMPRÉHENSION — logique) — ordonner des événements selon « avant » (tri topologique).
MUR : substrat ne minte pas le tri topologique. GÉNÉRAL ×2 : ordonne (ordre complet) ET premier (le 1er) sur des
relations JAMAIS vues. HONNÊTE : hors famille -> rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurTemporel, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

# (a, b) = « a avant b » : lever -> petitdej -> travail -> diner.
R = "[('lever','petitdej'),('petitdej','travail'),('travail','diner')]"


def _t(fn, sig, tests, held):
    return Tache(id=f"tp/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# ORDONNE : ordre chronologique. held-out = événements donnés en désordre, sous-ensembles.
ORDONNE = _t("ordonne", "relations, evenements",
    f"def check(c):\n    R={R}\n    assert c(R,['travail','lever','petitdej']) == ['lever','petitdej','travail']\ncheck(ordonne)",
    f"def check(c):\n    R={R}\n    assert c(R,['diner','lever','travail','petitdej']) == ['lever','petitdej','travail','diner']\ncheck(ordonne)")
# PREMIER : le tout premier. held-out = sous-ensembles.
PREMIER = _t("premier", "relations, evenements",
    f"def check(c):\n    R={R}\n    assert c(R,['travail','lever','petitdej']) == 'lever'\ncheck(premier)",
    f"def check(c):\n    R={R}\n    assert c(R,['diner','travail','petitdej']) == 'petitdej'\ncheck(premier)")
# HORS : « combien » d'événements = hors famille (ordre).
HORS = _t("combien", "relations, evenements",
    f"def check(c):\n    R={R}\n    assert c(R,['lever','travail']) == 2\ncheck(combien)",
    f"def check(c):\n    R={R}\n    assert c(R,['lever','travail']) == 2\ncheck(combien)")


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
    tp = GenerateurTemporel()
    r.append(_check("MUR : le substrat ne minte pas le tri topologique (ordonne held-out)",
                    _resout(GenerateurSubstrat(), ORDONNE) is None))
    r.append(_check("GÉNÉRAL ×2 : ordonne (ordre complet) ET premier (le 1er) sur relations held-out",
                    _resout(tp, ORDONNE) is not None and _resout(tp, PREMIER) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `combien` (hors famille)", _resout(tp, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), temporel=True)
        e, _, code, _ = resoudre(orch, ORDONNE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (temporel=True) résout à l'étage `{e}`",
                    code is not None and e == "temporel"))
    print()
    print("LOGIQUE TEMPORELLE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
