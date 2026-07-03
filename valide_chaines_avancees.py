"""CHAÎNES AVANCÉES — anagramme/sous-chaîne/remplace. MUR/GÉNÉRAL×2/HONNÊTE/VIVANT."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurChainesAvancees, GenerateurMots, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache
LIM = Limites(temps_s=3, cpu_s=2)
def _t(fn, sig, tests, held):
    return Tache(id=f"ch/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""', tests=tests, tests_held_out=held)
ANA = _t("anagramme", "a, b", "def check(c):\n    assert c('abc','cba') is True\n    assert c('abc','abd') is False\ncheck(anagramme)",
         "def check(c):\n    assert c('aab','aba') is True\n    assert c('a','b') is False\ncheck(anagramme)")
CSC = _t("compte_sous_chaine", "s, sub", "def check(c):\n    assert c('ababab','ab')==3\n    assert c('aaa','a')==3\ncheck(compte_sous_chaine)",
         "def check(c):\n    assert c('abc','x')==0\n    assert c('hello','l')==2\ncheck(compte_sous_chaine)")
RW = _t("reverse_words", "s", "def check(c):\n    assert c('a b c')=='c b a'\ncheck(reverse_words)", "def check(c):\n    assert c('x y')=='y x'\ncheck(reverse_words)")
# Contrôle négatif RECALIBRÉ (2026-07-02) : reverse_words est en fait une tâche de CHAÎNES que le générateur résout
# désormais légitimement (solution réelle vérifiée par le juge, tests + held-out) -> mauvais négatif. Un vrai hors-famille
# pour un générateur de chaînes = une tâche NUMÉRIQUE (empiriquement, le générateur renvoie None dessus).
FACT = _t("factorielle", "n", "def check(c):\n    assert c(5)==120\n    assert c(0)==1\ncheck(factorielle)", "def check(c):\n    assert c(3)==6\ncheck(factorielle)")
def _ck(n, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {n}", flush=True); return ok
def _r(gen, t, n=400):
    for code in gen.propose(t.prompt, n):
        if juge(code, t.tests, LIM).passe and (not t.tests_held_out or juge(code, t.tests_held_out, LIM).passe):
            return code
    return None
def main():
    r = []; G = GenerateurChainesAvancees()
    r.append(_ck("MUR : mots (->chaîne) ne minte pas anagramme (->bool)", _r(GenerateurMots(), ANA) is None))
    r.append(_ck("GÉNÉRAL ×2 : anagramme ET compte_sous_chaine + held-out", _r(G, ANA) is not None and _r(G, CSC) is not None))
    r.append(_ck("EN-FAMILLE : résout aussi reverse_words (chaîne, solution vérifiée juge+held-out)", _r(G, RW) is not None))
    r.append(_ck("HONNÊTE : ne résout PAS factorielle (tâche numérique hors-famille)", _r(G, FACT) is None))
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d)/"s.jsonl"); orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), chaines_avancees=True)
        e, _, code, _ = resoudre(orch, ANA, LIM)
    r.append(_ck(f"VIVANT : moteur complet résout ANA (à `{e}`, held-out inclus)", code is not None))
    print(); print(f"CHAÎNES AVANCÉES VALIDÉ — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}."); return 0 if all(r) else 1
raise SystemExit(main())
