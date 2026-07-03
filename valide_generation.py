"""GÉNÉRATION DE PHRASE (brique COMPRÉHENSION — production) — l'IA écrit une phrase complète depuis un sens.
MUR : substrat ne minte pas article+conjugaison+assemblage. GÉNÉRAL ×2 : phrase (SVO) ET intransitif sur du
vocabulaire JAMAIS vu, avec élision (l'). HONNÊTE : hors famille -> rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurGeneration, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

G = "{'chat':'masculin','chien':'masculin','souris':'féminin','voiture':'féminin','oiseau':'masculin'}"


def _t(fn, sig, tests, held):
    return Tache(id=f"gn/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# PHRASE SVO. held-out = vocabulaire neuf + élision (l'oiseau).
PHRASE = _t("phrase", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','manger','souris',G) == 'le chat mange la souris'\ncheck(phrase)",
    f"def check(c):\n    G={G}\n    assert c('chien','regarder','voiture',G) == 'le chien regarde la voiture'\n    assert c('chat','voir','oiseau',G) == \"le chat voit l'oiseau\"\ncheck(phrase)")
# INTRANSITIF. held-out = vocabulaire neuf.
INTRANS = _t("intransitif", "sujet, verbe, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','chanter',G) == 'le chat chante'\ncheck(intransitif)",
    f"def check(c):\n    G={G}\n    assert c('souris','danser',G) == 'la souris danse'\n    assert c('oiseau','voler',G) == \"l'oiseau vole\"\ncheck(intransitif)")
# HORS : « question » (forme interrogative) hors famille.
HORS = _t("question", "sujet, verbe, objet, genres",
    f"def check(c):\n    G={G}\n    assert c('chat','manger','souris',G) == 'le chat mange-t-il la souris ?'\ncheck(question)",
    f"def check(c):\n    G={G}\n    assert c('chat','manger','souris',G) == 'le chat mange-t-il la souris ?'\ncheck(question)")


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
    gn = GenerateurGeneration()
    r.append(_check("MUR : le substrat ne minte pas article+conjugaison+assemblage (phrase held-out)",
                    _resout(GenerateurSubstrat(), PHRASE) is None))
    r.append(_check("GÉNÉRAL ×2 : phrase (SVO) ET intransitif sur vocabulaire held-out + élision (l')",
                    _resout(gn, PHRASE) is not None and _resout(gn, INTRANS) is not None))
    r.append(_check("HONNÊTE : ne produit pas la forme `question` (hors famille)", _resout(gn, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), generation=True)
        e, _, code, _ = resoudre(orch, PHRASE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (generation=True) résout à l'étage `{e}`",
                    code is not None and e == "generation"))
    print()
    print("GÉNÉRATION DE PHRASE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
