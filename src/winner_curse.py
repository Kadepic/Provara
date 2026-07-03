"""
PALIER 2 — MALÉDICTION DU VAINQUEUR & INFÉRENCE SÉLECTIVE (brique 71, 2026-06-27).

On mesure K effets bruités X_i ~ N(μ_i, σ²) (K traitements, variantes A/B, gènes…) puis on RAPPORTE le MEILLEUR :
ĵ = argmax_i X_i. Problème : l'estimé sélectionné est BIAISÉ VERS LE HAUT (on a choisi celui qui a eu de la chance) —
E[X_ĵ − μ_ĵ] > 0 (malédiction du vainqueur). Un intervalle de confiance NAÏF X_ĵ ± z·σ, calculé comme si on n'avait
pas sélectionné, SOUS-COUVRE le vrai effet μ_ĵ : on annonce un effet plus grand et plus sûr qu'il ne l'est =
SUR-CONFIANCE (cause majeure de la non-reproductibilité).

CORRECTION (inférence SÉLECTIVE) : tenir compte de la sélection. Borne simultanée de BONFERRONI : utiliser le quantile
z_{α/(2K)} (intervalle plus large) garantit que TOUS les μ_i sont couverts simultanément avec probabilité ≥ 1−α — en
particulier μ_ĵ. (Distinct du FDR [[fdr_controle]] = découvertes parmi des tests ; ici = ESTIMATION de l'effet
sélectionné.) Le prix : un intervalle plus prudent. Sans sélection (K=1) le naïf est correct. ABSTENTION si invalide.
Pur Python.
"""
from __future__ import annotations

from proportion_binomiale import _invnorm

ABSTENTION = "abstention"
ESTIME = "estime"


def selectionne(estimes):
    """Indice du plus grand estimé (le « vainqueur »)."""
    return max(range(len(estimes)), key=lambda i: estimes[i])


def ic_naif(x_sel, sigma, alpha=0.05):
    """IC NAÏF (ignore la sélection) : x_sel ± z_{α/2}·σ. SOUS-couvre l'effet sélectionné."""
    z = _invnorm(1 - alpha / 2)
    return (x_sel - z * sigma, x_sel + z * sigma)


def ic_simultane(x_sel, sigma, K, alpha=0.05):
    """IC SIMULTANÉ de Bonferroni : x_sel ± z_{α/(2K)}·σ. Couvre μ_ĵ avec prob ≥ 1−α malgré la sélection."""
    z = _invnorm(1 - alpha / (2 * K))
    return (x_sel - z * sigma, x_sel + z * sigma)


def estime(estimes, sigma, alpha=0.05, methode="simultane"):
    """Façade : (ESTIME, {indice, valeur, ic}) ou (ABSTENTION, raison). Défaut = IC simultané (corrigé pour la sélection)."""
    K = len(estimes)
    if K < 1 or sigma <= 0 or not (0 < alpha < 1):
        return (ABSTENTION, "K<1 / σ≤0 / α∉(0,1)")
    j = selectionne(estimes)
    xs = estimes[j]
    ic = ic_naif(xs, sigma, alpha) if methode == "naif" else ic_simultane(xs, sigma, K, alpha)
    return (ESTIME, {"indice": j, "valeur": xs, "ic": ic, "methode": methode})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'estimation : {res[1]}."
    info = res[1]
    lo, hi = info["ic"]
    note = "corrigé pour la sélection" if info["methode"] == "simultane" else "NAÏF — sous-couvre (sur-confiant)"
    return (f"Effet sélectionné (variante {info['indice']}) = {info['valeur']:.3f}, IC {info['methode']} [{lo:.3f}, "
            f"{hi:.3f}] ({note}). L'estimé brut sur-estime l'effet (malédiction du vainqueur).")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== MALÉDICTION DU VAINQUEUR — inférence sélective ===\n")
    K, sigma = 10, 1.0
    # tous les vrais effets = 0 (nulls) : le max observé est pur bruit chanceux
    biais = 0.0
    naif_couvre = simul_couvre = 0
    N = 20000
    for _ in range(N):
        xs = [rng.gauss(0, sigma) for _ in range(K)]
        j = selectionne(xs)
        biais += xs[j] - 0.0
        ln, hn = ic_naif(xs[j], sigma); ls, hs = ic_simultane(xs[j], sigma, K)
        naif_couvre += (ln <= 0 <= hn); simul_couvre += (ls <= 0 <= hs)
    print(f"  K=10, tous μ=0 : biais moyen de l'estimé sélectionné = {biais/N:.3f} (>0 = malédiction)")
    print(f"   couverture IC NAÏF = {naif_couvre/N:.3f} (≪ 0.95, sur-confiant) ; IC SIMULTANÉ = {simul_couvre/N:.3f} (≥ 0.95)")
    print(" ", formule(estime([0.2, 1.9, 0.5, -0.3], 1.0)))
