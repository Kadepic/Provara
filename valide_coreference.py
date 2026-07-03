"""CORÉFÉRENCE (brique COMPRÉHENSION — discours) — résoudre un pronom vers son antécédent par le genre.
MUR : substrat ne minte pas la recherche du plus récent compatible. GÉNÉRAL ×2 : antecedent ET compatible sur des
discours JAMAIS vus, pronom masculin ET féminin. HONNÊTE : aucun antécédent compatible -> None / False. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurCoreference, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

G = "{'chat':'masculin','chien':'masculin','lion':'masculin','souris':'féminin','voiture':'féminin','table':'féminin'}"


def _t(fn, sig, tests, held):
    return Tache(id=f"co/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# ANTECEDENT : le nom le plus RÉCENT compatible. held-out = pronom féminin + discours neufs.
ANTE = _t("antecedent", "genres, mentions, pronom",
    f"def check(c):\n    G={G}\n    assert c(G,['chat','souris'],'il') == 'chat'\ncheck(antecedent)",
    f"def check(c):\n    G={G}\n    assert c(G,['chien','voiture'],'elle') == 'voiture'\n    assert c(G,['chat','lion'],'il') == 'lion'\n    assert c(G,['chat'],'elle') is None\ncheck(antecedent)")
# COMPATIBLE : booléen genre. held-out = incompatibles.
COMPAT = _t("compatible", "genres, nom, pronom",
    f"def check(c):\n    G={G}\n    assert c(G,'chat','il') == True\ncheck(compatible)",
    f"def check(c):\n    G={G}\n    assert c(G,'souris','il') == False\n    assert c(G,'voiture','elle') == True\ncheck(compatible)")
# HORS : compter les mentions = hors famille.
HORS = _t("compte", "genres, mentions, pronom",
    f"def check(c):\n    G={G}\n    assert c(G,['chat','souris'],'il') == 2\ncheck(compte)",
    f"def check(c):\n    G={G}\n    assert c(G,['chat','souris'],'il') == 2\ncheck(compte)")


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
    co = GenerateurCoreference()
    r.append(_check("MUR : le substrat ne minte pas la recherche du plus récent compatible (antecedent held-out)",
                    _resout(GenerateurSubstrat(), ANTE) is None))
    r.append(_check("GÉNÉRAL ×2 : antecedent (le bon nom) ET compatible (booléen) sur discours held-out",
                    _resout(co, ANTE) is not None and _resout(co, COMPAT) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `compte` (hors famille)", _resout(co, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), coreference=True)
        e, _, code, _ = resoudre(orch, ANTE, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (coreference=True) résout à l'étage `{e}`",
                    code is not None and e == "coreference"))
    print()
    print("CORÉFÉRENCE VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
