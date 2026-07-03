"""
PALIER 2 — MATRICE DE CONFUSION, DÉSÉQUILIBRE & TAUX DE BASE : l'exactitude ment quand les classes sont rares
(brique 84, 2026-06-27).

Évaluer un classifieur par son EXACTITUDE (accuracy) est SUR-CONFIANT sous DÉSÉQUILIBRE : sur une maladie touchant 1 %
de la population, un classifieur qui répond TOUJOURS « négatif » a 99 % d'exactitude — et ne détecte RIEN. L'exactitude
récompense la classe majoritaire et masque l'incapacité sur la minorité.

LE TAUX DE BASE (Bayes) : un test « 95 % fiable » (sensibilité=spécificité=0.95) ne donne PAS P(malade | test+) = 95 %.
    P(malade | +) = sens·prév / ( sens·prév + (1−spéc)·(1−prév) ).
À 1 % de prévalence, ça fait ≈ 16 % : la plupart des positifs sont des FAUX positifs. Confondre la fiabilité du test
avec la probabilité a posteriori = la NÉGLIGENCE DU TAUX DE BASE = sur-confiance.

LE MODE D'ÉCHEC DÉMASQUÉ : se fier à l'exactitude (ou à la « fiabilité » d'un test) sous déséquilibre est sur-confiant ;
PRÉCISION/RAPPEL, EXACTITUDE ÉQUILIBRÉE, MCC et le calcul de Bayes donnent l'image honnête. ABSTENTION si données vides
/ prévalence invalide. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
METRIQUES = "metriques"


def confusion(y_vrai, y_pred, positif=1):
    """Compte (TP, FP, TN, FN) pour la classe `positif`."""
    TP = FP = TN = FN = 0
    for yt, yp in zip(y_vrai, y_pred):
        if yp == positif and yt == positif:
            TP += 1
        elif yp == positif and yt != positif:
            FP += 1
        elif yp != positif and yt != positif:
            TN += 1
        else:
            FN += 1
    return TP, FP, TN, FN


def _div(a, b):
    return a / b if b > 0 else 0.0


def exactitude(y_vrai, y_pred, positif=1):
    TP, FP, TN, FN = confusion(y_vrai, y_pred, positif)
    return _div(TP + TN, TP + FP + TN + FN)


def precision(y_vrai, y_pred, positif=1):
    TP, FP, TN, FN = confusion(y_vrai, y_pred, positif)
    return _div(TP, TP + FP)


def rappel(y_vrai, y_pred, positif=1):
    TP, FP, TN, FN = confusion(y_vrai, y_pred, positif)
    return _div(TP, TP + FN)


def specificite(y_vrai, y_pred, positif=1):
    TP, FP, TN, FN = confusion(y_vrai, y_pred, positif)
    return _div(TN, TN + FP)


def f1(y_vrai, y_pred, positif=1):
    p, r = precision(y_vrai, y_pred, positif), rappel(y_vrai, y_pred, positif)
    return _div(2 * p * r, p + r)


def exactitude_equilibree(y_vrai, y_pred, positif=1):
    """(rappel + spécificité)/2 : insensible au déséquilibre (0.5 = aléatoire/inutile)."""
    return (rappel(y_vrai, y_pred, positif) + specificite(y_vrai, y_pred, positif)) / 2


def mcc(y_vrai, y_pred, positif=1):
    """Coefficient de corrélation de Matthews ∈ [−1,1] (0 = inutile), robuste au déséquilibre."""
    TP, FP, TN, FN = confusion(y_vrai, y_pred, positif)
    den = math.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
    return _div(TP * TN - FP * FN, den) if den > 0 else 0.0


def ppv_bayes(sensibilite, specificite, prevalence):
    """P(positif réel | test positif) par Bayes = sens·prév / (sens·prév + (1−spéc)(1−prév)). Démasque le taux de base."""
    num = sensibilite * prevalence
    den = num + (1 - specificite) * (1 - prevalence)
    return _div(num, den)


def analyse(y_vrai, y_pred, positif=1):
    """Façade : (METRIQUES, {exactitude, exactitude_equilibree, precision, rappel, mcc, f1}) ou (ABSTENTION, raison)."""
    if not y_vrai or len(y_vrai) != len(y_pred):
        return (ABSTENTION, "données vides ou tailles différentes")
    return (METRIQUES, {"exactitude": exactitude(y_vrai, y_pred, positif),
                        "exactitude_equilibree": exactitude_equilibree(y_vrai, y_pred, positif),
                        "precision": precision(y_vrai, y_pred, positif), "rappel": rappel(y_vrai, y_pred, positif),
                        "mcc": mcc(y_vrai, y_pred, positif), "f1": f1(y_vrai, y_pred, positif)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de métriques : {res[1]}."
    i = res[1]
    alerte = " ⚠ exactitude trompeuse (déséquilibre : rappel/MCC faibles)" if i["exactitude"] > 0.9 and i["mcc"] < 0.2 else ""
    return (f"Exactitude {i['exactitude']:.3f} mais exactitude ÉQUILIBRÉE {i['exactitude_equilibree']:.3f}, "
            f"rappel {i['rappel']:.3f}, MCC {i['mcc']:.3f}.{alerte}")


if __name__ == "__main__":
    print("=== MATRICE DE CONFUSION, DÉSÉQUILIBRE & TAUX DE BASE ===\n")
    # 1000 cas, 1% positifs ; classifieur qui dit TOUJOURS négatif
    yv = [1] * 10 + [0] * 990
    yp = [0] * 1000
    info = analyse(yv, yp)[1]
    print(f"  'Toujours négatif' (1% positifs) : exactitude={info['exactitude']:.3f} mais rappel={info['rappel']:.3f}, "
          f"exact. équilibrée={info['exactitude_equilibree']:.3f}, MCC={info['mcc']:.3f}")
    print(f"\n  Test 95% fiable (sens=spéc=0.95), prévalence 1% :")
    print(f"   P(malade | test+) = {ppv_bayes(0.95, 0.95, 0.01):.3f} (≈16%, PAS 95% — négligence du taux de base)")
    print(" ", formule(analyse(yv, yp)))
