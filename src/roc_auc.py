"""
PALIER 2 — AUC (pouvoir DISCRIMINANT) AVEC INTERVALLE DE CONFIANCE (brique, 2026-06-26).

« Mon classifieur a une AUC de 0.82 » — annoncée comme un nombre EXACT. L'AUC = P(un positif tiré au hasard est mieux
scoré qu'un négatif) est elle-même ESTIMÉE sur un échantillon fini : avec peu de positifs/négatifs elle est très
incertaine. Conclure « mon modèle bat 0.5 » ou « bat l'autre » sans intervalle, c'est de la sur-confiance.

Le piège quantitatif classique : calculer l'erreur-type comme si les n₊·n₋ COMPARAISONS par paires étaient INDÉPENDANTES
(SE_naïf = √(AUC(1−AUC)/(n₊n₋))). Elles ne le sont pas — elles partagent les mêmes exemples → cette SE est BIEN trop
petite → intervalle trop étroit → SUR-CONFIANCE. La formule de HANLEY-McNEIL tient compte de cette corrélation (termes
Q1, Q2) et donne un intervalle CALIBRÉ. INVARIANT (jugé par calibration.py) : sur des tirages répétés, l'intervalle de
Hanley couvre la vraie AUC ≈ nominal, l'intervalle « pairs indépendants » s'effondre (sur-confiant). ABSTENTION si une
classe est vide. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def _invnorm(p: float) -> float:
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def auc(scores, labels):
    """AUC par somme de rangs (Mann-Whitney), gestion des ex æquo par rangs moyens. labels ∈ {0,1}. Renvoie None si une
    classe est vide."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    npos, nneg = len(pos), len(neg)
    if npos == 0 or nneg == 0:
        return None
    paires = sorted(zip(scores, labels), key=lambda t: t[0])
    # rangs moyens (1-based)
    rangs = [0.0] * len(paires)
    i = 0
    while i < len(paires):
        j = i
        while j + 1 < len(paires) and paires[j + 1][0] == paires[i][0]:
            j += 1
        moy = (i + j) / 2 + 1
        for k in range(i, j + 1):
            rangs[k] = moy
        i = j + 1
    somme_pos = sum(r for r, (_, y) in zip(rangs, paires) if y == 1)
    return (somme_pos - npos * (npos + 1) / 2) / (npos * nneg)


def _compte(labels):
    npos = sum(1 for y in labels if y == 1)
    return npos, len(labels) - npos


def se_hanley(a, npos, nneg):
    """Erreur-type de Hanley-McNeil (tient compte de la corrélation des comparaisons)."""
    q1 = a / (2 - a) if a < 2 else 0.0
    q2 = 2 * a * a / (1 + a) if a > -1 else 0.0
    var = (a * (1 - a) + (npos - 1) * (q1 - a * a) + (nneg - 1) * (q2 - a * a)) / (npos * nneg)
    return math.sqrt(max(var, 0.0))


def se_naive(a, npos, nneg):
    """Erreur-type NAÏVE : suppose les n₊·n₋ comparaisons INDÉPENDANTES. Trop petite -> sur-confiant."""
    return math.sqrt(a * (1 - a) / (npos * nneg))


def ic_hanley(scores, labels, confiance=0.95):
    a = auc(scores, labels)
    if a is None:
        return None
    npos, nneg = _compte(labels)
    z = _invnorm(1 - (1 - confiance) / 2)
    se = se_hanley(a, npos, nneg)
    return (max(0.0, a - z * se), min(1.0, a + z * se))


def ic_naif(scores, labels, confiance=0.95):
    a = auc(scores, labels)
    if a is None:
        return None
    npos, nneg = _compte(labels)
    z = _invnorm(1 - (1 - confiance) / 2)
    se = se_naive(a, npos, nneg)
    return (max(0.0, a - z * se), min(1.0, a + z * se))


def evalue(scores, labels, confiance=0.95):
    """Façade : (ESTIMATION, (auc, (lo, hi)), confiance) [Hanley] ou (ABSTENTION, None, raison)."""
    a = auc(scores, labels)
    if a is None:
        return (ABSTENTION, None, "une classe est vide (positifs ou négatifs)")
    return (ESTIMATION, (a, ic_hanley(scores, labels, confiance)), confiance)


def bat_le_hasard(scores, labels, confiance=0.95):
    """L'AUC est-elle SIGNIFICATIVEMENT > 0.5 (borne basse de Hanley au-dessus de 0.5) ? Renvoie bool ou None."""
    ic = ic_hanley(scores, labels, confiance)
    return None if ic is None else ic[0] > 0.5


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas évaluer l'AUC : {res[2]}."
    a, (lo, hi) = res[1]
    return (f"AUC = {a:.3f} (IC {round(res[2]*100)}% de Hanley-McNeil : [{lo:.3f}, {hi:.3f}]) — l'intervalle tient "
            f"compte de la taille des deux classes ; une erreur-type « paires indépendantes » serait sur-confiante.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    scores, labels = [], []
    for _ in range(15):
        scores.append(rng.gauss(1.19, 1.0)); labels.append(1)     # positifs (AUC vraie ~0.80)
        scores.append(rng.gauss(0.0, 1.0)); labels.append(0)      # négatifs
    a = auc(scores, labels)
    npos, nneg = _compte(labels)
    print("=== AUC + INTERVALLE — Hanley-McNeil vs « paires indépendantes » (naïf) ===\n")
    print(f"  AUC = {a:.3f}  (n₊={npos}, n₋={nneg}, vraie ≈ 0.80)")
    print(f"  IC 95% Hanley  = {tuple(round(v,3) for v in ic_hanley(scores, labels))}")
    print(f"  IC 95% naïf    = {tuple(round(v,3) for v in ic_naif(scores, labels))}  (trop étroit -> sur-confiant)")
    print(" ", formule(evalue(scores, labels)))
