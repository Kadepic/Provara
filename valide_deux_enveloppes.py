"""
VALIDATION du PARADOXE DES DEUX ENVELOPPES (deux_enveloppes.py). Vérifie : P(petite|a)=½ à l'intérieur mais 1/0 aux
BORNES (le défaut de l'argument naïf) ; le gain conditionnel séduisant +25 % à l'intérieur ; le gain INCONDITIONNEL
EXACTEMENT 0 ; l'égalité rester≈échanger en argent moyen (échangeabilité, simulation) ; la résolution légitime à seuil
(Cover, P(finir grande)>½) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import deux_enveloppes as DE
from deux_enveloppes import ABSTENTION, ANALYSE

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


K = 10

# ─── 1. P(petite|a) : ½ à l'intérieur, 1/0 aux bornes ───
print("=== P(petite | montant observé) : intérieur ½, bornes 1/0 ===")
print(f"   plancher j=0 → {DE.p_petite_sachant(0, K)} ; intérieur j=5 → {DE.p_petite_sachant(5, K)} ; plafond j={K+1} → {DE.p_petite_sachant(K+1, K)}")
check("intérieur : P(petite|a) = ½ (la prémisse naïve y est vraie)", DE.p_petite_sachant(5, K) == 0.5)
check("plancher : P(petite|a) = 1 (la prémisse naïve y est FAUSSE)", DE.p_petite_sachant(0, K) == 1.0)
check("plafond : P(petite|a) = 0 (la prémisse naïve y est FAUSSE)", DE.p_petite_sachant(K + 1, K) == 0.0)

# ─── 2. Gain conditionnel séduisant à l'intérieur (+25 %) ───
print("=== Gain conditionnel intérieur = +25 % (le piège) ===")
for j in (3, 5, 7):
    g = DE.gain_conditionnel(j, K)
    check(f"gain conditionnel à j={j} vaut +0.25·a", abs(g - 0.25 * 2 ** j) < 1e-9)

# ─── 3. Gain INCONDITIONNEL exactement 0 ───
print("=== Gain inconditionnel = 0 (échangeabilité) ===")
gi = DE.esperance_gain_inconditionnel(K)
print(f"   E[échanger − rester] sur l'a priori = {gi}")
check("le gain inconditionnel d'échange est exactement 0", abs(gi) < 1e-12)

# ─── 4. Simulation : rester ≈ échanger (même argent moyen) ───
print("=== Simulation : rester ≈ échanger ===")
rng = random.Random(104)
m_rester, _ = DE.simule(K, 600000, rng, "rester")
m_echanger, _ = DE.simule(K, 600000, rng, "echanger")
print(f"   argent moyen : rester={m_rester:.1f} ; échanger={m_echanger:.1f}")
check("rester et échanger donnent le même argent moyen (à ~1 %)", abs(m_rester - m_echanger) < 0.02 * m_rester)

# ─── 5. Résolution légitime : règle à seuil (Cover) finit avec la grande > ½ ───
print("=== Résolution légitime : règle à seuil (Cover) ===")
_, p_large_seuil = DE.simule(K, 600000, rng, "seuil", seuil=2 ** (K // 2))
_, p_large_rester = DE.simule(K, 600000, rng, "rester")
print(f"   P(finir avec la grande) : seuil={p_large_seuil:.3f} ; rester={p_large_rester:.3f}")
check("la règle à seuil finit avec la grande enveloppe plus souvent que ½", p_large_seuil > 0.5)
check("rester finit avec la grande ½ du temps", abs(p_large_rester - 0.5) < 0.01)

# ─── 6. Cohérence façade ───
print("=== Façade ===")
st, info = DE.analyse(K)
check("la façade expose un gain inconditionnel nul", abs(info["gain_inconditionnel"]) < 1e-12)
check("la façade expose une prémisse intérieure ½", info["p_petite_interieur"] == 0.5)
check("formule signale la sur-confiance du « +25 % »", "sur-confiant" in DE.formule((st, info)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
check("support trop petit (K<2) → ABSTENTION", DE.analyse(1)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT deux_enveloppes : {ok}/{total}")
assert ok == total
