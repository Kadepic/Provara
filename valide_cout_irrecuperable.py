"""
VALIDATION du SOPHISME DU COÛT IRRÉCUPÉRABLE (cout_irrecuperable.py). Vérifie : l'INVARIANCE de la décision rationnelle au
coût irrécupérable ; le basculement du biais avec S (poursuite d'un projet perdant) ; la PERTE d'argent en espérance vs
l'agent rationnel (simulation) ; l'escalade Concorde ; l'innocuité sur un bon projet (honnêteté) ; l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import cout_irrecuperable as SC
from cout_irrecuperable import ABSTENTION, ANALYSE

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


# ─── 1. La décision rationnelle est INVARIANTE au coût irrécupérable ───
print("=== Invariance de la décision rationnelle ===")
decisions = {SC.continuer_rationnel(8.0, 10.0) for s in (0, 5, 20, 100)}  # E[V]<C : toujours 'arrêter'
decisions_bon = {SC.continuer_rationnel(15.0, 10.0) for s in (0, 5, 20, 100)}
check("la décision rationnelle ne dépend pas de S (projet perdant → toujours arrêter)", decisions == {False})
check("la décision rationnelle ne dépend pas de S (bon projet → toujours continuer)", decisions_bon == {True})

# ─── 2. Le biais bascule avec S (poursuite d'un projet perdant) ───
print("=== Le biais bascule avec le coût irrécupérable ===")
b_petit = SC.continuer_cout_irrecuperable(8.0, 10.0, 0.0)
b_grand = SC.continuer_cout_irrecuperable(8.0, 10.0, 20.0)
print(f"   projet perdant E[V]=8<C=10 : biais S=0 → {b_petit} ; biais S=20 → {b_grand}")
check("sans coût irrécupérable, le biais arrête (comme le rationnel)", not b_petit)
check("avec gros coût irrécupérable, le biais POURSUIT le projet perdant", b_grand)
info = SC.analyse(8.0, 10.0, 20.0)[1]
check("la façade détecte l'erreur du biais", info["erreur_biais"])

# ─── 3. Le biais PERD de l'argent en espérance (simulation) ───
print("=== Le biais perd de l'argent ===")
rng = random.Random(111)
C = 10.0
gain_rat = gain_biais = 0.0
for _ in range(20000):
    ev = rng.uniform(2, 18)                    # valeur espérée du projet
    sunk = rng.uniform(10, 40)                 # gros coût déjà engagé
    v_real = ev + rng.gauss(0, 2)              # valeur réalisée
    cr = SC.continuer_rationnel(ev, C)
    cb = SC.continuer_cout_irrecuperable(ev, C, sunk)
    gain_rat += SC.payoff_forward(cr, v_real, C)
    gain_biais += SC.payoff_forward(cb, v_real, C)
print(f"   gain forward moyen : rationnel={gain_rat/20000:.3f} ; biaisé={gain_biais/20000:.3f}")
check("l'agent rationnel gagne plus que l'agent à coût irrécupérable", gain_rat > gain_biais)
check("le rationnel ne réalise jamais de perte forward (n'entre que si E[V]>C)", gain_rat >= -1.0)

# ─── 4. Escalade Concorde ───
print("=== Escalade d'engagement (Concorde) ===")
r, b, pr, pb = SC.escalade_concorde([8, 7, 6, 5, 4], 10.0, 20.0)
print(f"   arrêt rationnel à l'étape {r} (payé {pr:.0f}) ; biaisé à {b} (payé {pb:.0f})")
check("le rationnel arrête tôt (projet perdant dès le départ)", r == 0)
check("le biaisé escalade et paie beaucoup plus", b > r and pb > pr)

# ─── 5. Honnêteté : sur un BON projet, le biais ne nuit pas ───
print("=== Honnêteté : bon projet ===")
info_bon = SC.analyse(15.0, 10.0, 20.0)[1]
check("sur un bon projet (E[V]>C), rationnel et biais continuent tous deux", info_bon["continuer_rationnel"] and info_bon["continuer_biaise"] and not info_bon["erreur_biais"])
check("formule signale la sur-confiance du coût irrécupérable", "sur-confiant" in SC.formule((ANALYSE, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("coûts négatifs → ABSTENTION", SC.analyse(8.0, -1.0, 20.0)[0] == ABSTENTION)
check("cas valide → ANALYSE", SC.analyse(8.0, 10.0, 20.0)[0] == ANALYSE)

print(f"\nRÉSULTAT cout_irrecuperable : {ok}/{total}")
assert ok == total
