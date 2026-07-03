"""INTENTION / BUT (brique SENS : viser un état vérifiable, moyen-fin) — le but est une post-condition jugeable.
MUR : substrat ne minte pas la recherche moyen-fin. GÉNÉRAL ×2 : buts d'ordre (croissant/decroissant) ET sans_doublon
sur des arguments JAMAIS vus. HONNÊTE : ne résout pas un but hors vocabulaire (`palindrome`). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurIntention, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"in/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# buts d'ORDRE : un sorted figé passerait `croissant` mais pas `decroissant` -> il FAUT le moyen-fin. held-out = args neufs.
ORDRE = _t("atteindre", "but, x",
    "def check(c):\n    assert c('croissant',[3,1,2]) == [1,2,3]\n    assert c('decroissant',[1,3,2]) == [3,2,1]\ncheck(atteindre)",
    "def check(c):\n    assert c('croissant',[9,5,7]) == [5,7,9]\n    assert c('decroissant',[2,8,4]) == [8,4,2]\ncheck(atteindre)")
# but sans_doublon = niveau 1 seul (vocabulaire de buts plus large).
DEDUP = _t("atteindre", "but, x",
    "def check(c):\n    assert c('sans_doublon',[3,1,3,2]) == [3,1,2]\ncheck(atteindre)",
    "def check(c):\n    assert c('sans_doublon',[5,5,1,5,2]) == [5,1,2]\ncheck(atteindre)")
# but hors vocabulaire = HORS portée.
HORS = _t("atteindre", "but, x",
    "def check(c):\n    assert c('palindrome',[1,2]) == [1,2,1]\ncheck(atteindre)",
    "def check(c):\n    assert c('palindrome',[1,2]) == [1,2,1]\ncheck(atteindre)")


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
    ing = GenerateurIntention()
    r.append(_check("MUR : le substrat ne minte pas la recherche moyen-fin (2 buts d'ordre held-out)",
                    _resout(GenerateurSubstrat(), ORDRE) is None))
    r.append(_check("GÉNÉRAL ×2 : buts d'ordre (croissant ET decroissant) ET sans_doublon sur arguments held-out",
                    _resout(ing, ORDRE) is not None and _resout(ing, DEDUP) is not None))
    r.append(_check("HONNÊTE : ne résout pas le but `palindrome` (hors vocabulaire)", _resout(ing, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), intention=True)
        e, _, code, _ = resoudre(orch, ORDRE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (intention=True) résout à l'étage `{e}`", code is not None and e == "intention"))
    print()
    print("INTENTION VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
