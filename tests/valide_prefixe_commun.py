"""PRÉFIXE/SUFFIXE COMMUN (brique puissante) — réduction croisée d'une liste de chaînes.
MUR : mots (split/join) ne minte pas lcp. GÉNÉRAL ×2 : lcp (préfixe) ET suffixe_commun. HONNÊTE : pas join. VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurMots, GenerateurOrchestre, GenerateurPrefixeCommun
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held):
    return Tache(id=f"pc/{fn}", point_entree=fn, prompt=f'def {fn}(strs):\n    """..."""', tests=tests, tests_held_out=held)


LCP = _t("longest_common_prefix",
    "def check(c):\n    assert c(['flow','flower','flight']) == 'fl'\n    assert c(['a','b']) == ''\ncheck(longest_common_prefix)",
    "def check(c):\n    assert c(['abc','abd']) == 'ab'\n    assert c(['x']) == 'x'\n    assert c(['same','same']) == 'same'\ncheck(longest_common_prefix)")
SUF = _t("suffixe_commun",
    "def check(c):\n    assert c(['testing','running']) == 'ing'\n    assert c(['a','b']) == ''\ncheck(suffixe_commun)",
    "def check(c):\n    assert c(['xyz','abz']) == 'z'\n    assert c(['oui']) == 'oui'\ncheck(suffixe_commun)")
JOIN = _t("joindre",
    "def check(c):\n    assert c(['a','b','c']) == 'abc'\ncheck(joindre)",
    "def check(c):\n    assert c(['x','y']) == 'xy'\ncheck(joindre)")


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
    pc = GenerateurPrefixeCommun()
    r.append(_check("MUR : mots (split/join) ne minte pas longest_common_prefix",
                    _resout(GenerateurMots(), LCP) is None))
    r.append(_check("GÉNÉRAL ×2 : longest_common_prefix ET suffixe_commun mintés + held-out adverse",
                    _resout(pc, LCP) is not None and _resout(pc, SUF) is not None))
    r.append(_check("HONNÊTE : ne résout pas `joindre` (''.join, hors-famille)", _resout(pc, JOIN) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), prefixe_commun=True)
        e, _, code, _ = resoudre(orch, LCP, LIM)
    r.append(_check(f"VIVANT : l'orchestrateur (prefixe_commun=True) résout lcp à l'étage `{e}`", code is not None and e == "prefixe-commun"))
    print()
    print("PRÉFIXE-COMMUN VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
