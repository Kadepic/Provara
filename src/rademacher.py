"""
PALIER 2 — COMPLEXITÉ DE RADEMACHER & borne de généralisation UNIFORME (Bartlett-Mendelson ; Mohri) (brique 66,
2026-06-27).

Combien une classe d'hypothèses H peut-elle sur-apprendre ? La complexité de RADEMACHER empirique mesure sa capacité
à CORRÉLER avec du bruit pur :
    R̂_n(H) = E_σ[ sup_{h∈H} (1/n) Σ_i σ_i ℓ(h, zᵢ) ]      (σᵢ = ±1 équiprobables, ℓ ∈ [0,1])
Élevée = la classe peut coller à n'importe quel étiquetage aléatoire = elle sur-apprend. Elle donne une borne de
généralisation valable pour TOUT h simultanément, avec probabilité ≥ 1−δ :
    R_vrai(h) ≤ R_emp(h) + 2·R̂_n(H) + 3·√( ln(2/δ) / (2n) ).

LE MODE D'ÉCHEC DÉMASQUÉ : le risque EMPIRIQUE de l'hypothèse SÉLECTIONNÉE sous-estime le risque vrai (l'écart de
convergence uniforme ≈ 2·R̂_n) ; l'annoncer comme performance réelle est SUR-CONFIANT — d'autant plus que H est RICHE
(R̂_n élevé). Cas extrême : une classe NON RESTREINTE (tous les patterns possibles) a R̂_n = 1/2 → borne VIDE (≥1) =
« cette classe ne peut PAS généraliser ». La borne de Rademacher MAJORE le risque vrai à 1−δ. (Distinct de PAC-Bayes
[[pac_bayes]] : capacité de la CLASSE, data-dependent, vs prédicteur randomisé + KL.) ABSTENTION si n=0/δ∉(0,1). Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
BORNE = "borne"


def rademacher_empirique(loss_vectors, rng, n_sigma=400):
    """R̂_n(H) = E_σ[ sup_h (1/n) Σ σ_i ℓ_i(h) ] estimée par Monte-Carlo sur n_sigma tirages de σ.
    `loss_vectors` = liste (sur les hypothèses) de vecteurs de pertes ∈ [0,1] de longueur n."""
    n = len(loss_vectors[0])
    tot = 0.0
    for _ in range(n_sigma):
        sigma = [1 if rng.random() < 0.5 else -1 for _ in range(n)]
        tot += max(sum(s * lv[i] for i, s in enumerate(sigma)) for lv in loss_vectors) / n
    return tot / n_sigma


def borne_massart(n_hyp, n, norme_max=1.0):
    """Majorant analytique de R̂_n pour une classe FINIE (Massart) : ‖ℓ‖₂·√(2 ln|H|)/n ≤ norme_max·√(2 ln|H| / n)."""
    return norme_max * math.sqrt(2 * math.log(max(n_hyp, 1)) / n) if n_hyp > 1 else 0.0


def borne_generalisation(risque_emp, rad, n, delta=0.05):
    """Borne de généralisation uniforme : R_emp + 2·R̂_n + 3·√(ln(2/δ)/(2n)). (Peut dépasser 1 = vide.)"""
    return risque_emp + 2 * rad + 3 * math.sqrt(math.log(2.0 / delta) / (2.0 * n))


def borne(loss_vectors, risques_emp, n, rng, delta=0.05, n_sigma=400):
    """Calcule R̂_n puis la borne pour chaque hypothèse. (BORNE, {rad, bornes:{h:maj}}) ou (ABSTENTION, raison).
    `risques_emp` = liste alignée sur `loss_vectors`."""
    if n <= 0 or not (0 < delta < 1) or not loss_vectors:
        return (ABSTENTION, "n≤0, δ hors (0,1) ou classe vide")
    rad = rademacher_empirique(loss_vectors, rng, n_sigma)
    bornes = [borne_generalisation(re, rad, n, delta) for re in risques_emp]
    return (BORNE, {"rad": rad, "bornes": bornes})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de borne : {res[1]}."
    info = res[1]
    b = min(info["bornes"])
    vide = " (borne VIDE : la classe ne peut pas généraliser)" if b >= 1 else ""
    return (f"Complexité de Rademacher R̂_n={info['rad']:.3f} ; risque vrai ≤ {min(1.0,b):.3f} (uniforme, 95%){vide}. "
            f"Annoncer le seul risque empirique serait sur-confiant — il ignore la capacité de sur-apprentissage.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    n = 40
    print("=== COMPLEXITÉ DE RADEMACHER — capacité de sur-apprentissage ===\n")
    # classe NON restreinte : tous les patterns {0,1}^n -> R̂_n = 1/2 (borne vide)
    import itertools
    petit = 12
    tous = [list(p) for p in itertools.product([0, 1], repeat=petit)]
    print(f"  Classe NON restreinte (2^{petit} patterns) : R̂_n ≈ {rademacher_empirique(tous, rng, 300):.3f} (≈ 0.5 → borne vide)")
    # classe simple : peu d'hypothèses
    for K in (2, 8, 64):
        lv = [[1 if rng.random() < 0.5 else 0 for _ in range(n)] for _ in range(K)]
        rad = rademacher_empirique(lv, rng, 300)
        print(f"  |H|={K:>3} : R̂_n={rad:.3f}  (Massart ≤ {borne_massart(K, n):.3f})  borne gén.(R_emp=0.3)={borne_generalisation(0.3, rad, n):.3f}")
