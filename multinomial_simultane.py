"""
PALIER 2 — INTERVALLES DE CONFIANCE SIMULTANÉS POUR DES PARTS MULTINOMIALES (brique, 2026-06-26).

« Un sondage à K options : chaque part p_k a son intervalle à 95 %. » Erreur de MULTIPLICITÉ : annoncer « chacun des K
intervalles est juste à 95 % » et conclure « ILS LE SONT TOUS À LA FOIS à 95 % ». L'événement CONJOINT (toutes les vraies
parts dans leurs intervalles) couvre BIEN MOINS que 95 % dès que K grandit — SUR-CONFIANCE sur la lecture d'ensemble (qui
mène le candidat A, l'écart A−B est-il réel, etc.).

Le remède : des intervalles SIMULTANÉS. Bonferroni = chaque part au niveau 1−α/K (Wilson) → couverture conjointe ≥ 1−α
(garantie, un peu conservatrice). Goodman = inversion du χ² à correction K (plus serré). INVARIANT (jugé par
calibration.py) : la couverture CONJOINTE des intervalles simultanés ≈/≥ nominal ; celle des K intervalles marginaux à
1−α S'EFFONDRE (sur-confiante). Marginalement, chaque intervalle marginal reste correct (le défaut est CONJOINT).
ABSTENTION si n=0 ou < 2 catégories. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def _invnorm(p):
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


def _chi2_quantile(df, q):
    """Quantile de la loi du χ² à df ddl (approximation de Wilson-Hilferty)."""
    z = _invnorm(q)
    t = 1 - 2.0 / (9 * df) + z * math.sqrt(2.0 / (9 * df))
    return df * t ** 3


def _wilson_A(k, n, A):
    """Intervalle de type Wilson pour k/n avec valeur critique A (A = z² niveau normal, ou χ² pour Quesenberry-Hurst)."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + A / n
    centre = (p + A / (2 * n)) / denom
    demi = (math.sqrt(A) / denom) * math.sqrt(p * (1 - p) / n + A / (4 * n * n))
    return (max(0.0, centre - demi), min(1.0, centre + demi))


def marginaux(comptes, confiance=0.95):
    """K intervalles de Wilson INDÉPENDANTS chacun au niveau `confiance` (le piège pour la lecture conjointe)."""
    n = sum(comptes)
    A = _invnorm(1 - (1 - confiance) / 2) ** 2
    return [_wilson_A(k, n, A) for k in comptes]


def simultanes_bonferroni(comptes, confiance=0.95):
    """K intervalles SIMULTANÉS par Bonferroni (= Goodman) : chacun au niveau 1−α/K → couverture conjointe ≥ confiance."""
    n = sum(comptes)
    K = len(comptes)
    alpha = 1 - confiance
    A = _invnorm(1 - (alpha / K) / 2) ** 2          # = χ²₁ au niveau 1−α/K
    return [_wilson_A(k, n, A) for k in comptes]


def simultanes_quesenberry_hurst(comptes, confiance=0.95):
    """Intervalles simultanés de Quesenberry-Hurst : valeur critique COMMUNE χ²_{K−1,1−α} (région de confiance du
    multinomial projetée par coordonnée). Plus conservateur que Bonferroni quand K est grand."""
    n = sum(comptes)
    K = len(comptes)
    A = _chi2_quantile(K - 1, confiance)
    return [_wilson_A(k, n, A) for k in comptes]


def intervalles(comptes, confiance=0.95, methode="bonferroni"):
    """Façade : (ESTIMATION, liste d'intervalles, confiance) ou (ABSTENTION, None, raison)."""
    n = sum(comptes)
    if n <= 0:
        return (ABSTENTION, None, "aucune observation (n=0)")
    if len(comptes) < 2:
        return (ABSTENTION, None, "moins de 2 catégories")
    fn = {"bonferroni": simultanes_bonferroni, "quesenberry_hurst": simultanes_quesenberry_hurst,
          "marginaux": marginaux}.get(methode)
    if fn is None:
        return (ABSTENTION, None, f"méthode inconnue : {methode}")
    return (ESTIMATION, fn(comptes, confiance), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer les parts : {res[2]}."
    K = len(res[1])
    return (f"{K} parts avec intervalles SIMULTANÉS à {round(res[2]*100)}% (la lecture d'ensemble est garantie à ce "
            f"niveau) — {K} intervalles marginaux à {round(res[2]*100)}% seraient sur-confiants pris tous ensemble.")


if __name__ == "__main__":
    comptes = [40, 35, 15, 10]           # sondage à 4 options, n=100
    print("=== PARTS MULTINOMIALES — marginaux vs simultanés (Bonferroni/Goodman) ===\n")
    for nom, ivs in [("marginaux", marginaux(comptes)),
                     ("Bonferroni", simultanes_bonferroni(comptes)),
                     ("Ques.-Hurst", simultanes_quesenberry_hurst(comptes))]:
        larg = sum(hi - lo for lo, hi in ivs) / len(ivs)
        print(f"  {nom:11s} : {[ (round(lo,3),round(hi,3)) for lo,hi in ivs]}  (largeur moy {larg:.3f})")
    print(" ", formule(intervalles(comptes, methode="bonferroni")))
