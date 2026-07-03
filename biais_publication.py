"""
PALIER 2 — BIAIS DE PUBLICATION (file-drawer) : se fier à l'effet moyen de la littérature PUBLIÉE est sur-confiant
(brique 126, 2026-06-28).

Les revues publient surtout les résultats SIGNIFICATIFS ; les études « nulles » restent dans le tiroir (file-drawer). La
littérature publiée est donc un échantillon SÉLECTIONNÉ : la méta-analyse de ce qui est publié SUR-ESTIME l'effet réel.
Le signe caractéristique est l'ASYMÉTRIE EN ENTONNOIR (small-study effect) : une PETITE étude (grande erreur-type) ne
devient significative qu'avec un effet ESTIMÉ ÉNORME, donc les petites études publiées montrent un effet bien plus grand
que les grandes — alors que toutes estiment le MÊME effet vrai.

Conclure « l'effet vaut la moyenne publiée » est SUR-CONFIANT : c'est la moyenne d'un sous-ensemble biaisé vers le haut.
Les corrections : inclure TOUTES les études (registres pré-enregistrés), pondérer par la taille, ou un estimateur ajusté
de la sélection (trim-and-fill).

LE MODE D'ÉCHEC DÉMASQUÉ : prendre la moyenne de la littérature publiée pour l'effet vrai est sur-confiant. Sans filtre de
publication, la moyenne est non biaisée (honnêteté). Distinct de meta_analyse (37, effets aléatoires) et p_hacking (98,
sélection INTRA-étude) — ici la sélection est ENTRE études. ABSTENTION si données insuffisantes. Pur Python, rng seedé.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"

TAILLES = [20, 50, 100, 500, 2000]


def _etude(theta, rng):
    """Une étude : taille tirée au hasard, estimateur ~ N(θ, se), significativité bilatérale |z|>1.96."""
    n = rng.choice(TAILLES)
    se = 1.0 / math.sqrt(n)
    est = rng.gauss(theta, se)
    return est, se, abs(est / se) > 1.96


def simule(theta, n_etudes, rng):
    """Renvoie (toutes les estimations, estimations publiées, erreurs-types publiées)."""
    toutes, pub, se_pub = [], [], []
    for _ in range(n_etudes):
        est, se, sig = _etude(theta, rng)
        toutes.append(est)
        if sig:
            pub.append(est)
            se_pub.append(se)
    return toutes, pub, se_pub


def _moyenne(xs):
    return sum(xs) / len(xs) if xs else 0.0


def analyse(theta=0.2, n_etudes=20000, rng=None):
    """Façade : effet vrai vs moyenne publiée vs asymétrie en entonnoir. (ANALYSE, {...}) ou (ABSTENTION)."""
    if rng is None or theta <= 0:
        return (ABSTENTION, "rng requis / θ ≤ 0 (cadre l'inflation de magnitude)")
    toutes, pub, se_pub = simule(theta, n_etudes, rng)
    if len(pub) < 50:
        return (ABSTENTION, "trop peu d'études publiées")
    petites = [e for e, s in zip(pub, se_pub) if s > 0.1]       # n ≤ 100
    grandes = [e for e, s in zip(pub, se_pub) if s <= 0.05]     # n ≥ 500
    return (ANALYSE, {"theta": theta, "moyenne_toutes": _moyenne(toutes), "moyenne_publiee": _moyenne(pub),
                      "effet_petites": _moyenne(petites), "effet_grandes": _moyenne(grandes),
                      "n_publiees": len(pub)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Effet vrai θ={i['theta']}. Moyenne de TOUTES les études = {i['moyenne_toutes']:.3f} (non biaisée) ; moyenne "
            f"PUBLIÉE = {i['moyenne_publiee']:.3f} (gonflée). Asymétrie en entonnoir : petites études publiées "
            f"{i['effet_petites']:.3f} vs grandes {i['effet_grandes']:.3f}. Prendre la moyenne publiée pour l'effet vrai "
            f"est sur-confiant — la littérature est un échantillon sélectionné.")


if __name__ == "__main__":
    import random
    print("=== BIAIS DE PUBLICATION (file-drawer) ===\n")
    st, info = analyse(rng=random.Random(0))
    print(" ", formule((st, info)))
