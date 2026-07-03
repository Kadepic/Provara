"""VALIDATION blackboard.py (Vague 7). FAUX=0 : provenance obligatoire, append-only, conflit visible, aucune valeur inventée."""
from __future__ import annotations
from blackboard import Blackboard

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)
def leve(fn, exc):
    try: fn(); return False
    except exc: return True

bb = Blackboard()
bb.poste("COP_max", 19.7, source="limite.Carnot", confiance=1.0)
bb.poste("COP_reel", 3.5, source="fiche_produit")
check("lecture d'un sujet posté", bb.dernier("COP_max").valeur == 19.7)
check("provenance conservée", bb.dernier("COP_max").source == "limite.Carnot")
check("sujet non posté -> [] (rien inventé)", bb.lis("inexistant") == [])
check("sujets() liste les topics", bb.sujets() == {"COP_max", "COP_reel"})

# provenance obligatoire
check("poster sans source -> refus", leve(lambda: bb.poste("x", 1, source=""), ValueError))

# append-only + conflit visible pour l'arbitre
bb.poste("gravite", 9.81, source="pendule")
bb.poste("gravite", 9.83, source="capteur_defectueux")
check("append-only : 2 entrées conservées (pas d'écrasement)", len(bb.lis("gravite")) == 2)
check("en_conflit détecte 2 valeurs distinctes", bb.en_conflit("gravite"))
check("valeurs distinctes listées pour arbitrage", set(bb.valeurs("gravite")) == {9.81, 9.83})
check("pas de conflit quand une seule valeur", not bb.en_conflit("COP_max"))

print(f"\n=== valide_blackboard : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
