"""
PALIER 2 — ESTIMATION SOUS BIAIS D'ÉCHANTILLONNAGE (Horvitz-Thompson / Hájek, brique 28, 2026-06-25).

La vraie moyenne d'une population EXISTE, mais si l'échantillon est BIAISÉ (certaines unités sur-représentées), la
moyenne brute est SYSTÉMATIQUEMENT FAUSSE — un biais, pas du bruit (l'augmenter n'aide pas). Quand on connaît la
PROBABILITÉ D'INCLUSION πᵢ de chaque unité (ou des poids wᵢ ∝ 1/πᵢ), on corrige :

  • Horvitz-Thompson : μ̂_HT = (1/N) Σ yᵢ/πᵢ           (sans biais pour le TOTAL/moyenne de population de taille N connue)
  • Hájek (ratio)    : μ̂ = Σ wᵢ yᵢ / Σ wᵢ              (robuste, ne demande pas N ; recommandé par défaut)

INTERVALLE par bootstrap pondéré : on rééchantillonne -> distribution de l'estimateur -> quantiles. INVARIANT
(jugé par calibration.py) : l'estimateur pondéré est ~sans biais et son intervalle COUVRE la vraie moyenne ~confiance,
là où l'estimateur brut SOUS-couvre (biaisé). ABSTENTION si poids dégénérés / échantillon trop petit. Pur Python.
"""
from __future__ import annotations

import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 10


def estime_hajek(valeurs, poids):
    """Estimateur de Hájek : Σ wy / Σ w. Renvoie la moyenne pondérée (corrigée du biais d'inclusion)."""
    v = [float(x) for x in valeurs]
    w = [float(x) for x in poids]
    sw = sum(w)
    if sw <= 0:
        raise ValueError("somme des poids nulle")
    return sum(w[i] * v[i] for i in range(len(v))) / sw


def estime_ht(valeurs, proba_inclusion, N):
    """Horvitz-Thompson de la MOYENNE de population : (1/N) Σ yᵢ/πᵢ. `N` = taille de la population."""
    v = [float(x) for x in valeurs]
    pi = [float(x) for x in proba_inclusion]
    return sum(v[i] / pi[i] for i in range(len(v))) / N


def n_effectif(poids):
    """Taille d'échantillon EFFECTIVE de Kish : (Σw)² / Σw². Petite vs n -> poids très déséquilibrés (estimation fragile)."""
    w = [float(x) for x in poids]
    s2 = sum(x * x for x in w)
    return (sum(w) ** 2) / s2 if s2 > 0 else 0.0


def intervalle_hajek(valeurs, poids, confiance=0.90, n_boot=2000, seed=0):
    """Intervalle de confiance de la moyenne pondérée (Hájek) par BOOTSTRAP pondéré. Renvoie
    (ESTIMATION, (point, (bas, haut)), confiance) ou ABSTENTION (échantillon trop petit / poids dégénérés)."""
    v = [float(x) for x in valeurs]
    w = [float(x) for x in poids]
    n = len(v)
    if n < N_MIN:
        return (ABSTENTION, None, f"échantillon trop petit (n={n} < {N_MIN})")
    if sum(w) <= 0 or n_effectif(w) < 5:
        return (ABSTENTION, None, "poids dégénérés (taille effective < 5) : estimation non fiable")
    point = estime_hajek(v, w)
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        sw = sum(w[i] for i in idx)
        boot.append(sum(w[i] * v[i] for i in idx) / sw if sw > 0 else point)
    boot.sort()
    a = (1.0 - confiance) / 2.0
    bas = boot[int(a * n_boot)]
    haut = boot[min(n_boot - 1, int((1.0 - a) * n_boot))]
    return (ESTIMATION, (point, (bas, haut)), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je préfère ne pas estimer : {res[2]}."
    point, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"En corrigeant le biais d'échantillonnage, j'estime la moyenne de population à ~{point:.2f} "
            f"(à {round(conf*100)}% : entre {bas:.2f} et {haut:.2f}).")


if __name__ == "__main__":
    print("=== ESTIMATION SOUS BIAIS D'ÉCHANTILLONNAGE ===\n")
    import random as _r
    rng = _r.Random(0)
    # population : 50% valeur ~10, 50% valeur ~20 -> vraie moyenne 15. Mais on sur-échantillonne les "20".
    ech, poids = [], []
    for _ in range(200):
        if rng.random() < 0.75:            # 75% de l'échantillon = groupe "20" (sur-représenté)
            ech.append(rng.gauss(20, 2)); poids.append(1 / 0.75)
        else:
            ech.append(rng.gauss(10, 2)); poids.append(1 / 0.25)
    brut = sum(ech) / len(ech)
    print(f"  moyenne BRUTE (biaisée) = {brut:.2f} (vraie ≈ 15)")
    print(" ", formule(intervalle_hajek(ech, poids, 0.90)))
