"""ANALYSE DE PHRASE (brique COMPRÉHENSION — phrase) — décomposer la phrase en classes grammaticales.
MUR : substrat ne minte pas le mapping classe-par-token. GÉNÉRAL ×2 : analyse (suite des classes) ET noms (extraction)
sur des phrases JAMAIS vues. HONNÊTE : hors famille -> rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAnalysePhrase, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

C = ("{'le':'determinant','la':'determinant','chat':'nom','souris':'nom','chien':'nom',"
     "'noir':'adjectif','petit':'adjectif','dort':'verbe','mange':'verbe'}")


def _t(fn, sig, tests, held):
    return Tache(id=f"ap/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


ANALYSE = _t("analyse", "classes, phrase",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat noir dort') == ['determinant','nom','adjectif','verbe']\ncheck(analyse)",
    f"def check(c):\n    C={C}\n    assert c(C,'la souris mange') == ['determinant','nom','verbe']\n    assert c(C,'le petit chien dort') == ['determinant','adjectif','nom','verbe']\ncheck(analyse)")
NOMS = _t("noms", "classes, phrase",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat noir dort') == ['chat']\ncheck(noms)",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat mange la souris') == ['chat','souris']\ncheck(noms)")
HORS = _t("compte_mots", "classes, phrase",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat dort') == 3\ncheck(compte_mots)",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat dort') == 3\ncheck(compte_mots)")


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
    ap = GenerateurAnalysePhrase()
    r.append(_check("MUR : le substrat ne minte pas le mapping classe-par-token (analyse held-out)",
                    _resout(GenerateurSubstrat(), ANALYSE) is None))
    r.append(_check("GÉNÉRAL ×2 : analyse (suite des classes) ET noms (extraction) sur phrases held-out",
                    _resout(ap, ANALYSE) is not None and _resout(ap, NOMS) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte_mots` (hors famille)", _resout(ap, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), analyse_phrase=True)
        e, _, code, _ = resoudre(orch, ANALYSE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (analyse_phrase=True) résout à l'étage `{e}`",
                    code is not None and e == "analyse-phrase"))
    print()
    print("ANALYSE DE PHRASE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
