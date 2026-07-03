"""
PALIER 2 — TEST D'HYPOTHÈSE DE CALIBRATION (brique 27, 2026-06-25).

L'ECE (calibration.py) ESTIME un écart, mais ne dit pas s'il est SIGNIFICATIF (un petit ECE peut être du bruit, un
gros peut venir d'un petit échantillon). Ici on TESTE statistiquement « le forecaster est-il calibré ? » et on renvoie
une p-VALEUR — avec ERREUR DE TYPE I CONTRÔLÉE (on ne crie pas « mal calibré » plus de α du temps quand il l'est).

Deux tests propres, sans dépendance :
  • SPIEGELHALTER (Z) — sans binning : Z = Σ(yᵢ−pᵢ)(1−2pᵢ) / √Σ(1−2pᵢ)²pᵢ(1−pᵢ) ~ N(0,1) sous H0 (calibré).
  • HOSMER-LEMESHOW (χ²) — par casiers : Σ_g (O_g−E_g)² / (N_g·π_g(1−π_g)) ~ χ²(n_casiers) sous H0.

INVARIANT : sous H0 (vraiment calibré), la p-valeur est ~uniforme -> rejet à ~α (faux positifs contrôlés). Sous
mal-calibration réelle, p petite (puissance). ABSTENTION si trop peu de données. Pur Python (erf + gamma incomplète).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
CALIBRE = "calibre"
NON_CALIBRE = "non_calibre"
N_MIN = 30


def _phi(x):
    """CDF normale standard via erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _gammap(a, x):
    """Fonction gamma incomplète régularisée inférieure P(a,x) (série + fraction continue, Numerical Recipes)."""
    if x <= 0:
        return 0.0
    if x < a + 1.0:
        # série
        ap = a
        somme = 1.0 / a
        terme = somme
        for _ in range(200):
            ap += 1.0
            terme *= x / ap
            somme += terme
            if abs(terme) < abs(somme) * 1e-12:
                break
        return somme * math.exp(-x + a * math.log(x) - math.lgamma(a))
    # fraction continue pour Q, puis P = 1 - Q
    b = x + 1.0 - a
    c = 1e300
    d = 1.0 / b
    h = d
    for i in range(1, 200):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    q = math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
    return 1.0 - q


def _chi2_sf(x, df):
    """Survie (1 − CDF) de la loi du χ² à df degrés de liberté."""
    return 1.0 - _gammap(df / 2.0, x / 2.0)


def test_spiegelhalter(probas, issues):
    """Renvoie (Z, p_valeur_bilaterale). Sous H0 (calibré), Z ~ N(0,1)."""
    p = [float(v) for v in probas]
    y = [1.0 if v else 0.0 for v in issues]
    num = sum((y[i] - p[i]) * (1.0 - 2.0 * p[i]) for i in range(len(p)))
    den = math.sqrt(sum((1.0 - 2.0 * p[i]) ** 2 * p[i] * (1.0 - p[i]) for i in range(len(p))))
    if den <= 0:
        return (0.0, 1.0)
    Z = num / den
    return (Z, 2.0 * (1.0 - _phi(abs(Z))))


def test_hosmer_lemeshow(probas, issues, n_casiers=10):
    """Renvoie (chi2, df, p_valeur). Casiers par quantiles de proba ; χ² ~ chi2(n_casiers) sous H0."""
    p = [float(v) for v in probas]
    y = [1.0 if v else 0.0 for v in issues]
    idx = sorted(range(len(p)), key=lambda i: p[i])
    n = len(p)
    chi2 = 0.0
    used = 0
    taille = max(1, n // n_casiers)
    g = 0
    i = 0
    while i < n:
        groupe = idx[i:i + taille]
        i += taille
        if not groupe:
            continue
        Ng = len(groupe)
        Eg = sum(p[j] for j in groupe)
        Og = sum(y[j] for j in groupe)
        pi_g = Eg / Ng
        var = Ng * pi_g * (1.0 - pi_g)
        if var > 1e-9:
            chi2 += (Og - Eg) ** 2 / var
            used += 1
        g += 1
    df = max(1, used)
    return (chi2, df, _chi2_sf(chi2, df))


def est_calibre_test(probas, issues, alpha=0.05, methode="spiegelhalter", n_casiers=10):
    """VERDICT : (CALIBRE/NON_CALIBRE/ABSTENTION, infos). On REJETTE la calibration (NON_CALIBRE) si p < alpha.
    NON-rejet = « pas de mal-calibration détectée » (pas une preuve de calibration). ABSTENTION si trop peu."""
    n = len(list(probas))
    if n < N_MIN:
        return (ABSTENTION, {"n": n, "raison": f"trop peu de données (n={n} < {N_MIN})"})
    if methode == "hosmer":
        chi2, df, pval = test_hosmer_lemeshow(probas, issues, n_casiers)
        infos = {"n": n, "statistique": chi2, "df": df, "p_valeur": pval, "methode": "hosmer-lemeshow"}
    else:
        Z, pval = test_spiegelhalter(probas, issues)
        infos = {"n": n, "statistique": Z, "p_valeur": pval, "methode": "spiegelhalter"}
    return (NON_CALIBRE if pval < alpha else CALIBRE, infos)


def formule(verdict_infos) -> str:
    verdict, infos = verdict_infos
    if verdict == ABSTENTION:
        return f"Je ne peux pas tester la calibration : {infos.get('raison')}."
    if verdict == NON_CALIBRE:
        return (f"Test {infos['methode']} : calibration REJETÉE (p={infos['p_valeur']:.4f}) — l'écart n'est pas du hasard.")
    return (f"Test {infos['methode']} : pas de mal-calibration détectée (p={infos['p_valeur']:.3f}) — "
            "compatible avec un forecaster calibré (ce n'est pas une preuve absolue).")


if __name__ == "__main__":
    print("=== TEST D'HYPOTHÈSE DE CALIBRATION ===\n")
    import random
    rng = random.Random(0)
    p = [rng.random() for _ in range(2000)]
    y_cal = [1 if rng.random() < pi else 0 for pi in p]                 # calibré
    y_sur = [1 if rng.random() < (pi ** 2.5 / (pi ** 2.5 + (1 - pi) ** 2.5)) else 0 for pi in p]  # mal calibré
    print("  calibré      :", formule(est_calibre_test(p, y_cal)))
    print("  sur-confiant :", formule(est_calibre_test(p, y_sur)))
