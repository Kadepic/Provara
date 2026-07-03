"""ACCORD DANS LE GROUPE NOMINAL (brique COMPRÉHENSION — phrase) — propage le pluriel sur tout le groupe.
MUR : substrat ne minte pas la composition déterminant+nom+adjectif. GÉNÉRAL ×2 : groupe simple ET familles (-al/-eau)
sur des groupes JAMAIS vus. HONNÊTE : ne dépluralise pas (sens inverse). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAccordPhrase, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"af/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# groupe simple (+s) : held-out = groupes neufs, adjectif invariant en -s (gris -> gris).
SIMPLE = _t("accorder_pluriel", "phrase",
    "def check(c):\n    assert c('le chat noir') == 'les chats noirs'\n    assert c('la petite souris') == 'les petites souris'\ncheck(accorder_pluriel)",
    "def check(c):\n    assert c('le chien gris') == 'les chiens gris'\n    assert c('un grand chat') == 'des grands chats'\ncheck(accorder_pluriel)")
# familles (-al/-eau) = niveau 2 seul : held-out = groupes neufs.
FAMILLE = _t("accorder_pluriel", "phrase",
    "def check(c):\n    assert c('le cheval royal') == 'les chevaux royaux'\ncheck(accorder_pluriel)",
    "def check(c):\n    assert c('le nouveau bateau') == 'les nouveaux bateaux'\ncheck(accorder_pluriel)")
# HORS : dépluraliser (sens inverse) n'est pas dans la portée.
HORS = _t("accorder_pluriel", "phrase",
    "def check(c):\n    assert c('les chats noirs') == 'le chat noir'\ncheck(accorder_pluriel)",
    "def check(c):\n    assert c('les chats noirs') == 'le chat noir'\ncheck(accorder_pluriel)")


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
    af = GenerateurAccordPhrase()
    r.append(_check("MUR : le substrat ne minte pas la propagation déterminant+nom+adjectif",
                    _resout(GenerateurSubstrat(), SIMPLE) is None))
    r.append(_check("GÉNÉRAL ×2 : groupe simple ET familles (-al->-aux, -eau->+x) sur groupes held-out",
                    _resout(af, SIMPLE) is not None and _resout(af, FAMILLE) is not None))
    r.append(_check("HONNÊTE : ne dépluralise pas (sens inverse hors portée)", _resout(af, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), accord_phrase=True)
        e, _, code, _ = resoudre(orch, SIMPLE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (accord_phrase=True) résout à l'étage `{e}`",
                    code is not None and e == "accord-phrase"))
    print()
    print("ACCORD DU GROUPE NOMINAL VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
