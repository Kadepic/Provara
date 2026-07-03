"""
PALIER 2 — CALIBRATION DU CLASSEMENT (ranking) : confiance HONNÊTE des comparaisons par paires (brique, 2026-06-26).

« Un moteur de recherche/recommandation ORDONNE des items par score. L'ORDRE peut être bon, mais avec quelle CONFIANCE
l'item A est-il vraiment plus pertinent que B ? » L'erreur courante : transformer la différence de score en probabilité
par un sigmoïde BRUT, σ(s_A − s_B). Quand les scores ont une échelle plus large que l'incertitude réelle, ce sigmoïde
SATURE : il annonce « 99 % sûr que A > B » alors que l'ordre se trompe bien plus souvent — SUR-CONFIANCE en TÊTE de
liste, là où les décisions comptent le plus.

Le remède : une TEMPÉRATURE T apprise (σ((s_A − s_B)/T)) qui APLATIT les probabilités jusqu'à ce qu'elles soient
calibrées, SANS jamais changer l'ORDRE (T>0 est monotone). INVARIANT (jugé par calibration.py) : parmi les paires
annoncées correctes avec confiance p, la fraction réellement bien ordonnée ≈ p (le sigmoïde brut est sur-confiant, le
sigmoïde tempéré est calibré). On fournit aussi le NDCG (qualité du classement) comme utilité. ABSTENTION si trop peu de
paires pour estimer T. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 30
_EPS = 1e-12


def _sigmoid(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def proba_mieux(s_i, s_j, T: float = 1.0):
    """Probabilité (calibrée si T appris) que l'item i soit mieux classé que j : σ((s_i − s_j)/T)."""
    return _sigmoid((s_i - s_j) / T)


def _nll_paires(diffs, ordres, T):
    s = 0.0
    for d, y in zip(diffs, ordres):
        p = _sigmoid(d / T)
        p = min(1 - _EPS, max(_EPS, p))
        s += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return s / len(diffs)


def ajuste_temperature(diffs, ordres, bornes=(0.05, 50.0)):
    """Apprend T>0 minimisant la log-perte des comparaisons par paires (recherche par section dorée). diffs = s_i−s_j ;
    ordres = 1 si i est VRAIMENT mieux classé que j, 0 sinon. Renvoie T ou None si trop peu de paires."""
    if len(diffs) < N_MIN:
        return None
    lo, hi = bornes
    gr = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c = b - gr * (b - a)
    d = a + gr * (b - a)
    fc = _nll_paires(diffs, ordres, c)
    fd = _nll_paires(diffs, ordres, d)
    for _ in range(80):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = _nll_paires(diffs, ordres, c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = _nll_paires(diffs, ordres, d)
        if abs(b - a) < 1e-4:
            break
    return (a + b) / 2


def classe(scores):
    """Renvoie les indices triés par score DÉCROISSANT (le classement lui-même, indépendant de T)."""
    return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)


def dcg(pertinences_dans_l_ordre, k=None):
    g = pertinences_dans_l_ordre if k is None else pertinences_dans_l_ordre[:k]
    return sum(rel / math.log2(pos + 2) for pos, rel in enumerate(g))


def ndcg(ordre_predit, pertinences, k=None):
    """NDCG@k : qualité du classement prédit vs le classement IDÉAL (pertinences décroissantes). Dans [0,1]."""
    pred = [pertinences[i] for i in ordre_predit]
    ideal = sorted(pertinences, reverse=True)
    di = dcg(ideal, k)
    return dcg(pred, k) / di if di > 0 else 0.0


def calibre(diffs, ordres):
    """Façade : (ESTIMATION, T, log-perte) ou (ABSTENTION, None, raison)."""
    T = ajuste_temperature(diffs, ordres)
    if T is None:
        return (ABSTENTION, None, f"trop peu de paires (n={len(diffs)} < {N_MIN})")
    return (ESTIMATION, T, _nll_paires(diffs, ordres, T))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas calibrer le classement : {res[2]}."
    return (f"Confiances de classement calibrées par température T={res[1]:.2f} : un « X % sûr que A passe avant B » "
            f"s'avère juste ~X % du temps (le sigmoïde brut serait sur-confiant en tête de liste). L'ordre est inchangé.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== CALIBRATION DU CLASSEMENT — sigmoïde brut (sur-confiant) vs tempéré ===\n")
    # scores AMPLIFIÉS (échelle trop large) face à une pertinence vraie BRUITÉE -> sigmoïde brut sature -> sur-confiant.
    rel = [rng.gauss(0, 1.0) for _ in range(60)]
    score = [4.0 * r for r in rel]                         # le modèle annonce des scores trop tranchés
    truth = [r + rng.gauss(0, 1.0) for r in rel]           # « réellement mieux » est bruité
    diffs, ordres = [], []
    for i in range(len(rel)):
        for j in range(len(rel)):
            if i != j:
                diffs.append(score[i] - score[j]); ordres.append(1 if truth[i] > truth[j] else 0)
    qual = truth
    st, T, ll = calibre(diffs, ordres)
    print(f"  T appris = {T:.2f} (>1 => le sigmoïde brut était trop tranché)")
    print(f"  paire au score serré : brut σ={proba_mieux(1.0, 0.0):.3f}  tempéré σ={proba_mieux(1.0, 0.0, T):.3f}")
    print(f"  NDCG@10 du classement par score = {ndcg(classe(score), qual, 10):.3f}")
    print(" ", formule((st, T, ll)))
