"""
PALIER 2 — ESTIMATION DE TAUX POISSON (comptages, brique 36, 2026-06-25).

Beaucoup de questions non-bornées portent sur un TAUX d'événements observé par COMPTAGE : accidents/an, défauts/lot,
requêtes/seconde, désintégrations/min. On observe k événements sur une exposition `t` (durée, surface, lot) ; le taux
vrai λ existe mais est incertain. Modèle de Poisson :

  λ̂ = k / t   ;   IC EXACT de Garwood :  λ_bas = ½·χ²_{α/2}(2k)/t ,  λ_haut = ½·χ²_{1−α/2}(2k+2)/t
  P(N = k) = e^{−λt}(λt)^k / k!   ;   P(N ≥ k) = Q régularisée γ(k, λt)

INVARIANT (jugé par calibration.py) : l'IC exact couvre le vrai λ ≥ confiance (conservateur par discrétion, jamais
sur-confiant). Cas k=0 géré (borne basse 0). Pur Python (gamma incomplète + son inverse).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def _gammap(a, x):
    """Gamma incomplète régularisée inférieure P(a,x)."""
    if x <= 0:
        return 0.0
    if x < a + 1.0:
        ap, s, terme = a, 1.0 / a, 1.0 / a
        for _ in range(300):
            ap += 1.0
            terme *= x / ap
            s += terme
            if abs(terme) < abs(s) * 1e-13:
                break
        return s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1.0 - a
    c, d = 1e300, 1.0 / b
    h = d
    for i in range(1, 300):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-13:
            break
    return 1.0 - math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def _chi2_quantile(p, df):
    """Quantile de la loi du χ² à df ddl (inverse de la CDF = gammap(df/2, x/2)) par bissection."""
    if p <= 0:
        return 0.0
    a = df / 2.0
    lo, hi = 0.0, max(10.0, df + 10.0 * math.sqrt(2.0 * df) + 20.0)
    while _gammap(a, hi / 2.0) < p:
        hi *= 2.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if _gammap(a, mid / 2.0) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def estime_taux(k, exposition=1.0, confiance=0.90):
    """Estime un taux λ (événements par unité d'exposition) depuis k comptages sur `exposition`. Renvoie
    (ESTIMATION, (lambda, (bas, haut)), confiance) ou ABSTENTION (exposition ≤ 0 / k < 0)."""
    k = int(k)
    t = float(exposition)
    if t <= 0 or k < 0:
        return (ABSTENTION, None, "exposition ≤ 0 ou comptage négatif")
    alpha = 1.0 - confiance
    bas = 0.0 if k == 0 else 0.5 * _chi2_quantile(alpha / 2.0, 2 * k) / t
    haut = 0.5 * _chi2_quantile(1.0 - alpha / 2.0, 2 * k + 2) / t
    return (ESTIMATION, (k / t, (bas, haut)), confiance)


def proba_compte(lam, exposition, k):
    """P(N = k) pour un Poisson de moyenne λ·exposition."""
    mu = float(lam) * float(exposition)
    k = int(k)
    return math.exp(-mu + k * math.log(mu) - math.lgamma(k + 1)) if mu > 0 else (1.0 if k == 0 else 0.0)


def proba_au_moins(lam, exposition, k):
    """P(N ≥ k) pour un Poisson de moyenne λ·exposition."""
    mu = float(lam) * float(exposition)
    k = int(k)
    if k <= 0:
        return 1.0
    return _gammap(k, mu)        # P(N ≥ k) = P_regularisée(k, mu)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer le taux : {res[2]}."
    lam, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Taux estimé ≈ {lam:.3g} par unité (à {round(conf*100)}% entre {bas:.3g} et {haut:.3g}).")


if __name__ == "__main__":
    print("=== ESTIMATION DE TAUX POISSON ===\n")
    print("  3 pannes en 2 ans :", formule(estime_taux(3, 2.0, 0.90)))
    print("  0 défaut sur 500 pièces :", formule(estime_taux(0, 500.0, 0.95)))
    print("  P(au moins 5 events | λ=2, t=1) =", round(proba_au_moins(2.0, 1.0, 5), 4))
