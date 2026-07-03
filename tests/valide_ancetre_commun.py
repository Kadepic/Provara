"""ANCÊTRE COMMUN / LIEN (brique COMPRÉHENSION) — ce que deux mots ont en commun, sur le graphe de sens.
MUR : substrat ne minte pas le croisement de deux remontées. GÉNÉRAL ×2 : ancetre_commun (LCA) ET ont_lien (bool)
sur des paires JAMAIS directes. HONNÊTE : pas de lien -> None / False (jamais inventé). VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurAncetreCommun, GenerateurOrchestre, GenerateurSubstrat, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)

# graphe de sens : chat->félin->mammifère->animal ; chien->canidé->mammifère->animal ; voiture->véhicule.
E = ("[('chat','félin'),('félin','mammifère'),('mammifère','animal'),"
     "('chien','canidé'),('canidé','mammifère'),('voiture','véhicule')]")


def _t(fn, sig, tests, held):
    return Tache(id=f"ac/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)


# LCA : le PLUS PROCHE commun. chat/chien -> mammifère (pas animal, plus loin). held-out = autre paire.
LCA = _t("ancetre_commun", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','chien') == 'mammifère'\ncheck(ancetre_commun)",
    f"def check(c):\n    E={E}\n    assert c(E,'félin','canidé') == 'mammifère'\n    assert c(E,'chat','voiture') is None\ncheck(ancetre_commun)")
# LIEN : booléen. held-out = paire sans lien -> False.
LIEN = _t("ont_lien", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','chien') == True\ncheck(ont_lien)",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','voiture') == False\n    assert c(E,'chien','félin') == True\ncheck(ont_lien)")
# HORS : la « distance » (longueur) n'est pas dans la famille.
HORS = _t("distance", "aretes, x, y",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','mammifère') == 2\ncheck(distance)",
    f"def check(c):\n    E={E}\n    assert c(E,'chat','mammifère') == 2\ncheck(distance)")


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
    ac = GenerateurAncetreCommun()
    r.append(_check("MUR : le substrat ne minte pas le croisement de deux remontées (LCA held-out)",
                    _resout(GenerateurSubstrat(), LCA) is None))
    r.append(_check("GÉNÉRAL ×2 : ancetre_commun (LCA) ET ont_lien (bool) sur paires held-out indirectes",
                    _resout(ac, LCA) is not None and _resout(ac, LIEN) is not None))
    r.append(_check("HONNÊTE : ne calcule pas `distance` (hors famille)", _resout(ac, HORS) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), ancetre_commun=True)
        e, _, code, _ = resoudre(orch, LCA, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (ancetre_commun=True) résout à l'étage `{e}`",
                    code is not None and e == "ancetre-commun"))
    print()
    print("ANCÊTRE COMMUN VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
