"""
PALIER 2 — CONTRÔLE DU TAUX DE FAUSSES DÉCOUVERTES (multiplicité des TESTS, Benjamini-Hochberg) (brique, 2026-06-26).

« On teste K hypothèses (K gènes, K variantes A/B, K features) et on garde tout ce qui est “significatif” à α=0.05. »
Piège de MULTIPLICITÉ côté DÉCISION : si beaucoup d'hypothèses sont nulles, on accumule les FAUX POSITIFS — parmi les
« découvertes », une FRACTION ÉNORME est du bruit. Annoncer « ces K′ résultats sont réels » est alors SUR-CONFIANT : le
taux de fausses découvertes (FDR) dépasse de loin α.

Deux remèdes : BONFERRONI (seuil α/K) contrôle la probabilité de la MOINDRE fausse alarme (FWER) — très strict, peu de
puissance ; BENJAMINI-HOCHBERG contrôle le FDR à q (on rejette les p₍ᵢ₎ ≤ q·i/K avec i le rang) — bien plus de PUISSANCE
à FDR maîtrisé. INVARIANT (jugé par calibration.py) : parmi les découvertes de BH, la proportion réellement vraies ≥ 1−q
(FDR ≤ q) ; le seuil naïf α voit son FDR EXPLOSER (sur-confiant) ; BH détecte plus de vrais positifs que Bonferroni.
ABSTENTION si aucune p-valeur. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def naif(pvaleurs, alpha=0.05):
    """Seuil NAÏF : rejette chaque test à α (ignore la multiplicité). Renvoie les indices rejetés."""
    return [i for i, p in enumerate(pvaleurs) if p <= alpha]


def bonferroni(pvaleurs, alpha=0.05):
    """BONFERRONI : rejette à α/K (contrôle le FWER). Renvoie les indices rejetés."""
    K = len(pvaleurs)
    seuil = alpha / K
    return [i for i, p in enumerate(pvaleurs) if p <= seuil]


def benjamini_hochberg(pvaleurs, q=0.05):
    """BENJAMINI-HOCHBERG : contrôle le FDR à q. Trouve le plus grand rang i (1-based, p triées) tel que p₍ᵢ₎ ≤ q·i/K,
    et rejette tous les tests de p-valeur ≤ ce seuil. Renvoie les indices rejetés (dans l'ordre d'origine)."""
    K = len(pvaleurs)
    if K == 0:
        return []
    ordre = sorted(range(K), key=lambda i: pvaleurs[i])
    kmax = -1
    for rang, i in enumerate(ordre, start=1):
        if pvaleurs[i] <= q * rang / K:
            kmax = rang
    if kmax < 0:
        return []
    seuil = pvaleurs[ordre[kmax - 1]]
    return [i for i in range(K) if pvaleurs[i] <= seuil]


def decouvre(pvaleurs, q=0.05, methode="bh"):
    """Façade : (ESTIMATION, indices_rejetés, q) ou (ABSTENTION, None, raison)."""
    if not pvaleurs:
        return (ABSTENTION, None, "aucune p-valeur")
    fn = {"bh": benjamini_hochberg, "bonferroni": lambda p, a: bonferroni(p, a), "naif": lambda p, a: naif(p, a)}.get(methode)
    if fn is None:
        return (ABSTENTION, None, f"méthode inconnue : {methode}")
    return (ESTIMATION, fn(pvaleurs, q), q)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas décider des découvertes : {res[2]}."
    n = len(res[1])
    return (f"{n} découverte(s) retenue(s) avec FDR contrôlé à {round(res[2]*100)}% (Benjamini-Hochberg) : garder tout "
            f"ce qui passe α sans correction gonflerait le taux de fausses découvertes — sur-confiance sur les résultats.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    # 200 tests : 180 nuls (p~U(0,1)), 20 vrais effets (p petite)
    pv, vrai = [], []
    for _ in range(180):
        pv.append(rng.random()); vrai.append(False)
    for _ in range(20):
        pv.append(rng.uniform(0, 0.01)); vrai.append(True)
    print("=== CONTRÔLE DU FDR — naïf vs Bonferroni vs Benjamini-Hochberg ===\n")
    for nom, idx in [("naïf α=0.05", naif(pv, 0.05)),
                     ("Bonferroni", bonferroni(pv, 0.05)),
                     ("Benjamini-Hochberg", benjamini_hochberg(pv, 0.05))]:
        if idx:
            fp = sum(1 for i in idx if not vrai[i])
            fdr = fp / len(idx)
            tp = len(idx) - fp
            print(f"  {nom:20s} : {len(idx)} découvertes, {tp} vrais / {fp} faux, FDR={fdr:.2f}")
    print(" ", formule(decouvre(pv, 0.05, "bh")))
