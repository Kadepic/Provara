"""ANTONYMES (brique COMPRÉHENSION — axe du sens : les contraires) — symétrique, non transitif.
MUR : substrat ne minte pas la recherche symétrique de paire. GÉNÉRAL ×2 : contraire (le mot opposé) ET
sont_contraires (booléen) sur des paires JAMAIS vues. HONNÊTE : pas d'antonyme -> None / False. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAntonyme, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

A = "[('grand','petit'),('chaud','froid'),('rapide','lent'),('clair','sombre')]"


def _t(fn, sig, tests, held):
    return Tache(id=f"an/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# CONTRAIRE : symétrique (marche dans les deux sens). held-out = mots jamais vus.
CONTRAIRE = _t("contraire", "antonymes, mot",
    f"def check(c):\n    A={A}\n    assert c(A,'grand') == 'petit'\n    assert c(A,'petit') == 'grand'\ncheck(contraire)",
    f"def check(c):\n    A={A}\n    assert c(A,'froid') == 'chaud'\n    assert c(A,'lent') == 'rapide'\n    assert c(A,'inconnu') is None\ncheck(contraire)")
# SONT_CONTRAIRES : booléen. held-out = paire non opposée -> False.
SONT = _t("sont_contraires", "antonymes, x, y",
    f"def check(c):\n    A={A}\n    assert c(A,'grand','petit') == True\ncheck(sont_contraires)",
    f"def check(c):\n    A={A}\n    assert c(A,'froid','chaud') == True\n    assert c(A,'grand','froid') == False\ncheck(sont_contraires)")
# HORS : « synonyme » (autre relation) n'est pas dans cette famille.
HORS = _t("synonyme", "antonymes, mot",
    f"def check(c):\n    A={A}\n    assert c(A,'grand') == 'immense'\ncheck(synonyme)",
    f"def check(c):\n    A={A}\n    assert c(A,'grand') == 'immense'\ncheck(synonyme)")


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
    an = GenerateurAntonyme()
    r.append(_check("MUR : le substrat ne minte pas la recherche symétrique de paire (contraire held-out)",
                    _resout(GenerateurSubstrat(), CONTRAIRE) is None))
    r.append(_check("GÉNÉRAL ×2 : contraire (mot opposé) ET sont_contraires (booléen) sur paires held-out",
                    _resout(an, CONTRAIRE) is not None and _resout(an, SONT) is not None))
    r.append(_check("HONNÊTE : ne renvoie pas un `synonyme` (autre relation)", _resout(an, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), antonyme=True)
        e, _, code, _ = resoudre(orch, CONTRAIRE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (antonyme=True) résout à l'étage `{e}`",
                    code is not None and e == "antonyme"))
    print()
    print("ANTONYMES VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
