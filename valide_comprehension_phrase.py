"""COMPRÉHENSION DE PHRASE (brique COMPRÉHENSION — sens + logique) — qui fait quoi (rôles SVO autour du verbe).
MUR : substrat ne minte pas le découpage relatif au verbe. GÉNÉRAL ×2 : sujet ET objet sur phrases JAMAIS vues,
groupes de longueur variable. HONNÊTE/LIMITE : phrase sans verbe -> pas d'action -> rejeté. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurComprehensionPhrase, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

C = ("{'le':'determinant','la':'determinant','chat':'nom','souris':'nom','chien':'nom','fromage':'nom',"
     "'noir':'adjectif','petit':'adjectif','gris':'adjectif','dort':'verbe','mange':'verbe','voit':'verbe'}")


def _t(fn, sig, tests, held):
    return Tache(id=f"cp/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# SUJET : groupe avant le verbe. held-out = sujet plus long (déterminant+adjectif+nom).
SUJET = _t("sujet", "classes, phrase",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat mange la souris') == 'le chat'\ncheck(sujet)",
    f"def check(c):\n    C={C}\n    assert c(C,'le petit chien voit la souris') == 'le petit chien'\n    assert c(C,'la souris dort') == 'la souris'\ncheck(sujet)")
# OBJET : groupe après le verbe. held-out = objet plus long.
OBJET = _t("objet", "classes, phrase",
    f"def check(c):\n    C={C}\n    assert c(C,'le chat mange la souris') == 'la souris'\ncheck(objet)",
    f"def check(c):\n    C={C}\n    assert c(C,'le chien voit le petit chat gris') == 'le petit chat gris'\ncheck(objet)")
# HORS/LIMITE : phrase SANS verbe -> aucun rôle d'action à attribuer.
HORS = _t("sujet", "classes, phrase",
    f"def check(c):\n    C={C}\n    assert c(C,'le petit chat noir') == 'le petit chat noir'\ncheck(sujet)",
    f"def check(c):\n    C={C}\n    assert c(C,'le petit chat noir') == 'le petit chat noir'\ncheck(sujet)")


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
    cp = GenerateurComprehensionPhrase()
    r.append(_check("MUR : le substrat ne minte pas le découpage relatif au verbe (sujet held-out)",
                    _resout(GenerateurSubstrat(), SUJET) is None))
    r.append(_check("GÉNÉRAL ×2 : sujet ET objet (groupes de longueur variable) sur phrases held-out",
                    _resout(cp, SUJET) is not None and _resout(cp, OBJET) is not None))
    r.append(_check("HONNÊTE/LIMITE : ne traite pas une phrase SANS verbe (aucune action)", _resout(cp, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), comprehension_phrase=True)
        e, _, code, _ = resoudre(orch, SUJET, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (comprehension_phrase=True) résout à l'étage `{e}`",
                    code is not None and e == "comprehension-phrase"))
    print()
    print("COMPRÉHENSION DE PHRASE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
