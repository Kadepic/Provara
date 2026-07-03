"""DISTANCE SÉMANTIQUE (brique COMPRÉHENSION) — proximité de sens sur le graphe is-a.
MUR : substrat ne minte pas la double profondeur. GÉNÉRAL ×2 : distance (entier) ET plus_proche (choix) sur paires
JAMAIS vues. HONNÊTE : aucun lien -> None. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurDistanceSemantique, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

E = ("[('chat','félin'),('félin','mammifère'),('mammifère','animal'),"
     "('chien','canidé'),('canidé','mammifère'),('voiture','véhicule')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"ds/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# DISTANCE : chat-chien = 2+2 = 4 ; chat-félin = 1. held-out = paires neuves + sans lien (None).
DIST = _t("distance", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','chien') == 4\ncheck(distance)",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','félin') == 1\n    assert c(E,'chat','voiture') is None\ncheck(distance)")
# PLUS_PROCHE : chat plus proche de chien que de voiture. held-out = autre jeu de candidats.
PROCHE = _t("plus_proche", "aretes, x, cands",
    f"def check(c):\n    E={E}\n    assert c(E,'chat',['chien','voiture']) == 'chien'\ncheck(plus_proche)",
    f"def check(c):\n    E={E}\n    assert c(E,'chien',['chat','voiture']) == 'chat'\ncheck(plus_proche)")
# HORS : « ancetre_commun » (renvoie un nom, pas une distance) n'est pas dans cette famille.
HORS = _t("ancetre_commun", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','chien') == 'mammifère'\ncheck(ancetre_commun)",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','chien') == 'mammifère'\ncheck(ancetre_commun)")


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
    ds = GenerateurDistanceSemantique()
    r.append(_check("MUR : le substrat ne minte pas la double profondeur (distance held-out)",
                    _resout(GenerateurSubstrat(), DIST) is None))
    r.append(_check("GÉNÉRAL ×2 : distance (entier) ET plus_proche (choix) sur paires held-out",
                    _resout(ds, DIST) is not None and _resout(ds, PROCHE) is not None))
    r.append(_check("HONNÊTE : ne renvoie pas l'ancêtre (autre famille) sur le point `ancetre_commun`",
                    _resout(ds, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), distance_semantique=True)
        e, _, code, _ = resoudre(orch, DIST, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (distance_semantique=True) résout à l'étage `{e}`",
                    code is not None and e == "distance-semantique"))
    print()
    print("DISTANCE SÉMANTIQUE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
