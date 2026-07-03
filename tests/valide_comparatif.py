"""COMPARATIF (PRODUCTION + COGNITION) — exprimer une comparaison a/b via un adjectif accordé, RÉGLÉ donc VÉRIFIABLE.
MUR : substrat ne minte pas la forme (held-out). GÉNÉRAL ×2 : sujet masculin (pas d'accord, vocab/degré held-out) ET
sujet féminin (accord +e). HONNÊTE : féminin irrégulier rejeté (beau -> 'belle' ; la brique dit 'beaue'). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurComparatif, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
G = "{'chat':'masculin','chien':'masculin','souris':'féminin','table':'féminin'}"


def _t(fn, sig, tests, held):
    return Tache(id=f"cmp/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# sujet masculin (pas d'accord) : VISIBLE = chat/grand ; HELD-OUT = degré 'moins', vocab jamais vu.
MASC = _t("comparatif", "a, b, adj, genres, degre",
    f"def check(c):\n    G={G}\n    assert c('chat','souris','grand',G,'plus') == 'le chat est plus grand que la souris'\ncheck(comparatif)",
    f"def check(c):\n    G={G}\n    assert c('chien','chat','rapide',G,'moins') == 'le chien est moins rapide que le chat'\ncheck(comparatif)")
# sujet féminin (accord +e) : généralisation distincte.
FEM = _t("comparatif", "a, b, adj, genres, degre",
    f"def check(c):\n    G={G}\n    assert c('souris','chat','grand',G,'plus') == 'la souris est plus grande que le chat'\ncheck(comparatif)",
    f"def check(c):\n    G={G}\n    assert c('table','chat','petit',G,'aussi') == 'la table est aussi petite que le chat'\ncheck(comparatif)")
# féminin irrégulier (beau -> belle) = HORS portée : la brique produit 'beaue', rejeté par le juge.
HORS = _t("comparatif", "a, b, adj, genres, degre",
    f"def check(c):\n    G={G}\n    assert c('souris','chat','beau',G,'plus') == 'la souris est plus belle que le chat'\ncheck(comparatif)",
    f"def check(c):\n    G={G}\n    assert c('souris','chat','beau',G,'plus') == 'la souris est plus belle que le chat'\ncheck(comparatif)")


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
    cm = GenerateurComparatif()
    r.append(_check("MUR : le substrat ne minte pas le comparatif (masculin held-out)",
                    _resout(GenerateurSubstrat(), MASC) is None))
    r.append(_check("GÉNÉRAL ×2 : sujet masculin (degré/vocab held-out) ET sujet féminin (accord +e)",
                    _resout(cm, MASC) is not None and _resout(cm, FEM) is not None))
    r.append(_check("HONNÊTE : ne résout pas `beau` (féminin irrégulier, hors portée)", _resout(cm, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), comparatif=True)
        e, _, code, _ = resoudre(orch, MASC, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (comparatif=True) résout à l'étage `{e}`",
                    code is not None and e == "comparatif"))
    print()
    print("COMPARATIF VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
