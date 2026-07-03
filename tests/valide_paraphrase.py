"""PARAPHRASE / MÊME SENS (brique COMPRÉHENSION) — voir au-delà des mots de surface (synonymes).
MUR : substrat ne minte pas la canonisation+comparaison. GÉNÉRAL ×2 : canonise (forme) ET meme_sens (booléen) sur des
phrases JAMAIS vues. HONNÊTE : sens différent -> False (ne confond pas rapide/lent). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurParaphrase, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

S = "{'auto':'voiture','automobile':'voiture','bagnole':'voiture','velo':'bicyclette','bicane':'bicyclette'}"


def _t(fn, sig, tests, held):
    return Tache(id=f"pa/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# CANONISE : ramène à la forme canonique. held-out = phrases neuves.
CANON = _t("canonise", "synonymes, phrase",
    f"def check(c):\n    S={S}\n    assert c(S,'la auto rapide') == 'la voiture rapide'\ncheck(canonise)",
    f"def check(c):\n    S={S}\n    assert c(S,'le velo rouge') == 'le bicyclette rouge'\n    assert c(S,'la bagnole') == 'la voiture'\ncheck(canonise)")
# MEME_SENS : booléen. held-out = même sens via synonyme ET sens différent -> False.
MEME = _t("meme_sens", "synonymes, p1, p2",
    f"def check(c):\n    S={S}\n    assert c(S,'la auto rapide','la voiture rapide') == True\ncheck(meme_sens)",
    f"def check(c):\n    S={S}\n    assert c(S,'la automobile','la voiture') == True\n    assert c(S,'la auto rapide','la auto lente') == False\ncheck(meme_sens)")
# HORS : compter les mots = hors famille.
HORS = _t("compte", "synonymes, phrase",
    f"def check(c):\n    S={S}\n    assert c(S,'la auto rapide') == 3\ncheck(compte)",
    f"def check(c):\n    S={S}\n    assert c(S,'la auto rapide') == 3\ncheck(compte)")


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
    pa = GenerateurParaphrase()
    r.append(_check("MUR : le substrat ne minte pas la canonisation + comparaison (canonise held-out)",
                    _resout(GenerateurSubstrat(), CANON) is None))
    r.append(_check("GÉNÉRAL ×2 : canonise (forme) ET meme_sens (booléen) sur phrases held-out",
                    _resout(pa, CANON) is not None and _resout(pa, MEME) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(pa, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), paraphrase=True)
        e, _, code, _ = resoudre(orch, MEME, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (paraphrase=True) résout à l'étage `{e}`",
                    code is not None and e == "paraphrase"))
    print()
    print("PARAPHRASE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
