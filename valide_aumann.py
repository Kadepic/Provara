"""
VALIDATION du THÉORÈME D'ACCORD D'AUMANN (aumann.py). Vérifie : à PRIOR COMMUN, des postérieurs initialement DIFFÉRENTS
convergent vers une valeur ÉGALE après échange (impossibilité de « convenir d'être en désaccord ») ; la convergence est
finie ; à PRIORS DIFFÉRENTS un désaccord persiste (honnêteté : le théorème requiert un prior commun) ; le désaccord force
une information privée non partagée à se révéler ; l'ABSTENTION. Pur Python déterministe.
"""
from __future__ import annotations

from garde_ressources import borne
import aumann as A
from aumann import ABSTENTION, ANALYSE

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


Omega = list(range(8))
E = {0, 1, 2, 3}
P1 = [{0, 1}, {2, 3}, {4, 5}, {6, 7}]
P2 = [{1, 2}, {3, 4}, {5, 6}, {7, 0}]            # cyclique → connaissance commune via dialogue

# ─── 1. Prior commun : désaccord initial → accord après échange ───
print("=== Prior commun : convergence vers l'accord ===")
st, info = A.analyse(Omega, P1, P2, E, omega=0)
print(f"   init=({info['init1']:.2f}, {info['init2']:.2f}) → final=({info['final1']:.3f}, {info['final2']:.3f}) en {info['rounds']} tours")
check("les postérieurs initiaux DIFFÈRENT", abs(info["init1"] - info["init2"]) > 1e-6)
check("après échange, les postérieurs sont ÉGAUX (Aumann)", info["egaux"])
check("la convergence se fait en un nombre fini de tours", info["rounds"] >= 1)

# ─── 2. La convergence vaut pour TOUS les états (prior commun) ───
print("=== Accord à tous les états (prior commun) ===")
tous_egaux = all(A.dialogue(Omega, P1, P2, E, w)["egaux"] for w in Omega)
check("à prior commun, les postérieurs finaux sont égaux en tout état", tous_egaux)

# ─── 3. Priors DIFFÉRENTS (même info) : désaccord persistant ───
print("=== Priors différents : désaccord légitime ===")
Pc = [{0, 4}, {1, 5}, {2, 6}, {3, 7}]            # cellule {0,4} mêle E et non-E
pr1 = {s: 1 / 8 for s in Omega}
pr2 = {s: (0.4 if s in E else 0.1) for s in Omega}
tot = sum(pr2.values()); pr2 = {s: v / tot for s, v in pr2.items()}
st3, info3 = A.analyse(Omega, Pc, Pc, E, omega=0, prior1=pr1, prior2=pr2)
print(f"   priors différents : final=({info3['final1']:.3f}, {info3['final2']:.3f}) égaux={info3['egaux']}")
check("avec des priors DIFFÉRENTS, le désaccord PERSISTE", not info3["egaux"])
check("le théorème ne s'applique pas hors prior commun (honnêteté)", abs(info3["final1"] - info3["final2"]) > 0.1)

# ─── 4. Même partition + prior COMMUN → accord immédiat ───
print("=== Contrôle : même info + prior commun → accord ===")
st4, info4 = A.analyse(Omega, Pc, Pc, E, omega=0)          # priors communs (défaut)
check("même information et prior commun → postérieurs égaux", info4["egaux"])

# ─── 5. Formules & ABSTENTION ───
print("=== Formules & ABSTENTION ===")
check("formule (prior commun) signale la sur-confiance du désaccord", "sur-confiant" in A.formule((st, info)))
check("formule (priors différents) invoque la condition de prior commun", "prior commun" in A.formule((st3, info3)))
check("partition ne couvrant pas Ω → ABSTENTION", A.analyse(Omega, [{0, 1}], P2, E, omega=0)[0] == ABSTENTION)
check("état hors Ω → ABSTENTION", A.analyse(Omega, P1, P2, E, omega=99)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT aumann : {ok}/{total}")
assert ok == total
