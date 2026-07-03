"""
VALIDATION du PARADOXE D'ELLSBERG (ellsberg.py). Vérifie : AUCUN prior unique n'exhibe le schéma d'Ellsberg (scan) ;
les préférences EU des deux paires sont gouvernées par la MÊME condition (P(noir)<1/3) ⇒ cohérence forcée ; un agent
maxmin (averse à l'ambiguïté) le reproduit ; la décomposition à conséquence commune (jaune) ; l'ABSTENTION. rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import ellsberg as EL
from ellsberg import ABSTENTION, ANALYSE

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


rng = random.Random(124)

# ─── 1. Aucun prior unique n'exhibe Ellsberg ───
print("=== Aucun prior unique n'exhibe Ellsberg ===")
exhibe = 0
for _ in range(200000):
    pB = rng.uniform(0, EL.P_NOIR_OU_JAUNE)
    if EL.schema_ellsberg(*EL.paris_eu(pB)):
        exhibe += 1
print(f"   priors EU exhibant Ellsberg sur 200000 = {exhibe}")
check("aucune probabilité unique n'exhibe le schéma d'Ellsberg (impossibilité)", exhibe == 0)

# ─── 2. Cohérence EU : A≻B ⟺ C≻D (même condition P(noir)<1/3) ───
print("=== Cohérence EU : A≻B ⟺ C≻D ===")
meme = 0
for _ in range(50000):
    pB = rng.uniform(0, EL.P_NOIR_OU_JAUNE)
    A, B, C, D = EL.paris_eu(pB)
    if (A > B) == (C > D):
        meme += 1
print(f"   A≻B ⟺ C≻D sur 50000 = {meme}")
check("un agent EU préfère A à B SSI il préfère C à D (cohérence)", meme == 50000)

# ─── 3. Contradiction : A≻B exige pB<1/3, D≻C exige pB>1/3 ───
print("=== Contradiction des conditions ===")
A1, B1, C1, D1 = EL.paris_eu(0.2)        # pB<1/3
check("à pB=0.2<1/3 : A≻B vrai", A1 > B1)
check("à pB=0.2<1/3 : D≻C FAUX (donc pas Ellsberg)", not (D1 > C1))
A2, B2, C2, D2 = EL.paris_eu(0.5)        # pB>1/3
check("à pB=0.5>1/3 : D≻C vrai", D2 > C2)
check("à pB=0.5>1/3 : A≻B FAUX (donc pas Ellsberg)", not (A2 > B2))

# ─── 4. Agent averse à l'ambiguïté (maxmin) exhibe Ellsberg ───
print("=== Aversion à l'ambiguïté (maxmin) reproduit Ellsberg ===")
st, info = EL.analyse()
print(f"   eu_ellsberg={info['eu_ellsberg']} ; maxmin_ellsberg={info['maxmin_ellsberg']}")
check("l'agent EU n'exhibe pas Ellsberg", not info["eu_ellsberg"])
check("l'agent maxmin (probabilités inférieures) exhibe Ellsberg", info["maxmin_ellsberg"])
A, B, C, D = EL.paris_maxmin()
check("maxmin : A(1/3) > B(0) et D(2/3) > C(1/3)", A > B and D > C)

# ─── 5. Décomposition à conséquence commune (jaune) ───
print("=== Conséquence commune (jaune) ===")
pB = 0.25
pR, pBl, pC, pD = EL.paris_eu(pB)
pY = EL.P_NOIR_OU_JAUNE - pB
check("C = P(rouge) + P(jaune) (A avec jaune ajouté)", abs(pC - (EL.P_ROUGE + pY)) < 1e-12)
check("D = P(noir) + P(jaune) (B avec le MÊME jaune ajouté)", abs(pD - (pB + pY)) < 1e-12)
check("formule signale la sur-confiance du prior unique", "sur-confiant" in EL.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("pB hors [0,2/3] → ABSTENTION", EL.analyse(pB=0.9)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT ellsberg : {ok}/{total}")
assert ok == total
