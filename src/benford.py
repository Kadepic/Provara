"""
PALIER 2 — LOI DE BENFORD : détecter des données anormales/fabriquées par la distribution du PREMIER CHIFFRE (brique
88, 2026-06-27).

Dans beaucoup de jeux de données « naturels » (montants comptables, populations, constantes physiques), le premier
chiffre significatif d suit
    P(d) = log₁₀(1 + 1/d)   →   « 1 » ≈ 30,1 %, « 9 » ≈ 4,6 % (décroissant),
parce que la distribution est invariante d'échelle (mantisse uniforme en log). Les nombres INVENTÉS par des humains
sont au contraire trop uniformes → ils VIOLENT Benford : d'où un test d'anomalie / de fraude (χ² vs Benford).

DOUBLE MODE D'ÉCHEC DÉMASQUÉ :
  • supposer qu'un jeu de chiffres « a l'air normal » est SUR-CONFIANT — le test de Benford révèle des manipulations
    invisibles à l'œil.
  • MAIS conclure « fraude » dès qu'on s'écarte de Benford est l'AUTRE sur-confiance : beaucoup de données LÉGITIMES
    ne suivent PAS Benford (plages bornées, numéros attribués, faible étendue). Le test signale une ANOMALIE à
    investiguer, pas une preuve. On rapporte donc un p-value calibré, avec la réserve d'applicabilité.
ABSTENTION si trop peu de données / valeurs non positives. Pur Python (χ² à 8 ddl, forme close).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
TEST = "test"


def proba_benford(d):
    """P(premier chiffre = d) = log₁₀(1 + 1/d), d ∈ {1..9}."""
    return math.log10(1 + 1 / d)


def premier_chiffre(x):
    """Premier chiffre significatif de |x| (≠ 0)."""
    x = abs(x)
    if x == 0:
        return None
    while x < 1:
        x *= 10
    while x >= 10:
        x /= 10
    return int(x)


def distribution(donnees):
    """Comptes observés des premiers chiffres 1..9."""
    cnt = {d: 0 for d in range(1, 10)}
    for x in donnees:
        d = premier_chiffre(x)
        if d:
            cnt[d] += 1
    return cnt


def _chi2_sf_df8(x):
    """P(χ² > x) à 8 ddl (forme close : Q(4, x/2) = e^{-y}(1+y+y²/2+y³/6), y=x/2)."""
    y = x / 2
    return math.exp(-y) * (1 + y + y * y / 2 + y ** 3 / 6)


def test_benford(donnees):
    """Statistique χ² et p-value vs Benford. (statistique, p_value, conforme_bool)."""
    cnt = distribution(donnees)
    n = sum(cnt.values())
    chi2 = sum((cnt[d] - n * proba_benford(d)) ** 2 / (n * proba_benford(d)) for d in range(1, 10))
    p = _chi2_sf_df8(chi2)
    return chi2, p, p > 0.05


def analyse(donnees, alpha=0.05):
    """Façade : (TEST, {chi2, p_value, conforme, distribution}) ou (ABSTENTION, raison)."""
    valides = [x for x in donnees if premier_chiffre(x) is not None]
    if len(valides) < 30:
        return (ABSTENTION, "trop peu de données (< 30) pour un test de Benford fiable")
    chi2, p, conf = test_benford(valides)
    return (TEST, {"chi2": chi2, "p_value": p, "conforme": conf, "n": len(valides)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de test : {res[1]}."
    i = res[1]
    if i["conforme"]:
        return f"Premiers chiffres conformes à Benford (χ²={i['chi2']:.1f}, p={i['p_value']:.3f}) : pas d'anomalie détectée."
    return (f"⚠ ÉCART à Benford (χ²={i['chi2']:.1f}, p={i['p_value']:.4f}) : ANOMALIE à investiguer — PAS une preuve de "
            f"fraude (certaines données légitimes ne suivent pas Benford). Affirmer la fraude serait sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== LOI DE BENFORD ===\n")
    print(f"  P(1)={proba_benford(1):.3f}, P(9)={proba_benford(9):.3f}, somme={sum(proba_benford(d) for d in range(1,10)):.3f}")
    naturel = [10 ** rng.uniform(0, 6) for _ in range(1000)]            # invariant d'échelle → Benford
    fabrique = [rng.randint(1, 9) * 10 ** rng.randint(0, 5) for _ in range(1000)]  # premiers chiffres uniformes
    print(" ", formule(analyse(naturel)))
    print(" ", formule(analyse(fabrique)))
