"""
PALIER 2 — CONTRÔLE DE RISQUE CONFORME (CRC, brique 12, 2026-06-25). Borner un risque CHOISI à une cible.

La prédiction conforme contrôle la COUVERTURE. Le CRC (Angelopoulos et al.) généralise : il contrôle N'IMPORTE QUEL
RISQUE BORNÉ et MONOTONE — ex. le TAUX DE FAUX NÉGATIFS d'un ensemble de prédiction, la fraction d'objet manquée, etc.
On choisit un paramètre λ (seuil / taille d'ensemble) ; le risque empirique R̂(λ) DÉCROÎT quand λ rend la prédiction
plus prudente. Le CRC sélectionne le λ le plus INFORMATIF (prédiction la plus serrée) dont le risque reste contrôlé :

    λ̂ = plus petit λ tel que   (n·R̂(λ) + B) / (n + 1)  ≤  cible        (B = borne sup de la perte, ex. 1)

GARANTIE (distribution-free, sous échangeabilité) : l'espérance du risque sur le test  E[R(λ̂)] ≤ cible. C'est
l'invariant de calibration transposé à un risque arbitraire : on PROMET « FNR ≤ 10 % » et on le TIENT.

Cas phare fourni : contrôle du FNR d'un ensemble de labels (le vrai label est dans l'ensemble ≥ 1−cible), + le
moteur générique pour toute perte bornée monotone. ABSTENTION implicite : si aucune λ ne contrôle, on renvoie la plus
prudente (ensemble le plus large) — jamais une fausse promesse.
"""
from __future__ import annotations

import math

AUCUN = None


def seuil_crc(lambdas, risques_emp, cible, n, B: float = 1.0):
    """Moteur générique. `lambdas` = paramètres candidats TRIÉS du plus informatif (risque le plus haut) au plus
    prudent (risque le plus bas) ; `risques_emp[i]` = R̂(lambdas[i]) sur n points de calibration, supposé NON
    CROISSANT. Renvoie le λ le plus informatif dont (n·R̂+B)/(n+1) ≤ cible, ou le DERNIER (plus prudent) si aucun ne
    contrôle (jamais de fausse promesse). Garantit E[R(λ̂)] ≤ cible."""
    choix = lambdas[-1]            # repli : le plus prudent
    for lam, r in zip(lambdas, risques_emp):
        if (n * r + B) / (n + 1.0) <= cible:
            choix = lam
            break
    return choix


def controle_fnr(scores_vrai_label_cal, cible: float):
    """Contrôle du FNR d'un ensemble de prédiction. `scores_vrai_label_cal` = score (proba/affinité) attribué à la
    VRAIE classe sur le jeu de calibration. Renvoie un SEUIL t tel que l'ensemble {labels: score ≥ t} contienne le
    vrai label avec un FNR ≤ cible (garanti). t = −inf si `cible` est trop petite pour n (on inclut tout : prudent)."""
    s = sorted(float(x) for x in scores_vrai_label_cal)
    n = len(s)
    if n == 0:
        return float("-inf")
    # on veut #{score_vrai < t} ≤ k avec (k+1)/(n+1) ≤ cible -> k = ⌊cible·(n+1)⌋ − 1
    k = math.floor(cible * (n + 1)) - 1
    if k < 0:
        return float("-inf")                 # impossible de garantir avec un seuil fini -> inclure tout
    if k >= n:
        return float("inf")                  # on peut tout exclure (risque déjà contrôlé) — ensemble potentiellement vide
    # seuil = (k+1)-ème plus petit score : alors #{score < t} = k (pour des scores distincts)
    return s[k]


def ensemble_au_seuil(scores_test, seuil):
    """Ensemble de labels {classe: score ≥ seuil}. `scores_test` = dict {classe: score}."""
    return {c for c, v in scores_test.items() if float(v) >= seuil}


if __name__ == "__main__":
    print("=== CONTRÔLE DE RISQUE CONFORME (CRC) ===\n")
    import random
    rng = random.Random(0)
    # 4 classes ; score de la vraie classe ~ U(0.2,1) ; on veut FNR ≤ 10%
    sc_vrai = [0.2 + 0.8 * rng.random() for _ in range(500)]
    t = controle_fnr(sc_vrai, 0.10)
    print(f"  seuil FNR≤10% : t = {t:.3f}")
    test = {"A": 0.9, "B": 0.5, "C": 0.25, "D": 0.05}
    print("  ensemble au seuil :", ensemble_au_seuil(test, t))
