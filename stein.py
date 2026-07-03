"""
PALIER 2 — PARADOXE DE STEIN (estimateur de James-Stein) : l'estimateur « évident » (le MLE) est sur-confiant à d≥3
(brique 114, 2026-06-28).

Pour estimer simultanément d moyennes à partir d'une observation bruitée X ~ N(θ, σ²I), le réflexe est de prendre
CHAQUE observation comme son estimation : θ̂ = X (maximum de vraisemblance). Charles Stein (1956) a montré que c'est
SUR-CONFIANT : pour d ≥ 3, le MLE est INADMISSIBLE — il est strictement DOMINÉ en risque quadratique TOTAL par
l'estimateur à rétrécissement de James-Stein
    θ̂_JS = (1 − (d−2)σ² / ‖X‖²)₊ · X,
et ce pour TOUT θ, même pour des quantités totalement SANS RAPPORT (le prix du thé, votre poids, la masse d'une étoile).
Tirer l'estimation vers un point commun réduit l'erreur totale parce que le bruit des d coordonnées se « mutualise ».

Le seuil est réel : à d = 1 ou 2, le MLE est ADMISSIBLE (rien ne le domine). Le gain est maximal près de la cible de
rétrécissement et s'amenuise quand ‖θ‖ grandit, mais la domination est UNIFORME (jamais pire). Subtilité : JS peut
empirer CERTAINES coordonnées, mais le TOTAL est toujours meilleur.

LE MODE D'ÉCHEC DÉMASQUÉ : « chaque mesure est sa meilleure estimation » est sur-confiant à d≥3 ; le rétrécissement
mutualisé domine. Distinct de petits_nombres (94, EB de TAUX) et ridge (89, régression). ABSTENTION si d<3. rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def james_stein(X, sigma2=1.0):
    """Estimateur de James-Stein (positive-part), rétrécissement vers 0. Pour d<3, renvoie X (MLE, admissible)."""
    d = len(X)
    if d < 3:
        return list(X)
    norme2 = sum(x * x for x in X)
    if norme2 == 0:
        return list(X)
    facteur = max(0.0, 1.0 - (d - 2) * sigma2 / norme2)
    return [facteur * x for x in X]


def _risque(theta, estimateur, sigma2, T, rng):
    """Risque quadratique total moyen E‖θ̂ − θ‖² par simulation."""
    s = 0.0
    sig = sigma2 ** 0.5
    for _ in range(T):
        X = [t + rng.gauss(0, sig) for t in theta]
        est = estimateur(X, sigma2)
        s += sum((a - t) ** 2 for a, t in zip(est, theta))
    return s / T


def risque_mle(theta, sigma2, T, rng):
    return _risque(theta, lambda X, s2: list(X), sigma2, T, rng)


def risque_js(theta, sigma2, T, rng):
    return _risque(theta, james_stein, sigma2, T, rng)


def risques_apparies(theta, sigma2, T, rng):
    """Risques MLE et JS sur les MÊMES tirages X (comparaison appariée, faible variance). Renvoie aussi les risques
    PAR COORDONNÉE (pour montrer que JS peut empirer certaines coordonnées tout en gagnant au total)."""
    d = len(theta)
    sig = sigma2 ** 0.5
    s_mle = s_js = 0.0
    coord_mle = [0.0] * d
    coord_js = [0.0] * d
    for _ in range(T):
        X = [t + rng.gauss(0, sig) for t in theta]
        est = james_stein(X, sigma2)
        for k in range(d):
            em = (X[k] - theta[k]) ** 2
            ej = (est[k] - theta[k]) ** 2
            s_mle += em
            s_js += ej
            coord_mle[k] += em
            coord_js[k] += ej
    return (s_mle / T, s_js / T, [c / T for c in coord_mle], [c / T for c in coord_js])


def analyse(theta, sigma2=1.0, T=20000, rng=None):
    """Façade : compare le risque total MLE vs James-Stein (tirages appariés). (ANALYSE, {...}) ou (ABSTENTION)."""
    if rng is None:
        return (ABSTENTION, "rng requis")
    d = len(theta)
    if d < 3:
        return (ABSTENTION, "domination de James-Stein garantie seulement pour d ≥ 3 (MLE admissible à d<3)")
    rm, rj, cm, cj = risques_apparies(theta, sigma2, T, rng)
    return (ANALYSE, {"d": d, "risque_mle": rm, "risque_js": rj, "domine": rj < rm,
                      "gain_relatif": (rm - rj) / rm if rm else 0.0,
                      "coord_mle": cm, "coord_js": cj})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"d={i['d']} moyennes : risque total MLE={i['risque_mle']:.2f} (=d) vs James-Stein={i['risque_js']:.2f} "
            f"({'DOMINE' if i['domine'] else 'ne domine pas'}, gain {100*i['gain_relatif']:.0f} %). Prendre chaque mesure "
            f"comme sa meilleure estimation est sur-confiant à d≥3 — le rétrécissement mutualisé fait mieux pour TOUT θ.")


if __name__ == "__main__":
    import random
    print("=== PARADOXE DE STEIN (James-Stein) ===\n")
    for theta in ([(-2, 0, 2)], [tuple((i % 5) - 2 for i in range(10))], [tuple([50, -30, 12, 0, 7, -8, 21, 3, -15, 40])]):
        th = theta[0]
        st, info = analyse(list(th), rng=random.Random(0))
        print(f"  d={info['d']:2d}, θ={'varié' if len(th) > 3 else th}: MLE={info['risque_mle']:.2f} JS={info['risque_js']:.2f} (gain {100*info['gain_relatif']:.0f} %)")
    print("\n ", formule(analyse([-2.0, 0.0, 2.0], rng=random.Random(0))))
