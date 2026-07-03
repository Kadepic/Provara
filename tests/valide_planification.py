"""VALIDATION planification.py (Vague 5). FAUX=0 : plan re-joué atteint le but ; pas de plan -> None ; longueur minimale."""
from __future__ import annotations
from planification import Operateur, plan, atteignable, _verifie

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Monde des blocs simplifié : amener "porte_ouverte" en passant par "clef" puis "deverrouille".
ops = [
    Operateur("prendre_clef", pre={"clef_visible"}, ajoute={"a_clef"}, retire={"clef_visible"}),
    Operateur("deverrouiller", pre={"a_clef"}, ajoute={"deverrouille"}),
    Operateur("ouvrir_porte", pre={"deverrouille"}, ajoute={"porte_ouverte"}),
]
p = plan({"clef_visible"}, {"porte_ouverte"}, ops)
check("plan trouvé", p is not None)
check("plan = [prendre_clef, deverrouiller, ouvrir_porte]", p == ["prendre_clef", "deverrouiller", "ouvrir_porte"])
check("le plan RE-JOUÉ atteint réellement le but (FAUX=0)", _verifie(frozenset({"clef_visible"}), frozenset({"porte_ouverte"}), p, ops))
check("but déjà atteint -> plan vide", plan({"porte_ouverte"}, {"porte_ouverte"}, ops) == [])

# FAUX=0 : but inatteignable -> None (pas de séquence fabriquée)
check("but inatteignable (pas de clef) -> None", plan(set(), {"porte_ouverte"}, ops) is None)
check("atteignable() cohérent", atteignable({"clef_visible"}, {"porte_ouverte"}, ops)
      and not atteignable(set(), {"porte_ouverte"}, ops))

# Longueur minimale : un raccourci direct est préféré
ops2 = ops + [Operateur("passe_magique", pre={"clef_visible"}, ajoute={"porte_ouverte"})]
check("BFS trouve le plan le plus court (1 pas via passe_magique)",
      len(plan({"clef_visible"}, {"porte_ouverte"}, ops2)) == 1)

# But composite (plusieurs littéraux)
ops3 = [Operateur("a", ajoute={"x"}), Operateur("b", ajoute={"y"})]
pc = plan(set(), {"x", "y"}, ops3)
check("but composite {x,y} atteint (2 actions)", pc is not None and set(pc) == {"a", "b"})

print(f"\n=== valide_planification : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
