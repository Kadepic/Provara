"""
PALIER 2 — DÉCOMPOSITION ÉPISTÉMIQUE / ALÉATOIRE (brique 38, 2026-06-25).

Toute incertitude n'est pas égale. L'honnêteté demande de distinguer DEUX sources :
  • ALÉATOIRE (irréductible) : la variabilité INHÉRENTE du phénomène (bruit, hasard). Aucune donnée supplémentaire ne
    la réduit — c'est un PLANCHER.
  • ÉPISTÉMIQUE (réductible) : notre ignorance due au MANQUE de données. Elle DÉCROÎT quand on observe plus (∝ 1/n).
    « Je ne sais pas encore » ≠ « c'est intrinsèquement imprévisible ».

Loi de la variance totale : Var(Y) = E[Var(Y|θ)] (aléatoire) + Var(E[Y|θ]) (épistémique).

Deux cas fournis :
  • ÉCHANTILLON : aléatoire = variance empirique σ̂² ; épistémique = σ̂²/n (incertitude sur la moyenne) ;
    incertitude prédictive (nouvelle obs) = σ̂²(1+1/n).
  • ENSEMBLE (plusieurs modèles) : épistémique = variance des prédictions entre membres (désaccord) ;
    aléatoire = moyenne des variances prédites par chaque membre.

INVARIANT (jugé par calibration.py) : l'épistémique → 0 quand n → ∞ (l'aléatoire reste) ; l'intervalle prédictif
(aléatoire+épistémique) couvre une nouvelle observation ~confiance. ABSTENTION si échantillon trop petit. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 5
_Z = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}


def decompose_echantillon(echantillon):
    """Décompose l'incertitude d'estimation à partir d'un échantillon. Renvoie (ESTIMATION, infos) avec
    infos = {moyenne, aleatoire (var), epistemique (var), total_predictif (var), n} ou ABSTENTION."""
    x = [float(v) for v in echantillon]
    n = len(x)
    if n < N_MIN:
        return (ABSTENTION, {"raison": f"échantillon trop petit (n={n} < {N_MIN})"})
    mu = sum(x) / n
    aleatoire = sum((v - mu) ** 2 for v in x) / (n - 1)        # variance inhérente (irréductible)
    epistemique = aleatoire / n                                 # incertitude sur la moyenne (réductible ∝ 1/n)
    return (ESTIMATION, {"moyenne": mu, "aleatoire": aleatoire, "epistemique": epistemique,
                         "total_predictif": aleatoire + epistemique, "n": n})


def decompose_ensemble(predictions_membres, variances_membres=None):
    """Décompose pour un ENSEMBLE de modèles. `predictions_membres` = liste des prédictions ponctuelles des membres ;
    `variances_membres` = variance prédite par chaque membre (ou None = membres déterministes -> aléatoire 0).
    Renvoie (ESTIMATION, {prediction, epistemique, aleatoire, total}) ou ABSTENTION."""
    p = [float(v) for v in predictions_membres]
    m = len(p)
    if m < 2:
        return (ABSTENTION, {"raison": "moins de 2 membres d'ensemble"})
    moy = sum(p) / m
    epistemique = sum((v - moy) ** 2 for v in p) / m           # désaccord entre membres
    if variances_membres is None:
        aleatoire = 0.0
    else:
        vm = [float(v) for v in variances_membres]
        aleatoire = sum(vm) / len(vm)                          # bruit moyen prédit par les membres
    return (ESTIMATION, {"prediction": moy, "epistemique": epistemique, "aleatoire": aleatoire,
                         "total": epistemique + aleatoire})


def intervalle_predictif(echantillon, confiance=0.90):
    """Intervalle de PRÉDICTION pour une nouvelle observation (aléatoire + épistémique). (ESTIMATION, (point,
    (bas, haut)), confiance) ou ABSTENTION."""
    st, infos = decompose_echantillon(echantillon)
    if st == ABSTENTION:
        return (ABSTENTION, None, infos["raison"])
    z = _Z.get(round(confiance, 2), 1.6449)
    demi = z * math.sqrt(infos["total_predictif"])
    mu = infos["moyenne"]
    return (ESTIMATION, (mu, (mu - demi, mu + demi)), confiance)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas décomposer l'incertitude : {res[1].get('raison')}."
    i = res[1]
    if "total_predictif" in i:
        al, ep = math.sqrt(i["aleatoire"]), math.sqrt(i["epistemique"])
        part = ep / (al + ep) if (al + ep) > 0 else 0.0
        red = "RÉDUCTIBLE en grande partie (plus de données aiderait)" if part > 0.3 else \
              "surtout IRRÉDUCTIBLE (le phénomène est intrinsèquement variable — plus de données n'aiderait guère)"
        return (f"Incertitude : aléatoire (irréductible) σ≈{al:.3f} ; épistémique (réductible) σ≈{ep:.3f}. "
                f"Elle est {red}.")
    return f"Ensemble : épistémique (désaccord) {i['epistemique']:.3f} ; aléatoire (bruit) {i['aleatoire']:.3f}."


if __name__ == "__main__":
    print("=== DÉCOMPOSITION ÉPISTÉMIQUE / ALÉATOIRE ===\n")
    import random
    rng = random.Random(0)
    petit = [rng.gauss(0, 2) for _ in range(8)]
    grand = [rng.gauss(0, 2) for _ in range(2000)]
    print("  n=8    :", formule(decompose_echantillon(petit)))
    print("  n=2000 :", formule(decompose_echantillon(grand)))
