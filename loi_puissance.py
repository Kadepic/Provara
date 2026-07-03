"""
PALIER 2 — LOIS À QUEUE LOURDE (loi de puissance / Pareto) : la moyenne et l'IC du TCL trompent quand la variance est
infinie (brique 90, 2026-06-27).

Beaucoup de phénomènes (richesses, tailles de villes, krachs, fichiers, pannes) suivent une loi de PUISSANCE :
P(X > x) ∝ x^{−α}. L'indice de queue α décide de TOUT :
  • α > 2 : variance finie → le TCL s'applique, l'IC x̄ ± z·s/√n est valide.
  • 1 < α ≤ 2 : moyenne FINIE mais variance INFINIE → la moyenne d'échantillon a une variance infinie : elle ne se
    concentre pas, et l'IC du TCL SOUS-COUVRE (sur-confiance) — `s/√n` sous-estime massivement l'incertitude réelle.
  • α ≤ 1 : moyenne INFINIE → la moyenne d'échantillon CROÎT avec n, elle ne converge JAMAIS (cf. St-Pétersbourg).

L'indice α s'estime SANS supposer α par l'estimateur de HILL sur les k plus grandes valeurs.

LE MODE D'ÉCHEC DÉMASQUÉ : calculer une moyenne, un écart-type et un IC gaussien sur des données à queue lourde est
SUR-CONFIANT ; il faut DÉTECTER α (Hill) et, si α ≤ 2, refuser l'IC du TCL / avertir (variance ou moyenne non
définie). ABSTENTION si données insuffisantes / non positives. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def pareto(rng, xmin, alpha):
    """Tire X ~ Pareto(xmin, α) : P(X>x)=(xmin/x)^α. X = xmin·U^{−1/α}."""
    u = 1 - rng.random()           # ∈ (0,1]
    return xmin * u ** (-1 / alpha)


def hill(donnees, k=None):
    """Estimateur de Hill de l'indice de queue α, sur les k plus grandes valeurs. α̂ = k / Σ ln(X_(i)/X_(k+1))."""
    xs = sorted((x for x in donnees if x > 0), reverse=True)
    n = len(xs)
    if k is None:
        k = max(2, int(n ** 0.5))      # règle pratique k ≈ √n
    k = min(k, n - 1)
    seuil = xs[k]
    s = sum(math.log(xs[i] / seuil) for i in range(k))
    return k / s if s > 0 else float("inf")


def moyenne(xs):
    return sum(xs) / len(xs)


def ic_tcl(xs, z=1.96):
    """IC gaussien (TCL) de la moyenne : x̄ ± z·s/√n. SOUS-COUVRE si α ≤ 2 (variance infinie)."""
    n = len(xs); m = moyenne(xs)
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    h = z * math.sqrt(v) / math.sqrt(n)
    return (m - h, m + h)


def moyenne_theorique(xmin, alpha):
    """E[X] = α·xmin/(α−1) si α>1, sinon ∞."""
    return alpha * xmin / (alpha - 1) if alpha > 1 else float("inf")


def analyse(donnees, k=None):
    """Façade : estime α (Hill) et juge la validité de l'IC du TCL. (ANALYSE, {alpha, variance_finie, moyenne_finie,
    ic_tcl, fiable_tcl}) ou (ABSTENTION, raison)."""
    valides = [x for x in donnees if x > 0]
    if len(valides) < 30:
        return (ABSTENTION, "trop peu de données positives (< 30)")
    a = hill(valides, k)
    return (ANALYSE, {"alpha": a, "variance_finie": a > 2, "moyenne_finie": a > 1,
                      "ic_tcl": ic_tcl(valides), "fiable_tcl": a > 2})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if i["fiable_tcl"]:
        return f"Indice de queue α≈{i['alpha']:.2f} > 2 : variance finie, IC du TCL valide {tuple(round(v,2) for v in i['ic_tcl'])}."
    if not i["moyenne_finie"]:
        return f"⚠ α≈{i['alpha']:.2f} ≤ 1 : moyenne INFINIE — l'échantillon ne converge pas. Rapporter une moyenne serait sur-confiant."
    return (f"⚠ α≈{i['alpha']:.2f} ∈ (1,2] : variance INFINIE — l'IC du TCL {tuple(round(v,2) for v in i['ic_tcl'])} "
            f"SOUS-COUVRE (sur-confiance). Utiliser des statistiques robustes / médiane.")


if __name__ == "__main__":
    import random, statistics
    rng = random.Random(0)
    print("=== LOIS À QUEUE LOURDE (Pareto) ===\n")
    for alpha in (3.0, 1.5, 0.8):
        ech = [pareto(rng, 1.0, alpha) for _ in range(3000)]
        print(f"  α={alpha} : Hill α̂={hill(ech):.2f} ; moyenne emp={moyenne(ech):8.1f} "
              f"(théo {moyenne_theorique(1,alpha) if alpha>1 else float('inf')})")
    # instabilité de la moyenne pour α<1 : croît avec n
    for n in (100, 10000):
        m = statistics.mean(moyenne([pareto(rng, 1, 0.8) for _ in range(n)]) for _ in range(50))
        print(f"  α=0.8 : moyenne d'échantillon (n={n:>5}) ≈ {m:.1f} (croît avec n → ne converge pas)")
    print(" ", formule(analyse([pareto(rng, 1.0, 1.5) for _ in range(2000)])))
