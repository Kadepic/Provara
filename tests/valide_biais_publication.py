"""
VALIDATION du BIAIS DE PUBLICATION (biais_publication.py). Vérifie : la moyenne PUBLIÉE sur-estime l'effet vrai tandis
que la moyenne de TOUTES les études le recouvre (la sélection cause le biais) ; l'ASYMÉTRIE EN ENTONNOIR (petites études
publiées ≫ grandes) ; les grandes études restent quasi non biaisées même publiées ; l'inflation est plus forte quand
l'effet vrai est petit ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import biais_publication as BP
from biais_publication import ABSTENTION, ANALYSE

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


st, info = BP.analyse(theta=0.2, n_etudes=30000, rng=random.Random(126))

# ─── 1. La moyenne publiée sur-estime l'effet vrai ───
print("=== La moyenne publiée gonfle l'effet ===")
print(f"   θ={info['theta']} ; publiée={info['moyenne_publiee']:.3f} ; toutes={info['moyenne_toutes']:.3f}")
check("la moyenne PUBLIÉE sur-estime l'effet vrai", info["moyenne_publiee"] > info["theta"] + 0.02)
check("la moyenne de TOUTES les études recouvre l'effet vrai (non biaisée)", abs(info["moyenne_toutes"] - info["theta"]) < 0.02)

# ─── 2. Asymétrie en entonnoir ───
print("=== Asymétrie en entonnoir (small-study effect) ===")
print(f"   petites études publiées={info['effet_petites']:.3f} ; grandes={info['effet_grandes']:.3f}")
check("les petites études publiées montrent un effet bien plus grand que les grandes", info["effet_petites"] > info["effet_grandes"] + 0.1)
check("les grandes études restent quasi non biaisées même publiées", abs(info["effet_grandes"] - info["theta"]) < 0.03)

# ─── 3. L'inflation est plus forte quand l'effet vrai est petit ───
print("=== Inflation ↑ quand l'effet vrai est petit ===")
info_petit = BP.analyse(theta=0.05, n_etudes=40000, rng=random.Random(2))[1]
info_grand = BP.analyse(theta=0.4, n_etudes=20000, rng=random.Random(3))[1]
infl_petit = info_petit["moyenne_publiee"] - 0.05
infl_grand = info_grand["moyenne_publiee"] - 0.4
print(f"   inflation : θ=0.05 → +{infl_petit:.3f} ; θ=0.4 → +{infl_grand:.3f}")
check("l'inflation absolue est plus forte pour un petit effet vrai", infl_petit > infl_grand)

# ─── 4. Honnêteté : sans filtre de publication, pas de biais ───
print("=== Honnêteté : sans filtre, moyenne non biaisée ===")
check("la moyenne de toutes les études (sans sélection) ≈ θ", abs(info["moyenne_toutes"] - info["theta"]) < 0.02)
check("formule signale la sur-confiance de la moyenne publiée", "sur-confiant" in BP.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", BP.analyse(rng=None)[0] == ABSTENTION)
check("θ ≤ 0 → ABSTENTION", BP.analyse(theta=0.0, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT biais_publication : {ok}/{total}")
assert ok == total
