"""
PALIER 2 — BORNES DE CONCENTRATION (Hoeffding, empirical-Bernstein) : un intervalle de confiance GARANTI à n fini,
sans hypothèse de loi (brique 68, 2026-06-27).

Pour estimer la moyenne μ de variables bornées dans [a,b], l'intervalle « gaussien » usuel x̄ ± z·s/√n s'appuie sur le
TCL : il n'est valide qu'ASYMPTOTIQUEMENT. À petit n, ou sur une loi ASYMÉTRIQUE / à événements rares, il SOUS-COUVRE
— il annonce une précision qu'il n'a pas (sur-confiance). Cas extrême : un échantillon tout à zéro donne s=0 et un
intervalle DÉGÉNÉRÉ [x̄, x̄], certitude absurde.

Les inégalités de concentration donnent un intervalle VALIDE à n fini et DISTRIBUTION-FREE :
  • HOEFFDING :  |x̄ − μ| ≤ (b−a)·√( ln(2/δ) / (2n) )            (ne dépend que de l'amplitude, pas des données)
  • EMPIRICAL-BERNSTEIN (Maurer-Pontil) :  |x̄ − μ| ≤ √( 2·V_n·ln(2/δ)/n ) + 7(b−a)·ln(2/δ)/(3(n−1))
    (V_n = variance empirique) → s'ADAPTE à la variance : bien plus serré que Hoeffding quand la variance est faible,
    tout en restant garanti.

LE MODE D'ÉCHEC DÉMASQUÉ : l'intervalle gaussien SOUS-COUVRE (SUR-CONFIANT) à petit n / loi asymétrique ; Hoeffding et
empirical-Bernstein MAINTIENNENT la couverture ≥ 1−δ. Empirical-Bernstein rachète l'excès de prudence de Hoeffding
quand la variance est petite. ABSTENTION si n<2, a≥b, δ∉(0,1), ou données hors [a,b]. Pur Python.
"""
from __future__ import annotations

import math

from proportion_binomiale import _invnorm

ABSTENTION = "abstention"
INTERVALLE = "intervalle"


def _stats(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)   # variance empirique non biaisée
    return n, m, v


def hoeffding(xs, a, b, delta=0.05):
    """Intervalle de Hoeffding (distribution-free, ne dépend que de l'amplitude b−a)."""
    n, m, _ = _stats(xs)
    h = (b - a) * math.sqrt(math.log(2.0 / delta) / (2.0 * n))
    return (max(a, m - h), min(b, m + h))


def empirical_bernstein(xs, a, b, delta=0.05):
    """Intervalle empirical-Bernstein (Maurer-Pontil) : s'adapte à la variance empirique."""
    n, m, v = _stats(xs)
    L = math.log(2.0 / delta)
    h = math.sqrt(2 * v * L / n) + 7 * (b - a) * L / (3 * (n - 1))
    return (max(a, m - h), min(b, m + h))


def gaussien(xs, delta=0.05):
    """Intervalle « gaussien » (TCL) x̄ ± z·s/√n — SUR-CONFIANT à petit n / loi asymétrique."""
    n, m, v = _stats(xs)
    z = _invnorm(1 - delta / 2)
    h = z * math.sqrt(v) / math.sqrt(n)
    return (m - h, m + h)


def intervalle(xs, a, b, delta=0.05, methode="empirical_bernstein"):
    """Façade : (INTERVALLE, (lo, hi), méthode) ou (ABSTENTION, raison). Défaut = empirical-Bernstein (garanti+adaptatif)."""
    if len(xs) < 2 or a >= b or not (0 < delta < 1):
        return (ABSTENTION, None, "n<2 / a≥b / δ∉(0,1)")
    if any(x < a - 1e-12 or x > b + 1e-12 for x in xs):
        return (ABSTENTION, None, "données hors [a,b]")
    fn = {"hoeffding": hoeffding, "empirical_bernstein": empirical_bernstein, "gaussien": gaussien}.get(methode)
    if fn is None:
        return (ABSTENTION, None, f"méthode inconnue : {methode}")
    return (INTERVALLE, (fn(xs, a, b, delta) if methode != "gaussien" else fn(xs, delta)), methode)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'intervalle : {res[2]}."
    (lo, hi), meth = res[1], res[2]
    note = {"hoeffding": "distribution-free, garanti à n fini",
            "empirical_bernstein": "garanti à n fini, adapté à la variance",
            "gaussien": "asymptotique — SUR-confiant à petit n / loi asymétrique"}[meth]
    return f"Moyenne ∈ [{lo:.3f}, {hi:.3f}] à {round((1-0.05)*100)}% ({note})."


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== BORNES DE CONCENTRATION — IC garanti à n fini ===\n")
    # loi à faible variance : EB bien plus serré que Hoeffding
    faible = [0.5 + rng.gauss(0, 0.02) for _ in range(50)]
    faible = [min(1, max(0, x)) for x in faible]
    H = hoeffding(faible, 0, 1); EB = empirical_bernstein(faible, 0, 1)
    print(f"  Faible variance (n=50) : Hoeffding largeur={H[1]-H[0]:.3f} ; emp-Bernstein largeur={EB[1]-EB[0]:.3f} (bien plus serré)")
    # Bernoulli(0.05), petit n : le gaussien sous-couvre
    bern = [1.0 if rng.random() < 0.05 else 0.0 for _ in range(20)]
    print(f"  Bernoulli(0.05) n=20, échantillon somme={int(sum(bern))} : gaussien={tuple(round(v,3) for v in gaussien(bern))}"
          f"  Hoeffding={tuple(round(v,3) for v in hoeffding(bern,0,1))}")
    print(" ", formule(intervalle(faible, 0, 1)))
