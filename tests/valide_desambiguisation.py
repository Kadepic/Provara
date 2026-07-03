"""DÉSAMBIGUÏSATION MULTI-CANAL (brique SENS : un mot + un geste) — le sens naît du COUPLE (mot, geste).
MUR : un corps qui ignore le geste ne distingue pas haut/bas ; le substrat ne minte pas le couple. GÉNÉRAL ×2 :
famille `tri` (haut/bas) ET famille `bout` (debut/fin) sur arguments JAMAIS vus. HONNÊTE : couple inconnu -> HORS. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurDesambiguisation, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"de/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# même mot `tri`, le GESTE (haut/bas) tranche la direction -> il FAUT les 2 canaux. held-out = listes neuves.
TRI = _t("commande", "mot, geste, x",
    "def check(c):\n    assert c('tri','haut',[3,1,2]) == [1,2,3]\n    assert c('tri','bas',[3,1,2]) == [3,2,1]\ncheck(commande)",
    "def check(c):\n    assert c('tri','haut',[9,5,7]) == [5,7,9]\n    assert c('tri','bas',[9,5,7]) == [9,7,5]\ncheck(commande)")
# famille `bout` = niveau 1 seul (table de couples plus large).
BOUT = _t("commande", "mot, geste, x",
    "def check(c):\n    assert c('bout','debut',[3,1,2]) == 3\n    assert c('bout','fin',[3,1,2]) == 2\ncheck(commande)",
    "def check(c):\n    assert c('bout','debut',[9,5,7]) == 9\n    assert c('bout','fin',[9,5,7]) == 7\ncheck(commande)")
# couple inconnu = HORS portée.
HORS = _t("commande", "mot, geste, x",
    "def check(c):\n    assert c('tri','milieu',[3,1,2]) == 1\ncheck(commande)",
    "def check(c):\n    assert c('tri','milieu',[3,1,2]) == 1\ncheck(commande)")


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
    de = GenerateurDesambiguisation()
    r.append(_check("MUR : le substrat ne minte pas la dispatch sur le couple (mot, geste)",
                    _resout(GenerateurSubstrat(), TRI) is None))
    r.append(_check("GÉNÉRAL ×2 : famille `tri` (haut/bas) ET famille `bout` (debut/fin) sur arguments held-out",
                    _resout(de, TRI) is not None and _resout(de, BOUT) is not None))
    r.append(_check("HONNÊTE : ne résout pas le couple ('tri','milieu') (inconnu)", _resout(de, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), desambiguisation=True)
        e, _, code, _ = resoudre(orch, TRI, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (desambiguisation=True) résout à l'étage `{e}`",
                    code is not None and e == "desambiguisation"))
    print()
    print("DÉSAMBIGUÏSATION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
