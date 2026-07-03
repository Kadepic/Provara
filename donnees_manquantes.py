"""
PALIER 2 — DONNÉES MANQUANTES : IMPUTATION MULTIPLE + RÈGLES DE RUBIN (brique 40, 2026-06-26).

« Une partie des valeurs manque (non au hasard : la probabilité de manquer dépend d'une covariable observée — MAR).
Quelle est la moyenne vraie, et avec quelle incertitude HONNÊTE ? » Deux pièges classiques :
  • CAS COMPLET (jeter les lignes incomplètes) → BIAISÉ sous MAR (les présents ne représentent pas la population).
  • IMPUTATION SIMPLE (remplir par la prédiction, une fois) → variance SOUS-ESTIMÉE : on traite des valeurs INVENTÉES
    comme certaines → intervalle trop étroit → SUR-CONFIANCE (la ligne rouge).

L'IMPUTATION MULTIPLE (Rubin) répare les deux : on complète m fois en TIRANT les valeurs manquantes de leur loi
prédictive (régression sur la covariable + bruit résiduel + incertitude des paramètres), on estime dans chaque jeu
complété, puis on combine :
  Q̄ = moyenne des estimations ;  W = variance intra moyenne ;  B = variance INTER (entre imputations)
  T = W + (1 + 1/m)·B          (T > W : l'incertitude d'imputation est AJOUTÉE, pas ignorée)
  df de Rubin = (m−1)·(1 + W/((1+1/m)·B))²        IC = Q̄ ± t_df · √T

INVARIANT (jugé par calibration.py) : sur une loi connue, l'IC de Rubin COUVRE la vraie moyenne ~confiance, là où
l'imputation simple SOUS-COUVRE (surconfiant) et le cas-complet est biaisé. ABSTENTION si trop peu d'observé. Pur Python.
"""
from __future__ import annotations

import math
import random

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_OBS = 15


def _invnorm(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p hors (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
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


def _t_quantile(p: float, df: float) -> float:
    """Quantile de Student (approx Cornish-Fisher sur le quantile normal). Suffisant pour df >= ~3."""
    z = _invnorm(p)
    if df > 1e6:
        return z
    g1 = (z ** 3 + z) / 4.0
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96.0
    g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384.0
    return z + g1 / df + g2 / df ** 2 + g3 / df ** 3


def _ols(xs, ys):
    """Régression simple y ~ a + b·x. Renvoie (a, b, sigma2_resid, x̄, Sxx) ou None."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    dof = max(1, n - 2)
    s2 = sum(r * r for r in resid) / dof
    return (a, b, s2, mx, sxx)


def cas_complet(x, y_obs):
    """Moyenne par CAS COMPLET (ignore les manquants). Biaisée sous MAR. Renvoie (moyenne, ic95) ou None."""
    ys = [y for y in y_obs if y is not None]
    n = len(ys)
    if n < N_MIN_OBS:
        return None
    m = sum(ys) / n
    s2 = sum((v - m) ** 2 for v in ys) / (n - 1)
    se = math.sqrt(s2 / n)
    z = _invnorm(0.975)
    return (m, (m - z * se, m + z * se))


def imputation_multiple(x, y_obs, m: int = 20, confiance: float = 0.95, seed: int = 0):
    """IMPUTATION MULTIPLE de la MOYENNE de y, manquants imputés par régression bayésienne sur x (paramètres tirés
    de leur loi + bruit résiduel). Combine par Rubin. Renvoie (ESTIMATION, (Q̄, (bas, haut)), confiance) ou ABSTENTION.
    `y_obs` : liste où None = manquant. `x` : covariable complète."""
    n = len(y_obs)
    # Cas dégénéré : AUCUN manquant -> l'imputation multiple est sans objet -> ABSTENTION honnête (la moyenne
    # empirique suffit). On le détecte par `None not in y_obs` (opérateur C, fiable). NB IMPORTANT : on évite ainsi
    # une boucle de comptage `for i in range(len(...))` sur une entrée tout-présent, qui sur CPython 3.12.3 est
    # mis-spécialisée (FOR_ITER_RANGE : itère trop peu, résultat faux déterministe perturbé par settrace/dis).
    # Avec au moins un manquant (chemin réel), tout est correct — vérifié cold == settrace.
    if None not in y_obs:
        return (ABSTENTION, None, "aucune valeur manquante — imputation multiple sans objet (moyenne empirique directe)")
    obs_idx, mis_idx = [], []
    for i in range(n):
        if y_obs[i] is None:
            mis_idx.append(i)
        else:
            obs_idx.append(i)
    if len(obs_idx) < N_MIN_OBS:
        return (ABSTENTION, None, f"trop peu d'observés ({len(obs_idx)} < {N_MIN_OBS})")
    xo, yo = [], []
    for i in obs_idx:
        xo.append(x[i]); yo.append(y_obs[i])
    fit = _ols(xo, yo)
    if fit is None:
        return (ABSTENTION, None, "régression d'imputation non estimable")
    a, b, s2, mx, sxx = fit
    n_o = len(obs_idx)
    rng = random.Random(seed)
    estimations, variances = [], []
    for _ in range(m):
        # 1) tirer sigma² puis (a,b) de leur loi a posteriori (imputation PROPRE, pas seulement la moyenne)
        chi = 0.0
        for _ in range(max(1, n_o - 2)):
            chi += rng.gauss(0, 1) ** 2
        sigma2 = s2 * (n_o - 2) / chi if chi > 0 else s2
        sigma = math.sqrt(sigma2)
        b_star = b + rng.gauss(0, 1) * sigma / math.sqrt(sxx)
        a_star = a + rng.gauss(0, 1) * sigma * math.sqrt(1.0 / n_o + mx * mx / sxx) - mx * (b_star - b)
        # 2) compléter
        comp = list(y_obs)
        for i in mis_idx:
            comp[i] = a_star + b_star * x[i] + rng.gauss(0, sigma)
        mu = sum(comp) / n
        acc = 0.0
        for v in comp:
            acc += (v - mu) ** 2
        estimations.append(mu)
        variances.append((acc / (n - 1)) / n)            # variance intra de la moyenne
    qbar = sum(estimations) / m
    w = sum(variances) / m
    if m > 1:
        accb = 0.0
        for e in estimations:
            accb += (e - qbar) ** 2
        bvar = accb / (m - 1)
    else:
        bvar = 0.0
    tvar = w + (1 + 1.0 / m) * bvar
    if bvar > 0:
        df = (m - 1) * (1 + w / ((1 + 1.0 / m) * bvar)) ** 2
    else:
        df = 1e9
    tq = _t_quantile(1 - (1 - confiance) / 2, df)
    demi = tq * math.sqrt(tvar)
    return (ESTIMATION, (qbar, (qbar - demi, qbar + demi)), confiance)


def imputation_simple(x, y_obs, confiance: float = 0.95):
    """IMPUTATION SIMPLE (déterministe, une fois) : manquants = prédiction de régression, SANS bruit ni incertitude
    d'imputation → variance sous-estimée → SUR-CONFIANCE. Sert à démasquer le piège. Renvoie (moyenne, ic) ou None."""
    obs_idx = [i for i, y in enumerate(y_obs) if y is not None]
    mis_idx = [i for i, y in enumerate(y_obs) if y is None]
    if len(obs_idx) < N_MIN_OBS:
        return None
    fit = _ols([x[i] for i in obs_idx], [y_obs[i] for i in obs_idx])
    if fit is None:
        return None
    a, b, _s2, _mx, _sxx = fit
    comp = list(y_obs)
    for i in mis_idx:
        comp[i] = a + b * x[i]
    n = len(comp)
    mu = sum(comp) / n
    s2 = sum((v - mu) ** 2 for v in comp) / (n - 1)
    se = math.sqrt(s2 / n)                  # traite les imputés comme de vraies données -> trop optimiste
    z = _invnorm(1 - (1 - confiance) / 2)
    return (mu, (mu - z * se, mu + z * se))


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas estimer la moyenne : {res[2]}."
    q, (bas, haut), conf = res[1][0], res[1][1], res[2]
    return (f"Moyenne estimée ≈ {q:.3f} (à {round(conf*100)}% entre {bas:.3f} et {haut:.3f}). L'incertitude des "
            f"valeurs manquantes est INCLUSE — une imputation simple sous-estimerait cet intervalle.")


if __name__ == "__main__":
    print("=== DONNÉES MANQUANTES : imputation multiple + Rubin ===\n")
    rng = random.Random(0)
    A, B = 1.0, 2.0      # y = 1 + 2x + bruit ; x ~ U(0,1) ; vraie moyenne(y) = 1 + 2*0.5 = 2.0
    x, y = [], []
    for _ in range(300):
        xi = rng.random()
        x.append(xi); y.append(A + B * xi + rng.gauss(0, 0.5))
    # MAR : manque d'autant plus que x est grand
    y_obs = [yi if rng.random() > 0.2 + 0.5 * xi else None for xi, yi in zip(x, y)]
    print(f"  manquants : {sum(1 for v in y_obs if v is None)}/{len(y_obs)} ; vraie moyenne ≈ 2.0")
    cc = cas_complet(x, y_obs)
    si = imputation_simple(x, y_obs)
    mi = imputation_multiple(x, y_obs, m=20)
    print(f"  cas complet      : moy={cc[0]:.3f} IC=({cc[1][0]:.3f},{cc[1][1]:.3f})  [biaisé bas sous MAR]")
    print(f"  imputation simple: moy={si[0]:.3f} IC=({si[1][0]:.3f},{si[1][1]:.3f})  [IC trop étroit]")
    print(f"  imputation MULTI : ", formule(mi))
