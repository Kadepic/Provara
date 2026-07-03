"""DÉTECTION D'ERREUR D'ACCORD (brique COMPRÉHENSION) — savoir quand le français est faux.
MUR : substrat ne minte pas la règle marque-du-pluriel. GÉNÉRAL ×2 : est_accorde (booléen) ET mot_fautif (localisation)
sur des groupes JAMAIS vus. HONNÊTE : groupe singulier -> rien à signaler. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAccordCorrect, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held):
    return Tache(id=f"ac2/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# EST_ACCORDE : correct vs fautif. held-out = groupes neufs + groupe singulier (rien à signaler -> True).
EST = _t("est_accorde", "phrase",
    "def check(c):\n    assert c('les chats noirs') == True\n    assert c('les chat noir') == False\ncheck(est_accorde)",
    "def check(c):\n    assert c('les chevaux gris') == True\n    assert c('les chien petit') == False\n    assert c('le chat noir') == True\ncheck(est_accorde)")
# MOT_FAUTIF : localise la faute. held-out = faute en position variable.
FAUTIF = _t("mot_fautif", "phrase",
    "def check(c):\n    assert c('les chat noirs') == 'chat'\ncheck(mot_fautif)",
    "def check(c):\n    assert c('les chats noir') == 'noir'\n    assert c('les chats noirs') is None\ncheck(mot_fautif)")
# HORS : compter les mots = hors famille.
HORS = _t("compte", "phrase",
    "def check(c):\n    assert c('les chats noirs') == 3\ncheck(compte)",
    "def check(c):\n    assert c('les chats noirs') == 3\ncheck(compte)")


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
    ac = GenerateurAccordCorrect()
    r.append(_check("MUR : le substrat ne minte pas la règle marque-du-pluriel (est_accorde held-out)",
                    _resout(GenerateurSubstrat(), EST) is None))
    r.append(_check("GÉNÉRAL ×2 : est_accorde (booléen) ET mot_fautif (localisation) sur groupes held-out",
                    _resout(ac, EST) is not None and _resout(ac, FAUTIF) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(ac, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), accord_correct=True)
        e, _, code, _ = resoudre(orch, EST, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (accord_correct=True) résout à l'étage `{e}`",
                    code is not None and e == "accord-correct"))
    print()
    print("DÉTECTION D'ERREUR D'ACCORD VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
