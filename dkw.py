"""
PALIER 2 — BANDE DE CONFIANCE DKW (Dvoretzky-Kiefer-Wolfowitz ; constante de Massart) : encadrer TOUTE une loi
inconnue sans hypothèse de forme (brique 65, 2026-06-27).

À partir de n tirages i.i.d., la CDF empirique F_n approche la vraie CDF F. L'inégalité DKW borne l'écart MAXIMAL
(uniforme) entre les deux :
    P( sup_x |F_n(x) − F(x)| > ε ) ≤ 2 e^{−2nε²}        (Massart : constante 2 optimale)
⇒ pour une bande de confiance 1−α :  ε_n = √( ln(2/α) / (2n) ), et avec probabilité ≥ 1−α, SIMULTANÉMENT pour TOUT x :
    F_n(x) − ε_n  ≤  F(x)  ≤  F_n(x) + ε_n.
C'est DISTRIBUTION-FREE (vrai pour n'importe quelle F) et SIMULTANÉ (toute la courbe à la fois).

DEUX MODES D'ÉCHEC DÉMASQUÉS :
  • prendre la CDF empirique F_n POUR la vraie F (probabilité d'un seuil, quantile…) est SUR-CONFIANT : F_n a une
    erreur d'échantillonnage que la bande quantifie.
  • calculer un IC PONCTUEL (Wald) à chaque x et le lire comme une bande : SOUS-COUVRE la courbe entière (multiplicité
    — la vraie F s'échappe QUELQUE PART avec forte probabilité). La bande DKW est SIMULTANÉE → couvre tout.
Vertu : ε_n → 0 quand n→∞. ABSTENTION si échantillon vide ou α∉(0,1). Pur Python.
"""
from __future__ import annotations

import bisect
import math

ABSTENTION = "abstention"
BANDE = "bande"


def epsilon(n, alpha):
    """Demi-largeur DKW-Massart ε_n = √(ln(2/α)/(2n))."""
    return math.sqrt(math.log(2.0 / alpha) / (2.0 * n))


def bande(echantillon, alpha=0.05):
    """Construit la bande DKW. (BANDE, {n, eps, tri}) ou (ABSTENTION, raison)."""
    if not echantillon or not (0 < alpha < 1):
        return (ABSTENTION, "échantillon vide ou α hors (0,1)")
    tri = sorted(echantillon)
    return (BANDE, {"n": len(tri), "eps": epsilon(len(tri), alpha), "tri": tri})


def F_n(b, x):
    """CDF empirique F_n(x) = #{xᵢ ≤ x}/n."""
    return bisect.bisect_right(b["tri"], x) / b["n"]


def F_inf(b, x):
    return max(0.0, F_n(b, x) - b["eps"])


def F_sup(b, x):
    return min(1.0, F_n(b, x) + b["eps"])


def ks_statistique(b, F_vraie):
    """D_n = sup_x |F_n(x) − F(x)| (atteint aux statistiques d'ordre, les deux côtés du saut)."""
    tri, n = b["tri"], b["n"]
    D = 0.0
    for i, x in enumerate(tri):
        Fx = F_vraie(x)
        D = max(D, abs((i + 1) / n - Fx), abs(i / n - Fx))
    return D


def couvre(b, F_vraie):
    """La bande contient-elle la vraie CDF partout ? ⟺ D_n ≤ ε (test exact)."""
    return ks_statistique(b, F_vraie) <= b["eps"] + 1e-15


def intervalle_quantile(b, p):
    """Intervalle de confiance pour le p-quantile, dérivé de la bande. (q_bas, q_haut) ; None à un bord = non borné."""
    tri, n, eps = b["tri"], b["n"], b["eps"]
    def ordre(seuil):
        k = math.ceil(seuil * n)
        if k < 1:
            return None       # non borné à gauche
        if k > n:
            return None       # non borné à droite
        return tri[k - 1]
    return (ordre(p - eps), ordre(p + eps))


def proba_seuil(b, x):
    """Encadrement de F(x)=P(X≤x) : [F_inf(x), F_sup(x)]."""
    return (F_inf(b, x), F_sup(b, x))


def formule(res, x=None) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de bande : {res[1]}."
    b = res[1]
    base = f"Bande DKW à {100*(1-0.05):.0f}% sur {b['n']} tirages (demi-largeur ε={b['eps']:.3f}, distribution-free, simultanée)"
    if x is not None:
        lo, hi = proba_seuil(b, x)
        return base + f" ; P(X ≤ {x}) ∈ [{lo:.3f}, {hi:.3f}] (lire la CDF empirique seule serait sur-confiant)."
    return base + "."


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    ech = [rng.gauss(0, 1) for _ in range(200)]
    st, b = bande(ech, 0.05)
    print("=== BANDE DE CONFIANCE DKW — encadrer toute une loi inconnue ===\n")
    print(f"  n=200, ε={b['eps']:.3f}")
    F = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))   # vraie CDF normale
    print(f"   sup|F_n−F| (KS) = {ks_statistique(b, F):.3f} ≤ ε ? {couvre(b, F)}")
    for x in (-1, 0, 1):
        lo, hi = proba_seuil(b, x)
        print(f"   P(X≤{x:>2}) ∈ [{lo:.3f}, {hi:.3f}]  (vrai {F(x):.3f})")
    print(f"   médiane ∈ {intervalle_quantile(b, 0.5)}")
    for n in (50, 500, 5000):
        print(f"   ε(n={n}) = {epsilon(n, 0.05):.3f}")
