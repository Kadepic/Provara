"""RELATIONS LEXICALES (brique SENS niv.2 : raisonner sur un graphe de sens) — la CLOSURE généralise, donc vérifiable.
MUR : substrat ne minte pas l'atteignabilité transitive. GÉNÉRAL ×2 : est_un (dirigé transitif) ET est_synonyme
(non dirigé) sur des paires JAMAIS données en direct. HONNÊTE : ne calcule pas `distance` (hors famille). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, GenerateurRelationLexicale, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"rl/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# is-a transitif : held-out = paire atteignable mais SANS arête directe (chat..animal, 3 sauts) -> seule la closure passe.
ESTUN = _t("est_un", "aretes, x, y",
    "E = [('chat','felin'),('felin','mammifere'),('mammifere','animal')]\n"
    "def check(c):\n    assert c(E,'chat','felin') == True\n    assert c(E,'felin','mammifere') == True\ncheck(est_un)",
    "E = [('chat','felin'),('felin','mammifere'),('mammifere','animal')]\n"
    "def check(c):\n    assert c(E,'chat','animal') == True\n    assert c(E,'animal','chat') == False\n"
    "    assert c(E,'chat','chien') == False\ncheck(est_un)")
# synonymie = atteignabilité NON DIRIGÉE : held-out remonte un lien à l'envers (becane->auto) -> dirigé échoue, pas elle.
SYN = _t("est_synonyme", "aretes, x, y",
    "S = [('auto','voiture'),('voiture','bagnole'),('bagnole','becane')]\n"
    "def check(c):\n    assert c(S,'auto','voiture') == True\ncheck(est_synonyme)",
    "S = [('auto','voiture'),('voiture','bagnole'),('bagnole','becane')]\n"
    "def check(c):\n    assert c(S,'auto','becane') == True\n    assert c(S,'becane','auto') == True\ncheck(est_synonyme)")
# `distance` (longueur du chemin) = HORS famille : aucun corps ne rend un entier.
HORS = _t("distance", "aretes, x, y",
    "E = [('a','b'),('b','c')]\ndef check(c):\n    assert c(E,'a','c') == 2\ncheck(distance)",
    "E = [('a','b'),('b','c')]\ndef check(c):\n    assert c(E,'a','c') == 2\ncheck(distance)")


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
    rl = GenerateurRelationLexicale()
    r.append(_check("MUR : le substrat ne minte pas l'atteignabilité transitive (held-out 3 sauts)",
                    _resout(GenerateurSubstrat(), ESTUN) is None))
    r.append(_check("GÉNÉRAL ×2 : est_un (dirigé transitif) ET est_synonyme (non dirigé) sur paires held-out indirectes",
                    _resout(rl, ESTUN) is not None and _resout(rl, SYN) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `distance` (longueur de chemin, hors famille)", _resout(rl, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), relation_lexicale=True)
        e, _, code, _ = resoudre(orch, ESTUN, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (relation_lexicale=True) résout à l'étage `{e}`",
                    code is not None and e == "relation-lexicale"))
    print()
    print("RELATIONS LEXICALES VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
