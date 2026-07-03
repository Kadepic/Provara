"""
PALIER 2 — INTERVALLE DE CONFIANCE D'UNE PROPORTION BINOMIALE (Wald vs Wilson vs Agresti-Coull) (brique, 2026-06-26).

« k succès sur n essais — quelle est la vraie proportion p, et à quel point en suis-je sûr ? » L'intervalle de WALD,
le plus enseigné (p̂ ± z·√(p̂(1−p̂)/n)), est SUR-CONFIANT : sa couverture réelle tombe BIEN en dessous du nominal
quand n est petit OU p proche de 0/1 (au cas extrême k=0 il donne l'intervalle DÉGÉNÉRÉ [0,0] — « certitude » absurde).
C'est l'archétype de la fausse précision que l'invariant T2 interdit.

L'intervalle de WILSON inverse le test de score : il est tiré vers 1/2, ne sort jamais de [0,1], et reste calibré
(couverture ≈ nominal) même à n petit / p extrême. AGRESTI-COULL = approximation simple de Wilson (« ajoute 2 succès et
2 échecs »), aussi bien calibrée. INVARIANT (jugé par calibration.py) : sur de nombreux (n, p), la couverture EMPIRIQUE
de Wilson/Agresti-Coull ≈ nominal (non sur-confiant), celle de Wald s'effondre (sur-confiant). ABSTENTION si n=0.
Pur Python (closed-form, fonction quantile normale).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def _invnorm(p: float) -> float:
    """Quantile de la normale standard (Acklam). p dans (0,1)."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p hors (0,1)")
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
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _z(confiance: float) -> float:
    return _invnorm(1 - (1 - confiance) / 2)


def wald(k: int, n: int, confiance: float = 0.95):
    """Intervalle de WALD (naïf, SUR-CONFIANT). Renvoie (lo, hi) borné à [0,1]. Dégénéré [p̂,p̂] si k∈{0,n}."""
    if n <= 0:
        return None
    p = k / n
    z = _z(confiance)
    demi = z * math.sqrt(p * (1 - p) / n)
    return (max(0.0, p - demi), min(1.0, p + demi))


def wilson(k: int, n: int, confiance: float = 0.95):
    """Intervalle de WILSON (score). Calibré même à n petit / p extrême ; toujours dans [0,1]."""
    if n <= 0:
        return None
    p = k / n
    z = _z(confiance)
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    demi = (z / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return (max(0.0, centre - demi), min(1.0, centre + demi))


def agresti_coull(k: int, n: int, confiance: float = 0.95):
    """AGRESTI-COULL : Wald sur (k+z²/2) succès et (n+z²) essais. Simple, bien calibré."""
    if n <= 0:
        return None
    z = _z(confiance)
    z2 = z * z
    ntilde = n + z2
    ptilde = (k + z2 / 2) / ntilde
    demi = z * math.sqrt(ptilde * (1 - ptilde) / ntilde)
    return (max(0.0, ptilde - demi), min(1.0, ptilde + demi))


def intervalle(k: int, n: int, confiance: float = 0.95, methode: str = "wilson"):
    """Façade : (ESTIMATION, (lo, hi), confiance) ou (ABSTENTION, None, raison). Défaut = Wilson (calibré)."""
    if n <= 0:
        return (ABSTENTION, None, "aucun essai (n=0)")
    if not (0 <= k <= n):
        return (ABSTENTION, None, f"k={k} hors [0,{n}]")
    fn = {"wald": wald, "wilson": wilson, "agresti_coull": agresti_coull}.get(methode)
    if fn is None:
        return (ABSTENTION, None, f"méthode inconnue : {methode}")
    return (ESTIMATION, fn(k, n, confiance), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer la proportion : {res[2]}."
    lo, hi = res[1]
    return (f"Proportion estimée dans [{lo:.3f}, {hi:.3f}] à {round(res[2]*100)}% (intervalle de Wilson, calibré même "
            f"à petit effectif — l'intervalle de Wald serait sur-confiant et pourrait dégénérer en certitude factice).")


if __name__ == "__main__":
    print("=== INTERVALLE DE PROPORTION BINOMIALE — Wald (sur-confiant) vs Wilson ===\n")
    for k, n in [(0, 10), (1, 20), (3, 12), (50, 100)]:
        w = wald(k, n); wi = wilson(k, n); ac = agresti_coull(k, n)
        print(f"  k={k}/n={n} (p̂={k/n:.2f}) : Wald [{w[0]:.3f},{w[1]:.3f}]  Wilson [{wi[0]:.3f},{wi[1]:.3f}]  "
              f"Agresti-Coull [{ac[0]:.3f},{ac[1]:.3f}]")
    print(f"\n  Cas k=0/n=10 : Wald = [0,0] (FAUSSE certitude) ; Wilson = [0, {wilson(0,10)[1]:.3f}] (honnête).")
    print(" ", formule(intervalle(2, 30)))
