"""
PALIER 2 — MÉTA-ANALYSE (effets aléatoires, brique 37, 2026-06-25).

Synthétiser l'évidence de PLUSIEURS études (chacune donnant un effet θᵢ ± erreur-type seᵢ) en UN effet global honnête.
Le piège : si les études DIVERGENT plus que ne l'explique leur erreur d'échantillonnage (HÉTÉROGÉNÉITÉ), le modèle à
EFFET FIXE (simple moyenne pondérée par 1/seᵢ²) sous-estime l'incertitude -> sur-confiant. Le modèle à EFFETS
ALÉATOIRES (DerSimonian-Laird) ajoute la variance INTER-études τ² :

  wᵢ = 1/seᵢ² ; Q = Σwᵢ(θᵢ−θ_FE)² ; τ² = max(0, (Q−(k−1)) / (Σwᵢ − Σwᵢ²/Σwᵢ))
  wᵢ* = 1/(seᵢ²+τ²) ; effet global = Σwᵢ*θᵢ/Σwᵢ* ; SE = 1/√Σwᵢ* ; IC = effet ± z·SE
  I² = max(0, (Q−(k−1))/Q) = part de la variance due à l'hétérogénéité.

INVARIANT (jugé par calibration.py) : l'IC à effets aléatoires couvre le vrai effet moyen ~confiance même sous
hétérogénéité, là où l'effet fixe SOUS-couvre (SURCONFIANT). ABSTENTION si < 2 études / erreurs invalides. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
_Z = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}


def _phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def meta_analyse(effets, erreurs_std, confiance=0.95, modele="aleatoire"):
    """Combine des études (effets θᵢ, erreurs-types seᵢ). `modele` ∈ {aleatoire (DL), fixe}. Renvoie
    (ESTIMATION, infos) avec infos = {effet, ic, se, tau2, I2, Q, p_heterogeneite, k} ou ABSTENTION."""
    th = [float(v) for v in effets]
    se = [float(v) for v in erreurs_std]
    k = len(th)
    if k < 2 or any(s <= 0 for s in se):
        return (ABSTENTION, {"raison": "moins de 2 études ou erreur-type invalide"})
    v = [s * s for s in se]
    w = [1.0 / vi for vi in v]
    sw = sum(w)
    fe = sum(w[i] * th[i] for i in range(k)) / sw
    Q = sum(w[i] * (th[i] - fe) ** 2 for i in range(k))
    df = k - 1
    c = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    I2 = max(0.0, (Q - df) / Q) if Q > 0 else 0.0
    p_het = 1.0 - _chi2_cdf(Q, df)
    if modele == "fixe":
        eff, se_g = fe, math.sqrt(1.0 / sw)
    else:
        ws = [1.0 / (v[i] + tau2) for i in range(k)]
        sws = sum(ws)
        eff = sum(ws[i] * th[i] for i in range(k)) / sws
        se_g = math.sqrt(1.0 / sws)
    z = _Z.get(round(confiance, 2), 1.96)
    infos = {"effet": eff, "ic": (eff - z * se_g, eff + z * se_g), "se": se_g, "tau2": tau2,
             "I2": I2, "Q": Q, "p_heterogeneite": p_het, "k": k}
    return (ESTIMATION, infos)


def _gammap(a, x):
    if x <= 0:
        return 0.0
    if x < a + 1.0:
        ap, s, t = a, 1.0 / a, 1.0 / a
        for _ in range(300):
            ap += 1.0
            t *= x / ap
            s += t
            if abs(t) < abs(s) * 1e-13:
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


def _chi2_cdf(x, df):
    return _gammap(df / 2.0, x / 2.0)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas combiner les études : {res[1].get('raison')}."
    i = res[1]
    bas, haut = i["ic"]
    het = "forte" if i["I2"] > 0.5 else ("modérée" if i["I2"] > 0.25 else "faible")
    return (f"Effet global ≈ {i['effet']:.3f} (à 95% entre {bas:.3f} et {haut:.3f}), sur {i['k']} études. "
            f"Hétérogénéité {het} (I²={round(i['I2']*100)}%) — prise en compte dans l'incertitude.")


if __name__ == "__main__":
    print("=== MÉTA-ANALYSE (effets aléatoires) ===\n")
    effets = [0.5, 0.3, 0.7, 0.4, 0.9, 0.2]
    se = [0.1, 0.12, 0.15, 0.1, 0.2, 0.13]
    print("  aléatoire :", formule(meta_analyse(effets, se, 0.95, "aleatoire")))
    print("  fixe      :", formule(meta_analyse(effets, se, 0.95, "fixe")))
