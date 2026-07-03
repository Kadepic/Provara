"""
PALIER 2 — FILTRE DE KALMAN ROBUSTE : un filtre qui SOUS-ESTIME sa propre erreur est sur-confiant (brique 64,
2026-06-27).

Le filtre de Kalman est l'estimateur d'état optimal SI les covariances de bruit (processus q, mesure r) sont EXACTES.
En pratique elles sont mal connues. Si on les SOUS-ESTIME, le filtre rapporte une variance d'erreur P plus petite que
l'erreur réelle → ses intervalles de crédibilité SOUS-COUVRENT : c'est de la sur-confiance (et, à l'extrême, la
« divergence du filtre »). L'invariant T2 (calibration) est exactement : la variance ANNONCÉE doit égaler l'erreur
RÉELLE.

DÉTECTEUR SANS VÉRITÉ-TERRAIN — le NIS (Normalized Innovation Squared) : l'innovation νₜ = yₜ − x̂⁻ₜ a une variance
THÉORIQUE Sₜ = P⁻ₜ + r. Sous bonne spécification, νₜ²/Sₜ ~ χ²(1), donc E[ν²/S] = 1. Si le filtre est SUR-CONFIANT
(S trop petit), les innovations sont plus grandes qu'attendu → NIS moyen > 1. **On détecte la sur-confiance depuis les
seules données**, sans connaître la vérité.

LA RÉPARATION — inflation de covariance (mémoire qui s'efface, facteur λ≥1) : P⁻ ← λ·(a²P + q). Élargit P et S →
intervalles plus prudents → restaure la couverture et ramène le NIS vers 1. Trop d'inflation = sous-confiance (l'autre
excès). ABSTENTION si q<0, r≤0 ou pas de données. Pur Python (état scalaire, mesure directe H=1).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
COHERENT = "coherent"
SURCONFIANT = "surconfiant"
SOUSCONFIANT = "sousconfiant"


def filtre(ys, a, q, r, x0=0.0, P0=1.0, inflation=1.0):
    """Filtre de Kalman scalaire (x_{t+1}=a x+w, y=x+v). `inflation` λ≥1 = mémoire qui s'efface (robustesse).
    Renvoie dict {est, var, innov, S} (estimés x̂ₜ, variances Pₜ, innovations νₜ, variances d'innovation Sₜ)."""
    xhat, P = x0, P0
    est, var, innov, S = [], [], [], []
    for y in ys:
        xm = a * xhat                       # prédiction état
        Pm = inflation * (a * a * P + q)    # prédiction variance (inflée)
        nu = y - xm                         # innovation
        Sk = Pm + r                         # variance d'innovation
        K = Pm / Sk                         # gain de Kalman
        xhat = xm + K * nu                  # mise à jour état
        P = (1 - K) * Pm                    # mise à jour variance
        est.append(xhat); var.append(P); innov.append(nu); S.append(Sk)
    return {"est": est, "var": var, "innov": innov, "S": S}


def nis_moyen(res):
    """NIS moyen = moyenne de νₜ²/Sₜ. ≈ 1 si cohérent ; > 1 = SUR-confiant (innovations trop grandes pour S annoncé)."""
    innov, S = res["innov"], res["S"]
    return sum(nu * nu / s for nu, s in zip(innov, S)) / len(innov)


def diagnostic(res, alpha=0.05):
    """Verdict de cohérence du filtre à partir du NIS (test, sans vérité-terrain). n·NIS ~ χ²(n) → approx normale
    Var(NIS)=2/n. Renvoie (verdict, nis). SUR-confiant prioritaire (ligne rouge T2)."""
    n = len(res["innov"])
    nis = nis_moyen(res)
    seuil = math.sqrt(2.0 / n) * 1.96
    if nis > 1 + seuil:
        return (SURCONFIANT, nis)
    if nis < 1 - seuil:
        return (SOUSCONFIANT, nis)
    return (COHERENT, nis)


def steady_state_P(a, q, r, inflation=1.0, iters=2000):
    """Variance d'erreur en régime permanent (point fixe de Riccati scalaire)."""
    P = q + r
    for _ in range(iters):
        Pm = inflation * (a * a * P + q)
        K = Pm / (Pm + r)
        P = (1 - K) * Pm
    return P


def inflation_pour_coherence(res_innov_brut, a, q, r, cible_nis=1.0):
    """Heuristique : facteur d'inflation qui ramènerait le NIS observé vers `cible_nis` (∝ NIS observé)."""
    nis = res_innov_brut
    return max(1.0, nis / cible_nis)


def analyse(ys, a, q, r, x0=0.0, P0=1.0, inflation=1.0):
    """Façade : filtre + diagnostic. (verdict, {est, var, nis}) ou (ABSTENTION, raison)."""
    if not ys or q < 0 or r <= 0 or P0 <= 0:
        return (ABSTENTION, "données vides ou covariances invalides (q<0 / r≤0 / P0≤0)")
    res = filtre(ys, a, q, r, x0, P0, inflation)
    verdict, nis = diagnostic(res)
    return (verdict, {"est": res["est"], "var": res["var"], "nis": nis})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Filtrage impossible : {res[1]}."
    verdict, info = res[0], res[1]
    msg = {COHERENT: "le filtre est calibré (variance annoncée ≈ erreur réelle)",
           SURCONFIANT: "le filtre est SUR-CONFIANT (NIS>1 : il sous-estime son erreur — gonfler la covariance)",
           SOUSCONFIANT: "le filtre est sous-confiant (NIS<1 : intervalles trop larges)"}[verdict]
    return f"Diagnostic NIS={info['nis']:.2f} : {msg}."


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    a, q_true, r_true, T = 0.95, 1.0, 1.0, 4000
    x = 0.0; ys = []; xs = []
    for _ in range(T):
        x = a * x + rng.gauss(0, math.sqrt(q_true))
        ys.append(x + rng.gauss(0, math.sqrt(r_true))); xs.append(x)
    print("=== FILTRE DE KALMAN ROBUSTE — détecter/réparer la sur-confiance ===\n")
    for q_a, lab in [(1.0, "bien spécifié"), (0.05, "q sous-estimé (sur-confiant)")]:
        res = filtre(ys, a, q_a, r_true)
        cov = sum(1 for xt, e, v in zip(xs, res["est"], res["var"]) if abs(xt - e) <= 1.96 * math.sqrt(v)) / T
        verdict, nis = diagnostic(res)
        print(f"  q_assumé={q_a:>4} ({lab}): NIS={nis:.2f} [{verdict}], couverture 95%={cov:.3f}")
    # réparation par inflation
    res_robuste = filtre(ys, a, 0.05, r_true, inflation=3.0)
    cov_r = sum(1 for xt, e, v in zip(xs, res_robuste["est"], res_robuste["var"]) if abs(xt - e) <= 1.96 * math.sqrt(v)) / T
    print(f"  + inflation λ=3 : NIS={nis_moyen(res_robuste):.2f}, couverture 95%={cov_r:.3f} (restaurée)")
