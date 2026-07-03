"""
PALIER 2 — INTERVALLE DE CONFIANCE PAR BOOTSTRAP (percentile & BCa) pour une statistique ARBITRAIRE (brique, 2026-06-26).

« J'ai un estimateur compliqué (médiane, variance, ratio, corrélation…) sans formule d'écart-type — quel intervalle de
confiance ? » Le piège classique : RÉUTILISER la formule de l'erreur-type de la MOYENNE (s/√n) pour une statistique qui
varie DAVANTAGE (la médiane d'une normale a une erreur-type ≈ 1,25×s/√n) → intervalle trop ÉTROIT → SUR-CONFIANCE. Plus
généralement, supposer une statistique normale, non biaisée, à variabilité « comme la moyenne » est faux dès qu'elle est
asymétrique ou bornée.

Le BOOTSTRAP rééchantillonne les données AVEC REMISE pour approcher la vraie distribution de θ̂ — sans aucune formule.
L'IC PERCENTILE prend les quantiles empiriques des répliques (il capte la variabilité RÉELLE de la statistique) ; le BCa
(bias-corrected & accelerated) corrige en plus le BIAIS (z0, fraction de répliques sous θ̂) et l'ASYMÉTRIE (a, jackknife),
et respecte les bornes naturelles (p. ex. ρ∈[−1,1]). INVARIANT (jugé par calibration.py) : sur des tirages répétés, la
couverture du bootstrap (percentile/BCa) ≈ nominal, là où l'intervalle NAÏF à formule plaquée s'effondre (sur-confiant).
ABSTENTION si trop peu de points. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 10


def _Phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


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


def _quantile(tri, p):
    """Quantile (interpolation linéaire) d'une liste DÉJÀ triée."""
    if not tri:
        return None
    if p <= 0:
        return tri[0]
    if p >= 1:
        return tri[-1]
    pos = p * (len(tri) - 1)
    lo = int(math.floor(pos))
    frac = pos - lo
    if lo + 1 < len(tri):
        return tri[lo] * (1 - frac) + tri[lo + 1] * frac
    return tri[lo]


def repliques(data, stat, B, rng):
    """B valeurs de `stat` sur des rééchantillonnages avec remise."""
    n = len(data)
    out = []
    for _ in range(B):
        ech = [data[int(rng.random() * n)] for _ in range(n)]
        out.append(stat(ech))
    return out


def ic_normal(data, stat, boot, confiance=0.90):
    """θ̂ ± z·SE_boot (SE = écart-type des répliques bootstrap). Symétrique : mal placé si la stat est asymétrique/bornée,
    mais déjà bien plus honnête qu'une formule d'erreur-type plaquée (cf. ic_naif_moyenne)."""
    theta = stat(data)
    m = sum(boot) / len(boot)
    se = math.sqrt(sum((b - m) ** 2 for b in boot) / (len(boot) - 1))
    z = _invnorm(1 - (1 - confiance) / 2)
    return (theta - z * se, theta + z * se)


def ic_naif_moyenne(data, stat, confiance=0.90):
    """IC NAÏF (le piège) : applique l'erreur-type de la MOYENNE (s/√n) à n'importe quelle statistique. Trop étroit dès
    que la statistique varie plus que la moyenne (médiane, variance…) → sur-confiant. Sert de repoussoir."""
    n = len(data)
    m = sum(data) / n
    s = math.sqrt(sum((x - m) ** 2 for x in data) / (n - 1))
    z = _invnorm(1 - (1 - confiance) / 2)
    theta = stat(data)
    return (theta - z * s / math.sqrt(n), theta + z * s / math.sqrt(n))


def ic_percentile(boot, confiance=0.90):
    tri = sorted(boot)
    a = (1 - confiance) / 2
    return (_quantile(tri, a), _quantile(tri, 1 - a))


def ic_bca(data, stat, boot, confiance=0.90):
    """IC BCa : corrige biais (z0) et accélération/asymétrie (a, jackknife)."""
    theta = stat(data)
    tri = sorted(boot)
    B = len(boot)
    # z0 : correction de biais
    prop = sum(1 for b in boot if b < theta) / B
    prop = min(1 - 1e-6, max(1e-6, prop))
    z0 = _invnorm(prop)
    # a : accélération par jackknife
    n = len(data)
    jack = []
    for i in range(n):
        ech = data[:i] + data[i + 1:]
        jack.append(stat(ech))
    jbar = sum(jack) / n
    num = sum((jbar - j) ** 3 for j in jack)
    den = 6.0 * (sum((jbar - j) ** 2 for j in jack) ** 1.5)
    a = num / den if den != 0 else 0.0
    za = _invnorm((1 - confiance) / 2)
    zb = _invnorm(1 - (1 - confiance) / 2)

    def ajuste(zq):
        return _Phi(z0 + (z0 + zq) / (1 - a * (z0 + zq)))

    a1 = ajuste(za)
    a2 = ajuste(zb)
    return (_quantile(tri, a1), _quantile(tri, a2))


def intervalle(data, stat, confiance=0.90, methode="bca", B=2000, rng=None):
    """Façade : (ESTIMATION, (lo, hi), confiance) ou (ABSTENTION, None, raison). methode ∈ {bca, percentile, normal}."""
    if len(data) < N_MIN:
        return (ABSTENTION, None, f"trop peu de points (n={len(data)} < {N_MIN})")
    if rng is None:
        import random
        rng = random.Random(12345)
    boot = repliques(data, stat, B, rng)
    if methode == "normal":
        iv = ic_normal(data, stat, boot, confiance)
    elif methode == "percentile":
        iv = ic_percentile(boot, confiance)
    else:
        iv = ic_bca(data, stat, boot, confiance)
    return (ESTIMATION, iv, confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer l'intervalle : {res[2]}."
    lo, hi = res[1]
    return (f"Intervalle de confiance bootstrap BCa à {round(res[2]*100)}% : [{lo:.3f}, {hi:.3f}] — il capte la "
            f"variabilité réelle de la statistique (biais et asymétrie corrigés), là où une formule d'erreur-type "
            f"plaquée serait sur-confiante.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    def mediane(xs):
        s = sorted(xs); n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    data = [rng.gauss(0, 1) for _ in range(40)]           # médiane : varie 1,25× plus que la moyenne
    print("=== IC de la MÉDIANE (n=40, vraie médiane=0) — naïf (SE de la moyenne) vs bootstrap ===\n")
    boot = repliques(data, mediane, 3000, random.Random(1))
    print(f"  médiane estimée = {mediane(data):.3f}")
    print(f"  IC NAÏF (SE moyenne) = {tuple(round(v,3) for v in ic_naif_moyenne(data, mediane))}  (trop étroit)")
    print(f"  IC percentile        = {tuple(round(v,3) for v in ic_percentile(boot))}")
    print(f"  IC BCa               = {tuple(round(v,3) for v in ic_bca(data, mediane, boot))}")
    print(" ", formule(intervalle(data, mediane, methode="bca", B=2000, rng=random.Random(2))))
