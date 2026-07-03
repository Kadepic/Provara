"""
PALIER 2 — LOI DES GRANDS NOMBRES MAL COMPRISE : « à la longue ça s'équilibre, je récupérerai mes pertes » est
sur-confiant (brique 132, 2026-06-28).

La loi des grands nombres dit que la MOYENNE des résultats d'un jeu équitable converge vers 0. Beaucoup en déduisent que
« les écarts se compensent » et qu'on finit par revenir à l'équilibre. C'est SUR-CONFIANT : c'est la MOYENNE qui converge,
pas la SOMME. Pour une marche aléatoire équitable (±1) :
    moyenne par pari  S_n/n  →  0   (LGN, vraie),
    MAIS  E|S_n| = √(2n/π)  →  ∞   (l'écart cumulé GRANDIT comme √n).
La richesse cumulée d'un joueur DIVERGE — elle ne revient PAS à 0. Pire, la LOI DE L'ARCSINUS : la fraction du temps passé
du côté gagnant n'est PAS concentrée autour de ½ ; elle est en U (le plus probable est de passer PRESQUE TOUT le temps d'un
seul côté). Un joueur perdant le reste souvent longtemps.

LE MODE D'ÉCHEC DÉMASQUÉ : croire que « ça s'équilibre / je vais me refaire » est sur-confiant — la MOYENNE s'équilibre,
la SOMME diverge. La LGN reste vraie pour la moyenne (honnêteté) ; l'erreur est de confondre moyenne et somme. Distinct du
sophisme du joueur (107, renversement du prochain tirage) et d'ergodicité (93, processus multiplicatif). rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def marche(n, rng):
    """Marche aléatoire équitable ±1. Renvoie (S_n, fraction de temps où S>0)."""
    S = 0
    pos = 0
    for _ in range(n):
        S += 1 if rng.random() < 0.5 else -1
        if S > 0:
            pos += 1
    return S, pos / n


def esperance_moyenne(n, T, rng):
    return sum(marche(n, rng)[0] / n for _ in range(T)) / T


def esperance_abs_somme(n, T, rng):
    return sum(abs(marche(n, rng)[0]) for _ in range(T)) / T


def distribution_temps_en_tete(n, T, rng):
    """Renvoie (fraction de parties passant <10% ou >90% du temps en tête, fraction proche de 50%)."""
    extreme = milieu = 0
    for _ in range(T):
        f = marche(n, rng)[1]
        if f < 0.1 or f > 0.9:
            extreme += 1
        if 0.4 < f < 0.6:
            milieu += 1
    return extreme / T, milieu / T


def analyse(n=10000, T=3000, rng=None):
    """Façade (une seule passe de T marches). (ANALYSE, {moyenne, abs_somme, abs_theorique, frac_extreme, frac_milieu})
    ou (ABSTENTION)."""
    if rng is None or n < 100:
        return (ABSTENTION, "rng requis / n trop petit")
    s_moy = s_abs = ext = mil = 0.0
    for _ in range(T):
        S, f = marche(n, rng)
        s_moy += S / n
        s_abs += abs(S)
        if f < 0.1 or f > 0.9:
            ext += 1
        if 0.4 < f < 0.6:
            mil += 1
    return (ANALYSE, {"n": n, "moyenne": s_moy / T, "abs_somme": s_abs / T, "abs_theorique": math.sqrt(2 * n / math.pi),
                      "frac_extreme": ext / T, "frac_milieu": mil / T})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Sur n={i['n']} paris équitables : la MOYENNE par pari = {i['moyenne']:+.4f} (→0, la LGN tient). MAIS l'écart "
            f"cumulé |S_n| = {i['abs_somme']:.0f} (≈√(2n/π)={i['abs_theorique']:.0f}) — il GRANDIT. Le temps passé en tête "
            f"est en U (extrêmes {i['frac_extreme']:.2f} vs milieu {i['frac_milieu']:.2f}, arcsinus). « Ça va s'équilibrer, "
            f"je vais me refaire » est sur-confiant — la moyenne s'équilibre, pas la somme.")


if __name__ == "__main__":
    import random
    print("=== LOI DES GRANDS NOMBRES MAL COMPRISE ===\n")
    print(" ", formule(analyse(rng=random.Random(0))))
