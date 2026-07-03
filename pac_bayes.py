"""
PALIER 2 — BORNES PAC-BAYES : le risque vrai GARANTI d'un prédicteur, pas son risque empirique optimiste (brique 63,
2026-06-27).

Quand on apprend un prédicteur sur des données, son risque EMPIRIQUE (erreur sur l'échantillon) SOUS-ESTIME le risque
VRAI (erreur en population) — d'autant plus qu'on a SÉLECTIONNÉ le prédicteur pour bien coller aux données (biais
d'optimisme / sur-apprentissage). Annoncer le risque empirique comme la performance réelle est SUR-CONFIANT.

Une borne PAC-Bayes donne, avec probabilité ≥ 1−δ sur l'échantillon, un MAJORANT VALIDE du risque vrai d'un
prédicteur RANDOMISÉ (distribution Q sur les hypothèses), valable pour TOUT Q simultanément :
    kl( R_emp(Q) ‖ R_vrai(Q) ) ≤ ( KL(Q‖P) + ln(2√n/δ) ) / n          (Maurer-Seeger, kl = KL de Bernoulli)
  ⇒ R_vrai(Q) ≤ kl⁻¹( R_emp(Q), budget )    (on inverse le kl pour majorer).
P = prior (indépendant des données), Q = posterior (choisi APRÈS les données). Le terme KL(Q‖P)/n est le PRIX de
complexité : plus Q s'éloigne du prior, plus la garantie se relâche. Borne plus simple (McAllester) :
    R_vrai(Q) ≤ R_emp(Q) + √( (KL(Q‖P) + ln(2√n/δ)) / (2n) ).

LE MODE D'ÉCHEC DÉMASQUÉ : utiliser R_emp(Q) comme garantie est SUR-CONFIANT (ce n'est pas un majorant : R_vrai le
dépasse ~la moitié du temps, et systématiquement pour l'hypothèse sélectionnée). La borne PAC-Bayes, elle, MAJORE le
risque vrai avec confiance 1−δ. Vertu : la borne → R_emp quand n→∞ (l'évidence rachète l'optimisme). ABSTENTION si
n=0, δ∉(0,1) ou distributions non normalisées. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
BORNE = "borne"


def kl_bernoulli(q, p):
    """kl(q‖p) = q ln(q/p) + (1−q) ln((1−q)/(1−p)) (divergence de Bernoulli, q,p ∈ [0,1])."""
    p = min(1 - 1e-15, max(1e-15, p))
    t1 = q * math.log(q / p) if q > 0 else 0.0
    t2 = (1 - q) * math.log((1 - q) / (1 - p)) if q < 1 else 0.0
    return t1 + t2


def kl_inverse(q, budget):
    """Plus grand p ∈ [q,1] tel que kl(q‖p) ≤ budget (majorant PAC-Bayes du risque vrai). Bisection."""
    if budget <= 0:
        return q
    lo, hi = q, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if kl_bernoulli(q, mid) > budget:
            hi = mid
        else:
            lo = mid
    return lo


def kl_distributions(Q, P):
    """KL(Q‖P) entre deux distributions sur les hypothèses (dicts h→proba). Exige P(h)>0 là où Q(h)>0."""
    tot = 0.0
    for h in Q:
        if Q[h] > 0:
            tot += Q[h] * math.log(Q[h] / P[h])
    return tot


def risque(Q, risques):
    """Risque moyen sous Q : Σ Q(h)·risque(h)."""
    return sum(Q[h] * risques[h] for h in Q)


def _budget(Q, P, n, delta):
    return (kl_distributions(Q, P) + math.log(2 * math.sqrt(n) / delta)) / n


def borne(Q, P, risques_emp, n, delta=0.05):
    """Borne PAC-Bayes-kl (Maurer-Seeger) sur le risque vrai de Q. (BORNE, majorant) ou (ABSTENTION, raison)."""
    if n <= 0 or not (0 < delta < 1):
        return (ABSTENTION, "n ≤ 0 ou δ hors (0,1)")
    if abs(sum(Q.values()) - 1) > 1e-9 or abs(sum(P.values()) - 1) > 1e-9:
        return (ABSTENTION, "Q ou P non normalisé")
    if any(Q[h] > 0 and P.get(h, 0.0) <= 0 for h in Q):
        return (ABSTENTION, "support de Q hors du prior P (KL infini)")
    r_emp = risque(Q, risques_emp)
    return (BORNE, kl_inverse(r_emp, _budget(Q, P, n, delta)))


def borne_mcallester(Q, P, risques_emp, n, delta=0.05):
    """Borne PAC-Bayes de McAllester (forme racine, plus simple et plus lâche)."""
    r_emp = risque(Q, risques_emp)
    return r_emp + math.sqrt(_budget(Q, P, n, delta) / 2)


def gibbs(P, risques_emp, gamma, n):
    """Posterior de Gibbs Q(h) ∝ P(h)·exp(−γ·n·R_emp(h)) (concentre sur les hypothèses à faible risque empirique)."""
    log_w = {h: math.log(P[h]) - gamma * n * risques_emp[h] for h in P if P[h] > 0}
    m = max(log_w.values())
    w = {h: math.exp(lw - m) for h, lw in log_w.items()}
    z = sum(w.values())
    return {h: wi / z for h, wi in w.items()}


def formule(res, r_emp=None) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas borner le risque : {res[1]}."
    b = res[1]
    pre = f"Risque empirique {r_emp:.3f} mais " if r_emp is not None else ""
    return (f"{pre}risque VRAI ≤ {b:.3f} (PAC-Bayes, 95% confiance). Annoncer le seul risque empirique serait "
            f"sur-confiant — il sous-estime l'erreur en population.")


if __name__ == "__main__":
    print("=== BORNES PAC-BAYES — risque vrai garanti vs empirique optimiste ===\n")
    P = {f"h{i}": 1 / 10 for i in range(10)}      # prior uniforme sur 10 hypothèses
    emp = {f"h{i}": 0.30 + 0.02 * i for i in range(10)}   # risques empiriques observés
    for n in (100, 1000, 10000):
        Q = gibbs(P, emp, gamma=2.0, n=n)
        st, b = borne(Q, P, emp, n)
        bm = borne_mcallester(Q, P, emp, n)
        print(f"   n={n:>5}: R_emp(Q)={risque(Q,emp):.3f}  borne kl={b:.3f}  borne McAllester={bm:.3f}")
    Q = gibbs(P, emp, 2.0, 1000)
    print(" ", formule(borne(Q, P, emp, 1000), risque(Q, emp)))
