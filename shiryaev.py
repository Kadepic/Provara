"""
PALIER 2 — DÉTECTION AU PLUS TÔT (Shiryaev, quickest detection bayésienne) : déclarer un changement avec une fausse
alarme CONTRÔLÉE (brique 67, 2026-06-27).

Un flux passe d'un régime f0 à un régime f1 à un instant de changement τ INCONNU (prior géométrique : à chaque pas,
probabilité ρ de basculer). On veut détecter le changement VITE, mais sans crier au loup. La procédure de Shiryaev
maintient la probabilité a posteriori que le changement a DÉJÀ eu lieu :
    p̃ₜ = p_{t-1} + (1−p_{t-1})·ρ        (prédiction : on a pu changer à t)
    Λₜ = f1(xₜ)/f0(xₜ)                   (rapport de vraisemblance)
    pₜ = p̃ₜΛₜ / ( p̃ₜΛₜ + (1−p̃ₜ) )       (mise à jour bayésienne)
On ALARME au premier t où pₜ ≥ A. Garantie : à l'alarme, P(fausse alarme) = E[1−p_T] ≤ 1−A. Donc **A = 1−α contrôle
exactement le taux de fausse alarme** (distinct du changepoint RÉTROSPECTIF [[changepoint]] qui localise a posteriori).

LE MODE D'ÉCHEC DÉMASQUÉ : un détecteur NAÏF (alarmer dès qu'une observation est « surprenante » sous f0, ex.
|x|>seuil) a un taux de fausse alarme INCONTRÔLÉ et bien supérieur au nominal — il est SUR-CONFIANT (les surprises
ponctuelles s'accumulent). La probabilité a posteriori pₜ de Shiryaev est CALIBRÉE : alarmer à pₜ≥1−α garantit
P(fausse alarme) ≤ α. Compromis : A↑ ⇒ moins de fausses alarmes mais délai de détection plus long. ABSTENTION si
données vides / ρ∉(0,1) / A∉(0,1). Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
DETECTION = "detection"


def gaussienne(mu, sigma=1.0):
    """Densité normale N(mu, sigma²)."""
    c = 1.0 / (sigma * math.sqrt(2 * math.pi))
    return lambda x: c * math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def posteriors(xs, f0, f1, rho, p0=0.0):
    """Suite des probabilités a posteriori pₜ = P(τ ≤ t | x₁..xₜ) (récursion de Shiryaev)."""
    p = p0
    out = []
    for x in xs:
        p_pred = p + (1 - p) * rho
        d0 = f0(x)
        lam = (f1(x) / d0) if d0 > 0 else float("inf")
        num = p_pred * lam
        p = num / (num + (1 - p_pred)) if math.isfinite(num) else 1.0
        out.append(p)
    return out


def detecte(xs, f0, f1, rho, A, p0=0.0):
    """Premier instant (1-indexé) où pₜ ≥ A, ou None si jamais. (Le seuil A=1−α contrôle la fausse alarme.)"""
    p = p0
    for t, x in enumerate(xs, 1):
        p_pred = p + (1 - p) * rho
        d0 = f0(x)
        lam = (f1(x) / d0) if d0 > 0 else float("inf")
        num = p_pred * lam
        p = num / (num + (1 - p_pred)) if math.isfinite(num) else 1.0
        if p >= A:
            return t
    return None


def seuil_pour_alpha(alpha):
    """Seuil A = 1−α garantissant un taux de fausse alarme ≤ α."""
    return 1.0 - alpha


def analyse(xs, f0, f1, rho, alpha=0.05, p0=0.0):
    """Façade : (DETECTION, {alarme, A, posteriors}) ou (ABSTENTION, raison). alarme=None si pas de détection."""
    if not xs or not (0 < rho < 1) or not (0 < alpha < 1):
        return (ABSTENTION, "données vides / ρ∉(0,1) / α∉(0,1)")
    A = seuil_pour_alpha(alpha)
    ps = posteriors(xs, f0, f1, rho, p0)
    alarme = next((t for t, p in enumerate(ps, 1) if p >= A), None)
    return (DETECTION, {"alarme": alarme, "A": A, "posteriors": ps})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Détection impossible : {res[1]}."
    info = res[1]
    if info["alarme"] is None:
        return f"Aucun changement détecté (posterior max {max(info['posteriors']):.3f} < seuil {info['A']:.3f})."
    return (f"Changement détecté à t={info['alarme']} (posterior ≥ {info['A']:.3f}). Taux de fausse alarme garanti "
            f"≤ {1-info['A']:.3f}. Alarmer sur une simple observation surprenante serait sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    f0, f1, rho = gaussienne(0, 1), gaussienne(1.5, 1), 0.01
    print("=== DÉTECTION AU PLUS TÔT (Shiryaev) ===\n")
    tau = 80
    xs = [rng.gauss(0, 1) for _ in range(tau)] + [rng.gauss(1.5, 1) for _ in range(60)]
    for alpha in (0.20, 0.05, 0.01):
        st, info = analyse(xs, f0, f1, rho, alpha)
        a = info["alarme"]
        print(f"  α={alpha:>4} (A={info['A']:.2f}) : alarme à t={a} (vrai τ={tau}, délai={a-tau if a else '—'})")
    print(" ", formule(analyse(xs, f0, f1, rho, 0.05)))
