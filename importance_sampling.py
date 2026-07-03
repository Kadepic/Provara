"""
PALIER 2 — ÉCHANTILLONNAGE PRÉFÉRENTIEL & TAILLE EFFECTIVE D'ÉCHANTILLON (ESS) : ne pas faire confiance à un
estimateur dont les poids ont dégénéré (brique 78, 2026-06-27).

Pour estimer E_p[f(X)] sans pouvoir tirer selon p, on tire selon une proposition q et on PONDÈRE : E_p[f] = E_q[f·w]
avec w = p/q. L'estimateur (1/n)Σ f(xᵢ)wᵢ est SANS BIAIS. MAIS si q est mal adaptée à p, quelques poids ÉCRASENT tous
les autres : l'estimateur a une énorme variance, et — piège — dans un tirage typique on NE VOIT PAS le poids géant
rare, donc l'écart-type ESTIMÉ SOUS-ESTIME la vraie erreur → l'intervalle naïf SOUS-COUVRE = SUR-CONFIANCE.

LA TAILLE EFFECTIVE D'ÉCHANTILLON diagnostique la dégénérescence SANS connaître la vérité :
    ESS = (Σ wᵢ)² / Σ wᵢ²   ∈ [1, n].
ESS = n si tous les poids sont égaux ; ESS → 1 si un poids domine. ESS ≪ n = signal d'alarme : « n échantillons mais
l'information de quelques-uns seulement » → l'estimateur (et son erreur annoncée) ne sont pas fiables.

LE MODE D'ÉCHEC DÉMASQUÉ : faire confiance à l'IC naïf quand ESS ≪ n est sur-confiant ; la bonne attitude est de
S'ABSTENIR / avertir quand ESS/n est trop faible. Une bonne proposition (ESS ≈ n) rend l'IC fiable. ABSTENTION si
n<2 / poids négatifs. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
FIABLE = "fiable"
NON_FIABLE = "non_fiable"


def normal_pdf(x, mu, sigma):
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))


def poids(xs, p, q):
    """Poids d'importance wᵢ = p(xᵢ)/q(xᵢ). p, q = densités (callables)."""
    return [p(x) / q(x) for x in xs]


def estimateur(xs, f, w):
    """Estimateur d'importance SANS biais (1/n)Σ f(xᵢ)·wᵢ de E_p[f]."""
    return sum(f(x) * wi for x, wi in zip(xs, w)) / len(xs)


def ess(w):
    """Taille effective d'échantillon ESS = (Σw)²/Σw²."""
    s1 = sum(w); s2 = sum(wi * wi for wi in w)
    return (s1 * s1) / s2 if s2 > 0 else 0.0


def erreur_naive(xs, f, w):
    """Écart-type NAÏF de l'estimateur = √( Var(f·w) / n ) (sous-estime sous poids à queue lourde)."""
    n = len(xs)
    g = [f(x) * wi for x, wi in zip(xs, w)]
    m = sum(g) / n
    var = sum((gi - m) ** 2 for gi in g) / (n - 1)
    return math.sqrt(var / n)


def intervalle_naif(xs, f, w, z=1.96):
    mu = estimateur(xs, f, w); se = erreur_naive(xs, f, w)
    return (mu - z * se, mu + z * se)


def analyse(xs, f, p, q, seuil_ess=0.1):
    """Façade : estime E_p[f], diagnostique via l'ESS. (FIABLE/NON_FIABLE, {estime, ess, ratio, ic}) ou (ABSTENTION,…).
    Si ESS/n < seuil_ess → NON_FIABLE (avertir/abstenir plutôt que sur-confier)."""
    if len(xs) < 2:
        return (ABSTENTION, "n < 2")
    w = poids(xs, p, q)
    if any(wi < 0 for wi in w):
        return (ABSTENTION, "poids négatifs (densités invalides)")
    n = len(xs)
    e = ess(w); ratio = e / n
    statut = NON_FIABLE if ratio < seuil_ess else FIABLE
    return (statut, {"estime": estimateur(xs, f, w), "ess": e, "ratio": ratio,
                     "ic": intervalle_naif(xs, f, w)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Estimation impossible : {res[1]}."
    i = res[1]
    if res[0] == NON_FIABLE:
        return (f"⚠ ESS={i['ess']:.1f} ({100*i['ratio']:.0f}% de n) : poids dégénérés — l'estimation {i['estime']:.4f} et "
                f"son IC ne sont PAS fiables (sur-confiance si on les croit). Améliorer la proposition q.")
    return f"E_p[f] ≈ {i['estime']:.4f}, IC {tuple(round(v,4) for v in i['ic'])} (ESS={i['ess']:.0f}, fiable)."


if __name__ == "__main__":
    import random, statistics
    rng = random.Random(0)
    p = lambda x: normal_pdf(x, 0, 1)
    f = lambda x: x * x                       # E_p[x²] = 1
    print("=== ÉCHANTILLONNAGE PRÉFÉRENTIEL & ESS ===\n")
    for sig_q, lab in [(1.0, "q=p (idéale)"), (2.0, "q large (sûre, défensive)"), (0.7, "q à queue LÉGÈRE (piège)")]:
        q = lambda x, s=sig_q: normal_pdf(x, 0, s)
        ests, esss, ses = [], [], []
        for _ in range(400):
            xs = [rng.gauss(0, sig_q) for _ in range(200)]
            w = poids(xs, p, q)
            ests.append(estimateur(xs, f, w)); esss.append(ess(w)); ses.append(erreur_naive(xs, f, w))
        vrai_se = statistics.pstdev(ests)
        print(f"  {lab:28s}: ESS_moy={statistics.mean(esss):5.0f} ; vrai SE={vrai_se:.3f} ; SE naïf médian={statistics.median(ses):.3f}"
              f"  {'← SOUS-ESTIMÉ (sur-confiant)' if statistics.median(ses) < vrai_se*0.8 else ''}")
    # cas dégénéré explicite : un poids domine -> ESS ≈ 1 -> NON FIABLE
    xs = [rng.gauss(0, 0.45) for _ in range(200)]
    print("\n ", formule(analyse(xs, f, p, lambda x: normal_pdf(x, 0, 0.45))))
