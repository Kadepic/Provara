"""
PALIER 2 — COPULES & DÉPENDANCE DE QUEUE : présumer l'indépendance sous-estime le risque CONJOINT (brique 72,
2026-06-27).

Une copule C(u,v) couple des marginales uniformes en une loi jointe : elle capte la STRUCTURE DE DÉPENDANCE
séparément des lois marginales (théorème de Sklar). Cas limites (bornes de Fréchet-Hoeffding) :
    max(u+v−1, 0) ≤ C(u,v) ≤ min(u,v)        (anti-comonotone ≤ C ≤ comonotone)
L'indépendance est C(u,v)=u·v. La DÉPENDANCE DE QUEUE inférieure λ = lim_{q→0} C(q,q)/q mesure la tendance des
extrêmes à survenir ENSEMBLE : 0 sous indépendance, > 0 pour une copule de Clayton (λ = 2^{−1/θ}).

LE MODE D'ÉCHEC DÉMASQUÉ : estimer P(X et Y tous deux extrêmes) en PRÉSUMANT l'indépendance donne ≈ q² (minuscule) —
l'illusion de la diversification. Si les variables sont dépendantes en queue, la vraie probabilité conjointe est
≈ λ·q ≫ q² → présumer l'indépendance SOUS-ESTIME massivement le risque de défaillance simultanée (le piège de la
copule gaussienne, crise de 2008) = SUR-CONFIANCE. La copule/empirique le capte. ABSTENTION si invalide. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"


def borne_inf(u, v):
    """Borne de Fréchet-Hoeffding inférieure (anti-comonotone) W(u,v)=max(u+v−1,0)."""
    return max(u + v - 1, 0.0)


def borne_sup(u, v):
    """Borne supérieure (comonotone) M(u,v)=min(u,v)."""
    return min(u, v)


def independance(u, v):
    return u * v


def clayton(u, v, theta):
    """Copule de Clayton C(u,v)=(u^{−θ}+v^{−θ}−1)^{−1/θ} (θ>0 : dépendance de queue INFÉRIEURE)."""
    if u <= 0 or v <= 0:
        return 0.0
    return (u ** (-theta) + v ** (-theta) - 1) ** (-1 / theta)


def lambda_inf_clayton(theta):
    """Dépendance de queue inférieure théorique de Clayton : λ = 2^{−1/θ}."""
    return 2.0 ** (-1.0 / theta)


def echantillon_clayton(rng, n, theta):
    """Tire n couples (u,v) ~ copule de Clayton (échantillonnage conditionnel)."""
    out = []
    for _ in range(n):
        u = rng.random()
        w = rng.random()
        v = (u ** (-theta) * (w ** (-theta / (1 + theta)) - 1) + 1) ** (-1 / theta)
        out.append((u, min(1.0, max(0.0, v))))
    return out


def proba_jointe_extreme(echantillon, q):
    """P(U≤q ET V≤q) empirique (les deux dans la queue basse)."""
    return sum(1 for u, v in echantillon if u <= q and v <= q) / len(echantillon)


def proba_jointe_independance(q):
    """Estimation SOUS HYPOTHÈSE D'INDÉPENDANCE : q·q."""
    return q * q


def tail_inf_empirique(echantillon, q):
    """Dépendance de queue empirique λ ≈ C(q,q)/q = P(V≤q | U≤q)."""
    return proba_jointe_extreme(echantillon, q) / q if q > 0 else 0.0


def analyse(echantillon, q=0.05):
    """Façade : compare le risque conjoint extrême empirique vs présumé-indépendant. (ANALYSE, {...}) ou ABSTENTION."""
    if not echantillon or not (0 < q < 1):
        return (ANALYSE if False else ABSTENTION, "échantillon vide ou q∉(0,1)")
    pj = proba_jointe_extreme(echantillon, q)
    pi = proba_jointe_independance(q)
    return (ANALYSE, {"q": q, "jointe_empirique": pj, "jointe_independance": pi,
                      "lambda_inf": tail_inf_empirique(echantillon, q), "facteur": (pj / pi if pi > 0 else float("inf"))})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Analyse impossible : {res[1]}."
    info = res[1]
    return (f"P(deux extrêmes simultanés, q={info['q']}) = {info['jointe_empirique']:.4f} ; en présumant l'indépendance "
            f"on dirait {info['jointe_independance']:.4f} (×{info['facteur']:.1f} trop optimiste). Présumer "
            f"l'indépendance sous-estime le risque conjoint (sur-confiance).")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== COPULES & DÉPENDANCE DE QUEUE ===\n")
    for theta, lab in [(0.3, "faible dépendance"), (2.0, "forte dépendance de queue")]:
        ech = echantillon_clayton(rng, 100000, theta)
        info = analyse(ech, 0.05)[1]
        print(f"  Clayton θ={theta} ({lab}): λ_théo={lambda_inf_clayton(theta):.3f} λ_emp={info['lambda_inf']:.3f} ; "
              f"P_jointe={info['jointe_empirique']:.4f} vs indép {info['jointe_independance']:.4f} (×{info['facteur']:.1f})")
    print(" ", formule(analyse(echantillon_clayton(rng, 50000, 2.0), 0.05)))
