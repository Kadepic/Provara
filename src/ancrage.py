"""
PALIER 2 — EFFET D'ANCRAGE QUANTITATIF : une estimation contaminée par une ancre non pertinente est sur-confiante
(brique 125, 2026-06-28).

Présenter un nombre AVANT de demander une estimation biaise systématiquement la réponse vers ce nombre — même si l'ancre
est ALÉATOIRE et SANS RAPPORT (Tversky & Kahneman). Le mécanisme d'« ancrage et ajustement » part de l'ancre et ajuste
INSUFFISAMMENT (facteur α<1) :  estimation = ancre + α·(signal − ancre). L'estimation devient alors CORRÉLÉE à un nombre
dénué de sens (la corrélation devrait être 0) et systématiquement déplacée vers lui.

Traiter une telle estimation comme une mesure fiable est SUR-CONFIANT : elle dépend d'une information NON PERTINENTE et a
une erreur quadratique plus grande qu'un estimateur qui IGNORE l'ancre. La CONTAMINATION est mesurable (régression de
l'estimation sur l'ancre : pente ≠ 0).

LE MODE D'ÉCHEC DÉMASQUÉ : se fier à une estimation ancrée est sur-confiant — la débiaiser, c'est l'AJUSTER PLEINEMENT
(α=1) ou s'appuyer sur un signal indépendant de l'ancre. Distinct de cadrage (108, invariance de description) et de
l'instrument de calibration. ABSTENTION si données insuffisantes. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def estimateur_ancre(signal, ancre, alpha):
    """Ancrage et ajustement : part de l'ancre et ajuste d'un facteur α<1 vers le signal propre."""
    return ancre + alpha * (signal - ancre)


def _moyenne(xs):
    return sum(xs) / len(xs)


def correlation(xs, ys):
    mx, my = _moyenne(xs), _moyenne(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx * dy else 0.0


def simule(theta, alpha, n, rng, sigma_signal=15.0, ancre_min=0.0, ancre_max=200.0):
    """Tire n estimations avec ancre aléatoire NON pertinente. Renvoie (ancres, estimations ancrées, estimations libres)."""
    ancres, anc, libre = [], [], []
    for _ in range(n):
        a = rng.uniform(ancre_min, ancre_max)
        signal = theta + rng.gauss(0, sigma_signal)        # signal propre, indépendant de l'ancre
        ancres.append(a)
        anc.append(estimateur_ancre(signal, a, alpha))
        libre.append(signal)
    return ancres, anc, libre


def analyse(theta=100.0, alpha=0.6, n=5000, rng=None):
    """Façade : contamination de l'estimation par l'ancre. (ANALYSE, {contamination, contamination_libre, mse_ancre,
    mse_libre, ecart_haute_basse}) ou (ABSTENTION)."""
    if rng is None or n < 100:
        return (ABSTENTION, "rng requis / n trop petit")
    ancres, anc, libre = simule(theta, alpha, n, rng)
    cont = correlation(anc, ancres)
    cont_libre = correlation(libre, ancres)
    mse_a = _moyenne([(e - theta) ** 2 for e in anc])
    mse_l = _moyenne([(e - theta) ** 2 for e in libre])
    med = (min(ancres) + max(ancres)) / 2
    hautes = [e for a, e in zip(ancres, anc) if a > med]
    basses = [e for a, e in zip(ancres, anc) if a < med]
    return (ANALYSE, {"contamination": cont, "contamination_libre": cont_libre, "mse_ancre": mse_a,
                      "mse_libre": mse_l, "ecart_haute_basse": _moyenne(hautes) - _moyenne(basses), "theta": theta})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"L'estimation ANCRÉE corrèle à {i['contamination']:.2f} avec une ancre ALÉATOIRE non pertinente (devrait être "
            f"0 ; estimateur libre : {i['contamination_libre']:.2f}). Les ancres hautes tirent l'estimation de "
            f"{i['ecart_haute_basse']:.0f} au-dessus des ancres basses, et l'erreur quadratique passe de {i['mse_libre']:.0f} "
            f"(libre) à {i['mse_ancre']:.0f} (ancrée). Se fier à une estimation ancrée est sur-confiant.")


if __name__ == "__main__":
    import random
    print("=== EFFET D'ANCRAGE QUANTITATIF ===\n")
    st, info = analyse(rng=random.Random(0))
    print(" ", formule((st, info)))
    st2, info2 = analyse(alpha=1.0, rng=random.Random(0))    # ajustement complet
    print(f"\n  α=1 (ajustement complet) : contamination={info2['contamination']:.3f} (l'ancre n'a plus d'effet)")
