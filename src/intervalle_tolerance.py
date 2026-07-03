"""
PALIER 2 — INTERVALLE DE TOLÉRANCE (contenir une PROPORTION de la population, pas la moyenne) (brique, 2026-06-26).

Confusion classique et coûteuse : « l'intervalle de confiance à 95 % de la moyenne est [70, 72] kg » lu comme « 95 % des
individus pèsent 70-72 kg ». FAUX — l'IC de la moyenne se RESSERRE avec n (il borne une MOYENNE), il ne dit RIEN des
individus. Même un naïf x̄ ± z_β·s SOUS-couvre la population : il ignore que x̄ et s sont ESTIMÉS (sur petit échantillon,
la vraie dispersion est sous-estimée trop souvent) — d'où une promesse SUR-CONFIANTE sur les individus.

L'INTERVALLE DE TOLÉRANCE x̄ ± k·s vise une garantie DOUBLE (β, γ) : « au moins une proportion β de la population, avec
confiance γ ». Le facteur k (approximation de Howe : k = z_(1+β)/2·√(ν(1+1/n)/χ²_{ν,1−γ}), ν=n−1) gonfle pour absorber
l'incertitude d'estimation. INVARIANT (jugé par calibration.py) : sur des échantillons répétés, la fraction où
l'intervalle de tolérance contient ≥ β de la population est ≥ γ ; le naïf x̄ ± z_β·s tombe sous β trop souvent
(sur-confiant) ; l'IC de la moyenne est ridiculement étroit pour les individus. ABSTENTION si n trop petit. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 5


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


def _Phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _chi2_quantile(df, q):
    """Quantile χ² à df ddl (Wilson-Hilferty)."""
    z = _invnorm(q)
    t = 1 - 2.0 / (9 * df) + z * math.sqrt(2.0 / (9 * df))
    return df * max(t, 1e-6) ** 3


def _moyenne_ecart(donnees):
    n = len(donnees)
    m = sum(donnees) / n
    s = math.sqrt(sum((x - m) ** 2 for x in donnees) / (n - 1))
    return m, s, n


def facteur_tolerance(n, beta=0.90, gamma=0.95):
    """Facteur k de l'intervalle de tolérance normal bilatéral (approximation de Howe)."""
    nu = n - 1
    zb = _invnorm((1 + beta) / 2)
    chi2 = _chi2_quantile(nu, 1 - gamma)
    return zb * math.sqrt(nu * (1 + 1.0 / n) / chi2)


def intervalle_tolerance(donnees, beta=0.90, gamma=0.95):
    """(ESTIMATION, (lo, hi), (beta, gamma)) : contient ≥ β de la population avec confiance γ. Ou ABSTENTION."""
    if len(donnees) < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={len(donnees)} < {N_MIN})")
    m, s, n = _moyenne_ecart(donnees)
    k = facteur_tolerance(n, beta, gamma)
    return (ESTIMATION, (m - k * s, m + k * s), (beta, gamma))


def intervalle_naif(donnees, beta=0.90):
    """NAÏF : x̄ ± z_(1+β)/2·s (ignore que x̄, s sont estimés). Sous-couvre la population -> sur-confiant."""
    m, s, n = _moyenne_ecart(donnees)
    z = _invnorm((1 + beta) / 2)
    return (m - z * s, m + z * s)


def ic_moyenne(donnees, confiance=0.95):
    """IC de la MOYENNE (se resserre en 1/√n) : à NE PAS confondre avec un intervalle pour les individus."""
    m, s, n = _moyenne_ecart(donnees)
    z = _invnorm(1 - (1 - confiance) / 2)
    demi = z * s / math.sqrt(n)
    return (m - demi, m + demi)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer l'intervalle de tolérance : {res[2]}."
    lo, hi = res[1]
    beta, gamma = res[2]
    return (f"Intervalle de TOLÉRANCE [{lo:.2f}, {hi:.2f}] : contient au moins {round(beta*100)}% de la population avec "
            f"{round(gamma*100)}% de confiance — bien plus large que l'IC de la moyenne, qu'il ne faut pas confondre "
            f"avec une garantie sur les individus.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    data = [rng.gauss(71.0, 5.0) for _ in range(20)]      # poids, n=20
    st, (lo, hi), bg = intervalle_tolerance(data, 0.90, 0.95)
    print("=== INTERVALLE DE TOLÉRANCE vs IC de la moyenne vs naïf (n=20) ===\n")
    print(f"  IC moyenne 95%        = {tuple(round(v,2) for v in ic_moyenne(data))}  (borne la MOYENNE)")
    print(f"  naïf x̄±z_β·s (β=0.90) = {tuple(round(v,2) for v in intervalle_naif(data, 0.90))}  (sous-couvre)")
    print(f"  tolérance (0.90,0.95) = ({lo:.2f}, {hi:.2f})  (k={facteur_tolerance(20):.2f})")
    print(" ", formule((st, (lo, hi), bg)))
