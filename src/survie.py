"""
PALIER 2 — ANALYSE DE SURVIE / TEMPS-JUSQU'À-ÉVÉNEMENT sous CENSURE (Kaplan-Meier, brique 39, 2026-06-26).

« Combien de temps avant l'événement (panne, rechute, désabonnement, décès) — alors qu'à la fin de l'étude beaucoup
n'ont PAS encore eu l'événement ? » Ces observations sont CENSURÉES à droite : on sait seulement que la durée vraie
DÉPASSE l'instant d'observation. Les jeter ou les compter comme des événements MENT (sous-estime la survie, sur-estime
le risque). L'estimateur de KAPLAN-MEIER les exploite honnêtement :

  à chaque instant d'événement t_i :  S(t_i) = S(t_{i−1}) · (1 − d_i / n_i)
  n_i = nombre ENCORE À RISQUE juste avant t_i (ni événement ni censuré avant) ; d_i = événements en t_i.
  Un censuré quitte le « risque » sans faire chuter la courbe → il contribue à n_i mais jamais à d_i.

INCERTITUDE : variance de GREENWOOD  Var(S(t)) = S(t)²·Σ d_i/(n_i(n_i−d_i)), avec IC par transformation
complémentaire log-log (reste dans (0,1), meilleure couverture en petite taille). INVARIANT (jugé par calibration.py) :
sur une loi connue (exponentielle + censure indépendante), l'IC de S(t) couvre la VRAIE survie ~confiance, là où le
naïf (censuré = événement) est SUR-CONFIANT (biaisé bas). En prime D-CALIBRATION : pour un modèle bien spécifié,
S(T_i) aux instants d'événement est ~UNIFORME(0,1). ABSTENTION si trop peu d'événements. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_EVENTS = 15


def _invnorm(p: float) -> float:
    """Quantile de la loi normale standard (Acklam). p dans (0,1)."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p hors (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _z(confiance: float) -> float:
    return _invnorm(1.0 - (1.0 - confiance) / 2.0)


def kaplan_meier(temps, evenement):
    """Estime la courbe de survie KM. `evenement` : 1 = événement observé, 0 = censuré à droite.
    Renvoie un dict {temps, S, V, n, d} aux instants d'ÉVÉNEMENT (S juste APRÈS t_i, V = somme de Greenwood),
    ou None si aucun événement."""
    obs = sorted((float(t), int(e)) for t, e in zip(temps, evenement))
    n_total = len(obs)
    if n_total == 0:
        return None
    # instants d'événement distincts
    inst = sorted({t for t, e in obs if e == 1})
    if not inst:
        return None
    out = {"temps": [], "S": [], "V": [], "n": [], "d": []}
    S = 1.0
    Vsum = 0.0
    for ti in inst:
        n_i = sum(1 for t, _ in obs if t >= ti)            # à risque juste avant t_i
        d_i = sum(1 for t, e in obs if t == ti and e == 1)
        if n_i <= 0:
            continue
        S *= (1.0 - d_i / n_i)
        if n_i > d_i:
            Vsum += d_i / (n_i * (n_i - d_i))
        out["temps"].append(ti); out["S"].append(S)
        out["V"].append(Vsum); out["n"].append(n_i); out["d"].append(d_i)
    return out if out["temps"] else None


def survie_a(km, t: float) -> float:
    """S(t) : fonction en escalier (continue à droite). S=1 avant le 1er événement."""
    if km is None:
        return float("nan")
    S = 1.0
    for ti, Si in zip(km["temps"], km["S"]):
        if ti <= t:
            S = Si
        else:
            break
    return S


def _greenwood_at(km, t: float):
    """Renvoie (S(t), V(t)) où V est la somme de Greenwood cumulée jusqu'à t."""
    S, V = 1.0, 0.0
    for ti, Si, Vi in zip(km["temps"], km["S"], km["V"]):
        if ti <= t:
            S, V = Si, Vi
        else:
            break
    return S, V


def mediane(km):
    """Survie médiane : plus petit instant d'événement où S <= 0.5. None si la courbe ne descend pas à 0.5."""
    if km is None:
        return None
    for ti, Si in zip(km["temps"], km["S"]):
        if Si <= 0.5:
            return ti
    return None


def km_avec_ic(temps, evenement, t: float, confiance: float = 0.95):
    """S(t) + IC par Greenwood/complémentaire-log-log. Renvoie (ESTIMATION, (S, (bas, haut)), confiance)
    ou (ABSTENTION, None, raison)."""
    n_ev = sum(1 for e in evenement if int(e) == 1)
    if n_ev < N_MIN_EVENTS:
        return (ABSTENTION, None, f"trop peu d'événements (D={n_ev} < {N_MIN_EVENTS})")
    km = kaplan_meier(temps, evenement)
    if km is None:
        return (ABSTENTION, None, "aucun événement observé")
    S, V = _greenwood_at(km, t)
    if S >= 1.0 or S <= 0.0:
        # courbe non informative en t (avant le 1er événement ou déjà à 0) -> IC dégénéré honnête
        return (ESTIMATION, (S, (S, S)), confiance)
    z = _z(confiance)
    logS = math.log(S)
    se_cll = math.sqrt(V) / abs(logS)        # écart-type de log(−log S)
    bas = S ** math.exp(z * se_cll)          # transformation monotone décroissante -> +z donne la borne basse
    haut = S ** math.exp(-z * se_cll)
    return (ESTIMATION, (S, (max(0.0, bas), min(1.0, haut))), confiance)


def km_naif_a(temps, evenement, t: float) -> float:
    """Estimateur NAÏF qui IGNORE la censure (compte tout le monde comme événement) : S(t) = P(durée observée > t).
    Biaisé BAS (sur-estime le risque) — sert à démasquer l'erreur que KM corrige."""
    xs = [float(x) for x in temps]
    n = len(xs)
    if n == 0:
        return float("nan")
    return sum(1 for x in xs if x > t) / n


def d_calibration(temps, evenement, S_pred, n_bins: int = 10):
    """D-CALIBRATION (Haider et al.) : pour un modèle bien spécifié, les déciles de S_pred sont ~ÉQUI-occupés.
    `S_pred` : callable t -> S(t). Un ÉVÉNEMENT en T_i compte 1 dans le décile de S_pred(T_i) ; un CENSURÉ en C_i
    (on sait seulement que la survie vraie < S_pred(C_i)) étale UNE unité de masse UNIFORMÉMENT sur [0, S_pred(C_i)].
    Sans ce traitement, ne garder que les événements biaiserait vers S≈1 (les durées courtes sont sur-observées).
    Renvoie (occupations_deciles, stat_chi2) ; chi2 faible = uniforme = D-calibré."""
    occ = [0.0] * n_bins
    m = 0
    for t, e in zip(temps, evenement):
        s = min(1.0, max(0.0, S_pred(float(t))))
        m += 1
        if int(e) == 1:
            b = min(n_bins - 1, max(0, int(s * n_bins)))
            occ[b] += 1.0
        elif s <= 0.0:
            occ[0] += 1.0
        else:
            for b in range(n_bins):
                lo, hi = b / n_bins, (b + 1) / n_bins
                ov = min(hi, s) - lo
                if ov > 0:
                    occ[b] += ov / s
    if m == 0:
        return ([0.0] * n_bins, float("inf"))
    att = m / n_bins
    chi2 = sum((o - att) ** 2 / att for o in occ)
    return (occ, chi2)


def formule(res, t: float) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer la survie en t={t} : {res[2]}."
    S, (bas, haut) = res[1][0], res[1][1]
    conf = res[2]
    return (f"Probabilité de « survie » au-delà de t={t} ≈ {S:.1%} (à {round(conf*100)}% entre {bas:.1%} et "
            f"{haut:.1%}). Censure prise en compte — l'estimateur naïf, lui, sous-estimerait cette probabilité.")


if __name__ == "__main__":
    import random
    print("=== ANALYSE DE SURVIE (Kaplan-Meier sous censure) ===\n")
    rng = random.Random(0)
    LAM, MU = 0.5, 0.3        # durée vraie ~Exp(0.5) ; censure ~Exp(0.3) indépendante
    temps, evt = [], []
    for _ in range(500):
        tv = -math.log(1 - rng.random()) / LAM
        c = -math.log(1 - rng.random()) / MU
        temps.append(min(tv, c)); evt.append(1 if tv <= c else 0)
    km = kaplan_meier(temps, evt)
    for t in (0.5, 1.0, 2.0):
        vrai = math.exp(-LAM * t)
        res = km_avec_ic(temps, evt, t, 0.90)
        naif = km_naif_a(temps, evt, t)
        print(f"  t={t}: vrai S={vrai:.3f} | KM={survie_a(km, t):.3f} naïf={naif:.3f}")
        print("        ", formule(res, t))
    print(f"\n  médiane KM = {mediane(km)} (vraie médiane = {math.log(2)/LAM:.3f})")
    occ, chi2 = d_calibration(temps, evt, lambda t: math.exp(-LAM * t))
    print(f"  D-calibration (modèle vrai) déciles={occ} chi2={chi2:.2f} (faible = uniforme = calibré)")
