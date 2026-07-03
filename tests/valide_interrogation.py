"""INTERROGATION (brique PRODUCTION) — tourner un sens en question (inversion + -t- euphonique), RÉGLÉ donc VÉRIFIABLE.
Abolit le mur de la génération (« ne sait pas questionner »). MUR : substrat ne minte pas la forme (held-out).
GÉNÉRAL ×2 : -er (mange-t-il, vocab JAMAIS vu) ET -ir (finit-il, pas de -t-). HONNÊTE : verbe irrégulier rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurInterrogation, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
G = "{'chat':'masculin','chien':'masculin','souris':'féminin','tarte':'féminin','balle':'féminin'}"


def _t(fn, sig, tests, held):
    return Tache(id=f"int/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# -er (euphonique -t-) : VISIBLE = chat/manger/souris ; HELD-OUT = vocab jamais vu.
ER = _t("question", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','manger','souris',G) == 'le chat mange-t-il la souris ?'\ncheck(question)",
    f"def check(c):\n    G={G}\n    assert c('chien','donner','balle',G) == 'le chien donne-t-il la balle ?'\ncheck(question)")
# -ir (pas de -t-, le verbe finit déjà par t) : généralisation distincte.
IR = _t("question", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chien','finir','tarte',G) == 'le chien finit-il la tarte ?'\ncheck(question)",
    f"def check(c):\n    G={G}\n    assert c('chat','choisir','balle',G) == 'le chat choisit-il la balle ?'\ncheck(question)")
# verbe irrégulier (prendre) = HORS portée : la brique laisse 'prendre' -> 'le chat prendre-il...', rejeté.
HORS = _t("question", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','prendre','souris',G) == 'le chat prend-il la souris ?'\ncheck(question)",
    f"def check(c):\n    G={G}\n    assert c('chat','prendre','souris',G) == 'le chat prend-il la souris ?'\ncheck(question)")


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
    it = GenerateurInterrogation()
    r.append(_check("MUR : le substrat ne minte pas l'interrogation (-er held-out)",
                    _resout(GenerateurSubstrat(), ER) is None))
    r.append(_check("GÉNÉRAL ×2 : -er (-t- euphonique, vocab held-out) ET -ir (finit-il, sans -t-)",
                    _resout(it, ER) is not None and _resout(it, IR) is not None))
    r.append(_check("HONNÊTE : ne résout pas `prendre` (verbe irrégulier, hors portée)", _resout(it, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), interrogation=True)
        e, _, code, _ = resoudre(orch, ER, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (interrogation=True) résout à l'étage `{e}`",
                    code is not None and e == "interrogation"))
    print()
    print("INTERROGATION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
