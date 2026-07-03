"""NÉGATION (PRODUCTION) — tourner un sens en phrase négative (encadrement ne…pas), RÉGLÉ donc VÉRIFIABLE.
MUR : substrat ne minte pas la forme (held-out). GÉNÉRAL ×2 : -er (ne mange pas, vocab JAMAIS vu) ET élision n'
devant voyelle (n'aime pas). HONNÊTE : verbe irrégulier rejeté (prendre -> 'prend'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurNegationPhrase, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
G = "{'chat':'masculin','chien':'masculin','souris':'féminin','tarte':'féminin','os':'masculin'}"


def _t(fn, sig, tests, held):
    return Tache(id=f"ng/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# -er : VISIBLE = chat/manger/souris ; HELD-OUT = vocab jamais vu.
ER = _t("nier", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','manger','souris',G) == 'le chat ne mange pas la souris'\ncheck(nier)",
    f"def check(c):\n    G={G}\n    assert c('chien','donner','os',G) == \"le chien ne donne pas l'os\"\ncheck(nier)")
# élision n' devant voyelle (aimer -> n'aime) : généralisation distincte.
ELID = _t("nier", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','aimer','souris',G) == \"le chat n'aime pas la souris\"\ncheck(nier)",
    f"def check(c):\n    G={G}\n    assert c('chien','finir','tarte',G) == 'le chien ne finit pas la tarte'\ncheck(nier)")
# verbe irrégulier (prendre) = HORS portée : la brique laisse 'prendre', rejeté par le juge.
HORS = _t("nier", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','prendre','souris',G) == 'le chat ne prend pas la souris'\ncheck(nier)",
    f"def check(c):\n    G={G}\n    assert c('chat','prendre','souris',G) == 'le chat ne prend pas la souris'\ncheck(nier)")


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
    ng = GenerateurNegationPhrase()
    r.append(_check("MUR : le substrat ne minte pas la négation (-er held-out)",
                    _resout(GenerateurSubstrat(), ER) is None))
    r.append(_check("GÉNÉRAL ×2 : -er (vocab held-out) ET élision n' devant voyelle (n'aime pas)",
                    _resout(ng, ER) is not None and _resout(ng, ELID) is not None))
    r.append(_check("HONNÊTE : ne résout pas `prendre` (verbe irrégulier, hors portée)", _resout(ng, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), negation_phrase=True)
        e, _, code, _ = resoudre(orch, ER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (negation_phrase=True) résout à l'étage `{e}`",
                    code is not None and e == "negation_phrase"))
    print()
    print("NÉGATION (PRODUCTION) VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
