"""VALIDATION logique_tri.py (Vague 1). FAUX=0 : OWA -> INCONNU au doute ; CWA opt-in ; contradiction détectée ; Kleene."""
from __future__ import annotations
from logique_tri import BaseTrivaluee, Contradiction, non, et, ou, VRAI, FAUX, INCONNU

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)
def leve(fn, exc):
    try: fn(); return False
    except exc: return True

B = BaseTrivaluee()
B.affirme(("capitale", "France", "Paris"))
B.nie(("capitale", "France", "Lyon"))
check("fait affirmé -> VRAI", B.evalue(("capitale", "France", "Paris")) == VRAI)
check("fait nié -> FAUX", B.evalue(("capitale", "France", "Lyon")) == FAUX)
check("OWA : fait inconnu -> INCONNU (jamais FAUX au doute)", B.evalue(("capitale", "France", "Nice")) == INCONNU)

B.declare_complete("planetes")
B.affirme(("planetes", "Terre"))
check("CWA : relation complète, absent -> FAUX", B.evalue(("planetes", "Pluton"), relation="planetes") == FAUX)
check("CWA n'affecte QUE les relations complètes", B.evalue(("capitale", "France", "Nice"), relation="capitale") == INCONNU)

check("affirmer un fait déjà nié -> Contradiction", leve(lambda: B.affirme(("capitale", "France", "Lyon")), Contradiction))
check("nier un fait déjà affirmé -> Contradiction", leve(lambda: B.nie(("capitale", "France", "Paris")), Contradiction))

check("non : VRAI<->FAUX, non(INCONNU)=INCONNU", non(VRAI) == FAUX and non(FAUX) == VRAI and non(INCONNU) == INCONNU)
check("ET Kleene : INCONNU et FAUX = FAUX", et(INCONNU, FAUX) == FAUX)
check("ET Kleene : INCONNU et VRAI = INCONNU", et(INCONNU, VRAI) == INCONNU)
check("OU Kleene : INCONNU ou VRAI = VRAI", ou(INCONNU, VRAI) == VRAI)
check("OU Kleene : INCONNU ou FAUX = INCONNU", ou(INCONNU, FAUX) == INCONNU)
check("connu() distingue connu/inconnu", B.connu(("capitale", "France", "Paris")) and not B.connu(("x", "y")))

print(f"\n=== valide_logique_tri : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
