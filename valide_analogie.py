"""ANALOGIE / TRANSFERT (brique COMPRÉHENSION) — un motif appris se réutilise/adapte à travers les DOMAINES.
MUR : substrat ne minte pas l'appariement de relation + transfert. GÉNÉRAL ×2 : analogie (trouve l'image) sur DEUX
domaines distincts (géographie ET famille) ET meme_relation, held-out. HONNÊTE : pas d'image -> None. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAnalogie, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

# relations de DEUX domaines mélangés : géographie (capitale_de) + famille (mere_de).
R = ("[('paris','capitale_de','france'),('berlin','capitale_de','allemagne'),('rome','capitale_de','italie'),"
     "('marie','mere_de','paul'),('anne','mere_de','luc')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"an/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# ANALOGIE : transfère le motif. held-out = AUTRE domaine (famille) + nouvelles instances.
ANALOGIE = _t("analogie", "relations, a, b, c",
    f"def check(c):\n    R={R}\n    assert c(R,'paris','france','berlin') == 'allemagne'\ncheck(analogie)",
    f"def check(c):\n    R={R}\n    assert c(R,'marie','paul','anne') == 'luc'\n    assert c(R,'rome','italie','paris') == 'france'\ncheck(analogie)")
# MEME_RELATION : booléen de partage de motif. held-out = motifs différents -> False.
MEME = _t("meme_relation", "relations, a, b, c, d",
    f"def check(c):\n    R={R}\n    assert c(R,'paris','france','berlin','allemagne') == True\ncheck(meme_relation)",
    f"def check(c):\n    R={R}\n    assert c(R,'marie','paul','anne','luc') == True\n    assert c(R,'paris','france','marie','paul') == False\ncheck(meme_relation)")
# HORS : « inverse » (relation->sujet) hors famille.
HORS = _t("compte", "relations, a, b, c",
    f"def check(c):\n    R={R}\n    assert c(R,'paris','france','berlin') == 2\ncheck(compte)",
    f"def check(c):\n    R={R}\n    assert c(R,'paris','france','berlin') == 2\ncheck(compte)")


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
    an = GenerateurAnalogie()
    r.append(_check("MUR : le substrat ne minte pas l'appariement de relation + transfert (analogie held-out)",
                    _resout(GenerateurSubstrat(), ANALOGIE) is None))
    r.append(_check("GÉNÉRAL ×2 : analogie (transfert GÉO + FAMILLE, 2 domaines) ET meme_relation, held-out",
                    _resout(an, ANALOGIE) is not None and _resout(an, MEME) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(an, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), analogie=True)
        e, _, code, _ = resoudre(orch, ANALOGIE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (analogie=True) résout à l'étage `{e}`",
                    code is not None and e == "analogie"))
    print()
    print("ANALOGIE / TRANSFERT VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
