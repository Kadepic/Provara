"""
VALIDATION du THÉORÈME DU JURY DE CONDORCET (jury_condorcet.py). Vérifie : votants indépendants COMPÉTENTS → précision
majoritaire ↑ vers 1 (sagesse des foules réelle) ; INCOMPÉTENTS → ↓ vers 0 (majorité de plus en plus FAUSSE) ; CORRÉLÉS
→ PLATEAU loin de 1 (ajouter des votants n'aide presque plus) ; la foule compétente bat l'individu ; l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import jury_condorcet as J
from jury_condorcet import ABSTENTION, ANALYSE

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


T = 6000

# ─── 1. Indépendants compétents : ↑ vers 1 ───
print("=== Indépendants compétents (p=0.6) ===")
st, info = J.analyse(0.6, kappa=None, T=T, rng=random.Random(117))
accs = [a for _, a in info["courbe"]]
print(f"   précision : {[round(a,3) for a in accs]}")
check("la précision majoritaire CROÎT avec N", accs[0] < accs[1] < accs[2])
check("à grand N elle approche 1 (sagesse des foules)", accs[-1] > 0.98)
check("la foule bat largement l'individu (0.6)", accs[-1] > 0.6 + 0.3)

# ─── 2. Incompétents : ↓ vers 0 (majorité fausse) ───
print("=== Incompétents (p=0.45 < ½) ===")
sti, infoi = J.analyse(0.45, kappa=None, T=T, rng=random.Random(2))
accsi = [a for _, a in infoi["courbe"]]
print(f"   précision : {[round(a,3) for a in accsi]}")
check("la précision DÉCROÎT avec N (majorité de plus en plus fausse)", accsi[0] > accsi[1] > accsi[2])
check("à grand N la majorité est presque toujours FAUSSE", accsi[-1] < 0.15)

# ─── 3. Corrélés : plateau loin de 1 ───
print("=== Corrélés (p=0.6, forte corrélation) ===")
stc, infoc = J.analyse(0.6, kappa=5, T=T, rng=random.Random(3))
accsc = [a for _, a in infoc["courbe"]]
print(f"   précision : {[round(a,3) for a in accsc]}")
check("la précision PLAFONNE bien en dessous de 1", accsc[-1] < 0.8)
check("ajouter des votants (×18) n'aide presque plus (plateau)", abs(accsc[-1] - accsc[0]) < 0.1)
check("le corrélé fait bien pire que l'indépendant compétent à grand N", accsc[-1] < accs[-1] - 0.2)

# ─── 4. Honnêteté : sous les hypothèses, la sagesse des foules est réelle ───
print("=== Honnêteté : le théorème fonctionne sous ses hypothèses ===")
check("indépendant + compétent : la foule converge bien vers la vérité", info["monte"] and accs[-1] > 0.95)
check("formule (indépendant) parle de sagesse des foules réelle", "sagesse des foules réelle" in J.formule((st, info)))
check("formule (corrélé) signale le plafond", "PLAFONNE" in J.formule((stc, infoc)))
check("formule signale la sur-confiance de « plus de votants = mieux »", "sur-confiant" in J.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", J.analyse(rng=None)[0] == ABSTENTION)
check("p hors ]0,1[ → ABSTENTION", J.analyse(1.5, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT jury_condorcet : {ok}/{total}")
assert ok == total
