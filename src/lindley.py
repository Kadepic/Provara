"""
PALIER 2 — PARADOXE DE LINDLEY : un seuil de signification α FIXE est sur-confiant à grand n (brique 100, 2026-06-27).

Tester H0: θ=0 vs H1: θ≠0 avec un seuil α fixe (« p < 0.05 ⇒ on rejette H0 ») traite p comme une mesure de preuve
CONSTANTE. C'est SUR-CONFIANT : à p=0.05 FIXE (z≈1.96), quand la taille d'échantillon n grandit, l'effet estimé
x̄ = z·σ/√n → 0 — l'écart à H0 est de plus en plus NÉGLIGEABLE. Le facteur de Bayes B01 (H0 vs H1, prior diffus θ~N(0,τ²)
sous H1) CROÎT alors vers l'infini : la donnée soutient de plus en plus H0. Donc à un même p=0.05 :
  • le fréquentiste REJETTE H0 (résultat « significatif ») ;
  • le bayésien SOUTIENT H0 (B01 ≫ 1).
Les deux divergent — et le seuil fixe est du mauvais côté. La signification probante d'un p DÉPEND de n ; un p=0.05 sur
un million d'observations est une preuve FAIBLE (voire pro-H0), pas la même qu'un p=0.05 sur trente.

LA CORRECTION — rapporter le FACTEUR DE BAYES (ou un seuil α qui se resserre avec n, type BIC) plutôt qu'un α fixe.

DISTINCT de l'inférence anytime-valide (brique 35 : peeking séquentiel) et du p-hacking (brique 98 : multiplicité) — ici
un TEST UNIQUE, un SEUIL FIXE, sans peeking ni sélection : le problème est la dépendance à n de la preuve.

LE MODE D'ÉCHEC DÉMASQUÉ : « p<α ⇒ preuve contre H0 » est sur-confiant à grand n ; le facteur de Bayes recalibre.
ABSTENTION si données incohérentes. Pur Python (probit Acklam, pas de MC requis).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"
_SQRT2 = math.sqrt(2.0)


def _Phi(z):
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


def probit(p):
    """Quantile normal standard Φ⁻¹(p) (algorithme d'Acklam, précision ~1e-9)."""
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
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def z_pour_p(p):
    """Statistique z bilatérale correspondant à une p-value p (z tel que 2(1−Φ(z))=p)."""
    return probit(1 - p / 2)


def facteur_bayes_01(z, n, sigma=1.0, tau=1.0):
    """Facteur de Bayes B01 = p(donnée|H0)/p(donnée|H1), prior θ~N(0,τ²) sous H1, pour un z et une taille n donnés.
    B01 > 1 ⇒ la donnée soutient H0. À z fixe, B01 croît avec n (paradoxe de Lindley)."""
    v0 = sigma ** 2 / n                 # variance de x̄ sous H0
    v1 = v0 + tau ** 2                  # variance marginale de x̄ sous H1 (prior diffus)
    return math.sqrt(v1 / v0) * math.exp(-(z ** 2 / 2.0) * (1.0 - v0 / v1))


def posterior_h0(z, n, sigma=1.0, tau=1.0, prior_h0=0.5):
    """P(H0 | donnée) = 1 / (1 + (prior_h1/prior_h0)/B01)."""
    b01 = facteur_bayes_01(z, n, sigma, tau)
    cote = (prior_h0 / (1 - prior_h0)) * b01      # cote a posteriori en faveur de H0
    return cote / (1.0 + cote)


def analyse(p, n, sigma=1.0, tau=1.0, prior_h0=0.5, alpha=0.05):
    """Façade : à une p-value p et une taille n, confronte le verdict fréquentiste (seuil α) et le bayésien.
    (ANALYSE, {z, p, n, alpha, B01, post_h0, rejette_freq, soutient_h0_bayes}) ou (ABSTENTION, raison)."""
    if not (0.0 < p < 1.0) or n < 1:
        return (ABSTENTION, "p hors ]0,1[ ou n < 1")
    z = z_pour_p(p)
    b01 = facteur_bayes_01(z, n, sigma, tau)
    post = posterior_h0(z, n, sigma, tau, prior_h0)
    return (ANALYSE, {"z": z, "p": p, "n": n, "alpha": alpha, "B01": b01, "post_h0": post,
                      "rejette_freq": p <= alpha, "soutient_h0_bayes": b01 > 1.0})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    div = "DIVERGENCE (Lindley)" if (i["rejette_freq"] and i["soutient_h0_bayes"]) else "accord"
    return (f"p={i['p']:.3f} sur n={i['n']} : fréquentiste {'REJETTE' if i['rejette_freq'] else 'ne rejette pas'} H0 ; "
            f"facteur de Bayes B01={i['B01']:.2f} (P(H0|donnée)={i['post_h0']:.2f}) {'soutient' if i['soutient_h0_bayes'] else 'défavorise'} "
            f"H0 → {div}. Un seuil α fixe est sur-confiant : la preuve d'un même p dépend de n.")


if __name__ == "__main__":
    print("=== PARADOXE DE LINDLEY (p=0.05 fixe, n croissant) ===\n")
    p = 0.05
    print(f"  z pour p=0.05 : {z_pour_p(p):.3f}")
    for n in (30, 1000, 100000, 10000000):
        st, info = analyse(p, n)
        print(f"  n={n:>9} : B01={info['B01']:8.2f}  P(H0|donnée)={info['post_h0']:.3f}  | {formule((st, info)).split('→')[-1].strip()}")
