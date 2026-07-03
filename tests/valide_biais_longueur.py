"""
VALIDATION du BIAIS DE LONGUEUR (biais_longueur.py). Vérifie : l'identité μ_biaisée = E[X²]/E[X] = μ + σ²/μ ; la
simulation de l'échantillonnage biaisé en taille (moyenne ≈ μ_biaisée > μ) ; la correction harmonique qui récupère μ ;
l'écart croissant avec la dispersion ; le paradoxe d'amitié (degré voisin ≥ degré moyen, égalité si graphe régulier) ;
l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import biais_longueur as BL
from biais_longueur import ABSTENTION, ANALYSE

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


rng = random.Random(102)
tailles = [1, 1, 2, 3, 5, 8, 13, 21, 50, 100]

# ─── 1. Identité μ_biaisée = μ + σ²/μ ───
print("=== Identité μ_biaisée = μ + σ²/μ ===")
mu = BL.moyenne(tailles)
mb = BL.moyenne_biaisee_taille(tailles)
identite = mu + BL.variance(tailles) / mu
print(f"   μ={mu:.3f} ; μ_biaisée={mb:.3f} ; μ+σ²/μ={identite:.3f}")
check("μ_biaisée = E[X²]/E[X] = μ + σ²/μ", abs(mb - identite) < 1e-9)
check("μ_biaisée > μ (biais strictement positif)", mb > mu)

# ─── 2. Simulation de l'échantillonnage biaisé ───
print("=== Simulation : l'échantillon biaisé sur-estime μ ===")
ech = BL.echantillonne_biais_taille(tailles, 300000, rng)
m_ech = BL.moyenne(ech)
print(f"   moyenne échantillon biaisé simulé={m_ech:.2f} ; théorie={mb:.2f} ; μ réel={mu:.2f}")
check("la moyenne simulée biaisée colle à la théorie E[X²]/E[X]", abs(m_ech - mb) < 1.0)
check("la moyenne biaisée sur-estime fortement μ", m_ech > 1.5 * mu)

# ─── 3. Correction harmonique récupère μ ───
print("=== Correction harmonique ===")
mu_corr = BL.correction_harmonique(ech)
print(f"   correction harmonique={mu_corr:.2f} ; μ réel={mu:.2f}")
check("la moyenne harmonique de l'échantillon biaisé récupère μ", abs(mu_corr - mu) < 0.5)

# ─── 4. L'écart croît avec la dispersion ───
print("=== L'écart croît avec la dispersion ===")
serre = [10, 11, 9, 10, 12, 8]                  # peu dispersé
disperse = [1, 2, 5, 20, 80, 200]               # très dispersé
e_serre = BL.analyse(serre)[1]["ecart"]
e_disp = BL.analyse(disperse)[1]["ecart"]
print(f"   écart (serré)={e_serre:.2f} ; écart (dispersé)={e_disp:.2f}")
check("plus la population est dispersée, plus le biais est grand", e_disp > 10 * e_serre)
check("ecart = σ²/μ (théorique)", abs(BL.analyse(tailles)[1]["ecart"] - BL.analyse(tailles)[1]["ecart_theorique"]) < 1e-9)

# ─── 5. Paradoxe d'amitié ───
print("=== Paradoxe d'amitié ===")
# étoile : centre relié à 4 feuilles → forte variance de degré
etoile = {0: [1, 2, 3, 4], 1: [0], 2: [0], 3: [0], 4: [0]}
dm = BL.degre_moyen(etoile)
dv = BL.degre_voisin_moyen(etoile)
print(f"   étoile : degré moyen={dm:.2f} ; degré moyen d'un voisin={dv:.2f}")
check("le degré moyen d'un voisin dépasse le degré moyen (paradoxe d'amitié)", dv > dm)
# graphe régulier (cycle) : pas de paradoxe (variance de degré nulle)
cycle = {0: [1, 3], 1: [0, 2], 2: [1, 3], 3: [2, 0]}
check("graphe régulier : degré voisin = degré moyen (pas de paradoxe)", abs(BL.degre_voisin_moyen(cycle) - BL.degre_moyen(cycle)) < 1e-9)
check("formule signale la sur-confiance de l'échantillon biaisé", "sur-confiant" in BL.formule(BL.analyse(tailles)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("< 3 éléments → ABSTENTION", BL.analyse([5, 10])[0] == ABSTENTION)
check("taille ≤ 0 → ABSTENTION", BL.analyse([5, 0, 10])[0] == ABSTENTION)
check("cas valide → ANALYSE", BL.analyse(tailles)[0] == ANALYSE)

print(f"\nRÉSULTAT biais_longueur : {ok}/{total}")
assert ok == total
