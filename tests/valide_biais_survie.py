"""
VALIDATION du BIAIS DE SURVIE (biais_survie.py). Vérifie que la moyenne des survivants SUR-ESTIME la vraie moyenne
(biais positif, croissant avec la sélection), qu'elle correspond à la moyenne tronquée-normale théorique (ratio de
Mills), la sur-estimation du taux de succès, la LEÇON DE WALD (les survivants sous-représentent les zones fatales),
et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import biais_survie as BS
from biais_survie import ABSTENTION, BIAIS

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


rng = random.Random(85)
mu, sigma = 0.05, 0.2
pop = [rng.gauss(mu, sigma) for _ in range(20000)]

# ─── 1. Moyenne des survivants > vraie moyenne (biais positif) ───
print("=== Biais de survie positif ===")
b = BS.biais(pop, 0.0)
print(f"   biais (seuil 0) = +{b:.3f}")
check("moyenne(survivants) > moyenne(population)", b > 0.05)

# ─── 2. Biais croît avec la sélection (seuil plus haut) ───
print("=== Biais croissant avec la sélection ===")
biais_seq = [BS.biais(pop, s) for s in (-0.3, -0.05, 0.05, 0.2)]
print(f"   biais pour seuils croissants : {[round(x,3) for x in biais_seq]}")
check("le biais augmente quand le seuil de survie monte", all(biais_seq[i] <= biais_seq[i+1] + 1e-9 for i in range(len(biais_seq)-1)))

# ─── 3. Concorde avec la moyenne tronquée-normale (ratio de Mills) ───
print("=== Concordance avec la théorie (tronquée-normale) ===")
theo = BS.moyenne_tronquee_normale(mu, sigma, 0.0)
emp = BS.moyenne(BS.survivants(pop, 0.0))
print(f"   E[X|X≥0] : théorie={theo:.3f} ; empirique={emp:.3f}")
check("moyenne des survivants ≈ μ + σ·λ(α) (tronquée-normale)", abs(theo - emp) < 0.01)
check("ratio de Mills > 0 et croissant en α", BS.ratio_mills(0.5) > BS.ratio_mills(-0.5) > 0)

# ─── 4. Sur-estimation du taux de succès ───
print("=== Sur-estimation du taux de succès ===")
p_surv, p_pop = BS.taux_succes_survivant(pop, 0.0, 0.3)
print(f"   P(rendement≥0.30) : survivants={p_surv:.3f} vs population={p_pop:.3f}")
check("le taux de succès est sur-estimé chez les survivants", p_surv > p_pop)

# ─── 5. LEÇON DE WALD : les survivants sous-représentent les zones fatales ───
print("=== Leçon de Wald : zones touchées des survivants ≠ zones fatales ===")
# chaque avion touché au MOTEUR (fatal, P(retour)=0.1) ou à l'AILE (survivable, P(retour)=0.9)
moteur_all = moteur_surv = total_all = total_surv = 0
for _ in range(20000):
    region = "moteur" if rng.random() < 0.5 else "aile"
    revient = rng.random() < (0.1 if region == "moteur" else 0.9)
    total_all += 1; moteur_all += (region == "moteur")
    if revient:
        total_surv += 1; moteur_surv += (region == "moteur")
p_moteur_all = moteur_all / total_all
p_moteur_surv = moteur_surv / total_surv
print(f"   P(touché au moteur) : tous={p_moteur_all:.3f} ; survivants={p_moteur_surv:.3f}")
check("la zone FATALE (moteur) est SOUS-représentée chez les survivants", p_moteur_surv < p_moteur_all - 0.2)
# => blinder là où les survivants SONT touchés (aile) est l'erreur ; le signal est dans la donnée manquante

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = BS.analyse([], 0.0)
st2, _ = BS.analyse([0.1, 0.2], 5.0)        # aucun survivant
check("population vide → ABSTENTION", st1 == ABSTENTION)
check("aucun survivant → ABSTENTION", st2 == ABSTENTION)
st3, _ = BS.analyse(pop, 0.0)
check("cas valide → BIAIS", st3 == BIAIS)

print(f"\nRÉSULTAT biais_survie : {ok}/{total}")
assert ok == total
