"""
PALIER 2 — RÉGRESSION FALLACIEUSE (Granger-Newbold 1974) : régresser deux séries NON-STATIONNAIRES est sur-confiant
(brique 121, 2026-06-28).

Régresser une série temporelle Y sur une autre X et lire le t de la pente / le R² comme une preuve de relation est
SUR-CONFIANT quand les séries sont NON-STATIONNAIRES (marches aléatoires, séries à tendance). Deux marches aléatoires
TOTALEMENT INDÉPENDANTES produisent, en régression de NIVEAUX, un t « significatif » (|t|>1.96) dans ~75 % des cas — pas
5 % — et un R² souvent élevé. La cause : les résidus sont eux-mêmes une marche aléatoire (autocorrélés, variance non
bornée), ce qui INVALIDE l'inférence OLS (qui suppose des erreurs i.i.d.). On « découvre » des relations qui n'existent
pas.

LA CORRECTION : travailler sur les DIFFÉRENCES (ΔY sur ΔX) — qui sont stationnaires si les niveaux sont I(1) — rétablit
un taux de faux positif de ~5 %. (Ou tester la COINTÉGRATION avant de régresser les niveaux.)

LE MODE D'ÉCHEC DÉMASQUÉ : trouver un t significatif / un R² élevé entre deux séries tendancielles et en conclure une
relation est sur-confiant. Pour des séries STATIONNAIRES (bruit blanc), l'inférence OLS reste valide (honnêteté).
Distinct des régressions i.i.d. (ridge=89, biais=86). ABSTENTION si séries trop courtes. Pur Python, rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def marche_aleatoire(n, rng):
    x = 0.0
    out = []
    for _ in range(n):
        x += rng.gauss(0, 1)
        out.append(x)
    return out


def bruit_blanc(n, rng):
    return [rng.gauss(0, 1) for _ in range(n)]


def _diff(s):
    return [s[i] - s[i - 1] for i in range(1, len(s))]


def t_et_r2(xs, ys):
    """|t| de la pente OLS et R² de la régression de ys sur xs."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0, 0.0
    b = sxy / sxx
    a = my - b * mx
    resid = [ys[i] - (a + b * xs[i]) for i in range(n)]
    rss = sum(e * e for e in resid)
    s2 = rss / (n - 2)
    se = math.sqrt(s2 / sxx) if s2 > 0 else 1e-12
    return abs(b / se), 1 - rss / syy


def taux_faux_positif(generateur, n, T, rng, differencier=False, seuil=1.96):
    """Fraction de régressions de deux séries INDÉPENDANTES jugées « significatives » (|t|>seuil)."""
    sig = 0
    r2s = []
    for _ in range(T):
        X = generateur(n, rng)
        Y = generateur(n, rng)
        if differencier:
            X, Y = _diff(X), _diff(Y)
        t, r2 = t_et_r2(X, Y)
        sig += t > seuil
        r2s.append(r2)
    return sig / T, sum(r2s) / T


def analyse(n=100, T=2000, rng=None):
    """Façade : taux de faux positif pour marches aléatoires (niveaux vs différences) et bruit blanc.
    (ANALYSE, {...}) ou (ABSTENTION)."""
    if rng is None or n < 20:
        return (ABSTENTION, "rng requis / série trop courte")
    fp_niveaux, r2_niveaux = taux_faux_positif(marche_aleatoire, n, T, rng)
    fp_diff, _ = taux_faux_positif(marche_aleatoire, n, T, rng, differencier=True)
    fp_blanc, _ = taux_faux_positif(bruit_blanc, n, T, rng)
    return (ANALYSE, {"fp_niveaux": fp_niveaux, "r2_niveaux": r2_niveaux, "fp_differences": fp_diff,
                      "fp_bruit_blanc": fp_blanc})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Deux marches aléatoires INDÉPENDANTES : régression de NIVEAUX → {100*i['fp_niveaux']:.0f} % de « significatif » "
            f"(au lieu de 5 %), R² moyen {i['r2_niveaux']:.2f}. En DIFFÉRENCES : {100*i['fp_differences']:.0f} % (correct). "
            f"Bruit blanc stationnaire : {100*i['fp_bruit_blanc']:.0f} %. Conclure à une relation depuis le t/R² de séries "
            f"non-stationnaires est sur-confiant.")


if __name__ == "__main__":
    import random
    print("=== RÉGRESSION FALLACIEUSE (Granger-Newbold) ===\n")
    print(" ", formule(analyse(rng=random.Random(0))))
