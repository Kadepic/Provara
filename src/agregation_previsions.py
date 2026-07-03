"""
PALIER 2 — AGRÉGATION DE PRÉVISIONS PROBABILISTES (pondération par historique + EXTREMIZE) (brique, 2026-06-26).

« Plusieurs prévisionnistes annoncent chacun une probabilité pour le même événement ; comment les combiner ? » La
MOYENNE simple des probabilités est SYSTÉMATIQUEMENT SOUS-CONFIANTE : en moyennant, on régresse vers 0.5 et on jette
l'information que des prévisionnistes en accord donnent collectivement une certitude plus grande qu'aucun seul. (Et
traiter tout le monde à égalité gaspille les ANTÉCÉDENTS : un prévisionniste régulièrement mauvais tire l'agrégat vers
le bruit.)

Remède en deux temps : (1) PONDÉRER chaque prévisionniste par son SCORE DE BRIER passé (les bons pèsent plus, les
nuls ≈ 0) ; (2) EXTREMIZER l'agrégat — logit(p̂) = a·moyenne_pondérée(logit pᵢ) avec a≥1 appris sur un historique — pour
défaire la régression vers 0.5. INVARIANT (jugé par calibration.py) : l'agrégat pondéré-extrémisé est CALIBRÉ et plus
TRANCHÉ (meilleur Brier), là où la moyenne naïve est sous-confiante. Garde-fou : a est BORNÉ et appris (jamais
d'extrémisation aveugle qui sur-confierait). ABSTENTION si historique trop court. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN = 30
_EPS = 1e-6
A_MAX = 4.0


def _clip(p):
    return min(1 - _EPS, max(_EPS, p))


def _logit(p):
    p = _clip(p)
    return math.log(p / (1 - p))


def _sigmoid(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def brier(historique):
    """Score de Brier moyen d'un prévisionniste : historique = liste de (p, y)."""
    if not historique:
        return 0.25
    return sum((p - y) ** 2 for p, y in historique) / len(historique)


def poids_track_record(historiques):
    """Poids ∝ compétence = (0.25 − Brier)_+ (0.25 = Brier du « toujours 0.5 »). Un prévisionniste pire que le hasard
    pèse 0. Renvoie des poids normalisés (uniformes si tous nuls)."""
    skill = [max(0.0, 0.25 - brier(h)) for h in historiques]
    s = sum(skill)
    if s <= 0:
        return [1.0 / len(historiques)] * len(historiques)
    return [x / s for x in skill]


def moyenne_logit_ponderee(ps, poids):
    return sum(poids[i] * _logit(ps[i]) for i in range(len(ps)))


def _logloss(zs, ys, a):
    s = 0.0
    for z, y in zip(zs, ys):
        p = _clip(_sigmoid(a * z))
        s += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return s / len(zs)


def ajuste_extremize(logit_agreges, ys, bornes=(1.0, A_MAX)):
    """Apprend le facteur d'extrémisation a∈[1, A_MAX] minimisant la log-perte (section dorée). a=1 => pas
    d'extrémisation. Plafonné pour ne JAMAIS sur-confier. Renvoie a ou None."""
    if len(logit_agreges) < N_MIN:
        return None
    lo, hi = bornes
    gr = (math.sqrt(5) - 1) / 2
    aa, bb = lo, hi
    c = bb - gr * (bb - aa)
    d = aa + gr * (bb - aa)
    fc, fd = _logloss(logit_agreges, ys, c), _logloss(logit_agreges, ys, d)
    for _ in range(60):
        if fc < fd:
            bb, d, fd = d, c, fc
            c = bb - gr * (bb - aa)
            fc = _logloss(logit_agreges, ys, c)
        else:
            aa, c, fc = c, d, fd
            d = aa + gr * (bb - aa)
            fd = _logloss(logit_agreges, ys, d)
        if abs(bb - aa) < 1e-4:
            break
    return (aa + bb) / 2


def agrege(ps, poids, a=1.0):
    """Agrégat final : extrémise la moyenne pondérée des logits. Renvoie une probabilité dans (0,1)."""
    return _sigmoid(a * moyenne_logit_ponderee(ps, poids))


def moyenne_naive(ps):
    return sum(ps) / len(ps)


def calibre_agregateur(previsions, ys, historiques):
    """Apprend (poids, a) à partir d'un historique de prévisions multi-sources. `previsions` = liste de listes pᵢ (une
    par item), `ys` = issues, `historiques` = track records par prévisionniste. Renvoie (ESTIMATION, {poids, a}, None)
    ou (ABSTENTION, None, raison)."""
    if len(previsions) < N_MIN:
        return (ABSTENTION, None, f"historique trop court (n={len(previsions)} < {N_MIN})")
    poids = poids_track_record(historiques)
    zs = [moyenne_logit_ponderee(ps, poids) for ps in previsions]
    a = ajuste_extremize(zs, ys)
    if a is None:
        return (ABSTENTION, None, "extrémisation non estimable")
    return (ESTIMATION, {"poids": poids, "a": a}, None)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas agréger les prévisions : {res[2]}."
    return (f"Agrégat pondéré par les antécédents (Brier) puis extrémisé (a={res[1]['a']:.2f}) : plus tranché et calibré "
            f"que la moyenne simple, qui serait sous-confiante. Le facteur a est plafonné pour ne jamais sur-confier.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    # 3 prévisionnistes voient la vraie proba q via un bruit logit ; le 3ᵉ est mauvais (gros bruit)
    taus = [0.6, 0.6, 1.8]
    prev, ys, hist = [], [], [[], [], []]
    for _ in range(400):
        q = rng.random()
        ps = [_sigmoid(_logit(q) + rng.gauss(0, t)) for t in taus]
        y = 1 if rng.random() < q else 0
        prev.append(ps); ys.append(y)
        for i in range(3):
            hist[i].append((ps[i], y))
    st, info, _ = calibre_agregateur(prev, ys, hist)
    print("=== AGRÉGATION DE PRÉVISIONS — moyenne naïve vs pondérée+extrémisée ===\n")
    print(f"  Brier par prévisionniste = {[round(brier(h),3) for h in hist]}")
    print(f"  poids track-record = {[round(w,3) for w in info['poids']]} ; a extrémisation = {info['a']:.2f}")
    print(" ", formule((st, info, None)))
