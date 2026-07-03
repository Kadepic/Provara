"""
PALIER 2 — PROPAGATION D'INCERTITUDE (brique 5, 2026-06-25). LE PONT avec le substrat P1.

Le borné (P1 / physique.py / CODATA) fournit des grandeurs MESURÉES, chacune avec une BARRE D'ERREUR (σ). Quand on
les combine dans un calcul z = f(x₁,…,xₙ), l'incertitude se PROPAGE. Cette brique la propage HONNÊTEMENT, de deux
façons :

  • propage_mc  — MONTE-CARLO : échantillonne les entrées selon leurs lois, calcule f, renvoie un INTERVALLE par
    quantiles empiriques. EXACT pour n'importe quel f (linéaire ou non), c'est la version CALIBRÉE.
  • propage_lineaire — PREMIER ORDRE : σ_z² = Σ (∂f/∂xᵢ)² σᵢ² (gradient numérique). Rapide, mais SUPPOSE f ~ linéaire
    autour du point ; sur un f très non linéaire elle peut être SUR-CONFIANTE (ex. z=x² en x̄=0 -> σ_z≈0, fausse
    certitude). On expose les deux et on laisse calibration.py démasquer la version linéaire quand elle ment.

INVARIANT : l'intervalle MC à `confiance` contient la vraie valeur ~`confiance` du temps quand les entrées suivent
les lois déclarées (prouvé valide_propagation.py). ABSTENTION si une incertitude est invalide (σ < 0).
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"

_Z = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}


def propage_mc(f, entrees, confiance: float = 0.90, n: int = 20000, seed: int = 0):
    """Propagation MONTE-CARLO. `entrees` = liste de (moyenne, sigma) (lois gaussiennes indépendantes). Renvoie
    (ESTIMATION, (point, (bas, haut)), confiance) — point = f(moyennes), intervalle par quantiles empiriques — ou
    ABSTENTION si un sigma est invalide. Exact pour tout f (non-linéaire compris)."""
    moyennes = []
    for (m, s) in entrees:
        if s < 0 or math.isnan(s) or math.isinf(s):
            return (ABSTENTION, None, f"incertitude invalide (σ={s})")
        moyennes.append(float(m))
    point = f(*moyennes)
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        ech = [rng.gauss(m, s) for (m, s) in entrees]
        vals.append(f(*ech))
    vals.sort()
    alpha = (1.0 - confiance) / 2.0

    def q(p):
        i = p * (len(vals) - 1)
        lo = int(i)
        if lo + 1 >= len(vals):
            return vals[-1]
        return vals[lo] * (1.0 - (i - lo)) + vals[lo + 1] * (i - lo)

    return (ESTIMATION, (point, (q(alpha), q(1.0 - alpha))), confiance)


def propage_lineaire(f, valeurs, sigmas):
    """Propagation au PREMIER ORDRE : renvoie (ESTIMATION, (z, sigma_z), None) avec σ_z = sqrt(Σ (∂f/∂xᵢ·σᵢ)²),
    gradient par différences centrées. ABSTENTION si σ invalide. ⚠ suppose f ~ linéaire (cf. docstring module)."""
    valeurs = [float(v) for v in valeurs]
    for s in sigmas:
        if s < 0 or math.isnan(s) or math.isinf(s):
            return (ABSTENTION, None, f"incertitude invalide (σ={s})")
    z = f(*valeurs)
    var = 0.0
    for i in range(len(valeurs)):
        h = 1e-5 * (abs(valeurs[i]) + 1.0)
        plus = list(valeurs); plus[i] += h
        moins = list(valeurs); moins[i] -= h
        d = (f(*plus) - f(*moins)) / (2.0 * h)
        var += (d * sigmas[i]) ** 2
    return (ESTIMATION, (z, math.sqrt(var)), None)


def intervalle_lineaire(f, valeurs, sigmas, confiance: float = 0.90):
    """Intervalle (z ± k·σ_z) issu de la propagation linéaire. Renvoie (ESTIMATION, (z, (bas, haut)), confiance)."""
    res = propage_lineaire(f, valeurs, sigmas)
    if res[0] == ABSTENTION:
        return res
    z, sigma = res[1]
    k = _Z.get(round(confiance, 2), 1.6449)
    return (ESTIMATION, (z, (z - k * sigma, z + k * sigma)), confiance)


def _n(v):
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.3g}"


def formule(res, quoi: str = "mc") -> str:
    """Parole honnête d'une propagation. `quoi` ∈ {mc, lineaire}."""
    if res[0] == ABSTENTION:
        return f"Je ne peux pas propager l'incertitude : {res[2]}."
    point, (bas, haut), conf = res[1][0], res[1][1], res[2]
    pct = round(conf * 100)
    return (f"Le résultat vaut ~{_n(point)}, mais avec l'incertitude des mesures combinées : à {pct}% il est "
            f"entre {_n(bas)} et {_n(haut)}.")


if __name__ == "__main__":
    print("=== PROPAGATION D'INCERTITUDE (le pont avec le borné mesuré) ===\n")
    # énergie cinétique E = ½ m v², m = 2.0 ± 0.1 kg, v = 3.0 ± 0.2 m/s
    Ec = lambda m, v: 0.5 * m * v * v
    print(" ", formule(propage_mc(Ec, [(2.0, 0.1), (3.0, 0.2)]), "mc"))
    z, sig = propage_lineaire(Ec, [2.0, 3.0], [0.1, 0.2])[1]
    print(f"   linéaire : E = {z:.3f} ± {sig:.3f} J (1σ)")
    # cas piège : z = x², x = 0 ± 1 -> la propagation linéaire dit « σ=0 » (faux), le MC voit l'étalement réel
    print("  z=x², x=0±1 :")
    print("    linéaire :", propage_lineaire(lambda x: x * x, [0.0], [1.0])[1], "(σ≈0 -> SUR-CONFIANT)")
    print("   ", formule(propage_mc(lambda x: x * x, [(0.0, 1.0)]), "mc"))
