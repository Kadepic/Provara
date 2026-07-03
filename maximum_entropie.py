"""
PALIER 2 — PRINCIPE DU MAXIMUM D'ENTROPIE (Jaynes) : la distribution la MOINS engagée compatible avec ce qu'on sait
(brique 80, 2026-06-27).

Quand on ne connaît qu'une information PARTIELLE (le support, une moyenne, une variance…), quelle loi adopter ? Toute
loi PLUS structurée/piquée qu'il ne le faut INJECTE de l'information qu'on n'a pas = SUR-CONFIANCE. Le principe de
JAYNES : choisir la loi de plus grande ENTROPIE H(p)=−Σ pᵢ ln pᵢ parmi celles qui respectent les contraintes connues.
C'est la loi qui assume STRICTEMENT le donné et rien de plus.
  • support seul → UNIFORME (entropie maximale ln K).
  • moyenne E[f]=μ imposée → famille EXPONENTIELLE  pᵢ ∝ exp(λ·fᵢ)  (λ réglé pour atteindre μ).

LE MODE D'ÉCHEC DÉMASQUÉ : adopter une loi de PLUS FAIBLE entropie compatible avec les contraintes (plus « sûre »)
assigne ~0 à des issues possibles → log-loss catastrophique quand elles surviennent (sur-confiance punie), alors que la
maxent garde une probabilité positive partout (honnête). Chaque contrainte ajoutée RÉDUIT l'entropie (= information
gagnée) ; à la limite (μ extrême) l'entropie → 0. ABSTENTION si μ hors [min f, max f]. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
MAXENT = "maxent"


def entropie(p):
    """Entropie de Shannon H(p) = −Σ pᵢ ln pᵢ (0·ln0 = 0)."""
    return -sum(pi * math.log(pi) for pi in p if pi > 0)


def uniforme(K):
    """Maxent sans contrainte (support seul) : uniforme, entropie ln K."""
    return [1.0 / K] * K


def _distrib_lambda(fs, lam):
    """pᵢ ∝ exp(λ fᵢ) (softmax stable)."""
    m = max(lam * f for f in fs)
    w = [math.exp(lam * f - m) for f in fs]
    z = sum(w)
    return [wi / z for wi in w]


def _moyenne(p, fs):
    return sum(pi * f for pi, f in zip(p, fs))


def maxent_moyenne(fs, mu, tol=1e-12):
    """Maxent sous contrainte E[f]=μ : pᵢ ∝ exp(λ fᵢ), λ trouvé par bisection (E_λ[f] croît avec λ)."""
    lo, hi = -200.0, 200.0
    for _ in range(200):
        lam = (lo + hi) / 2
        if _moyenne(_distrib_lambda(fs, lam), fs) < mu:
            lo = lam
        else:
            hi = lam
        if hi - lo < tol:
            break
    return _distrib_lambda(fs, (lo + hi) / 2)


def deux_points(fs, mu):
    """Loi à DEUX points (extrêmes) respectant E[f]=μ : entropie faible, assigne 0 aux issues du milieu (sur-confiant)."""
    fmin, fmax = min(fs), max(fs)
    w = (mu - fmin) / (fmax - fmin)
    imin, imax = fs.index(fmin), fs.index(fmax)
    p = [0.0] * len(fs)
    p[imin] += 1 - w; p[imax] += w
    return p


def analyse(fs, mu=None):
    """Façade : maxent (uniforme si mu=None, exponentielle sinon). (MAXENT, {p, entropie, mu}) ou (ABSTENTION, raison)."""
    if not fs:
        return (ABSTENTION, "support vide")
    if mu is None:
        p = uniforme(len(fs))
    else:
        if not (min(fs) <= mu <= max(fs)):
            return (ABSTENTION, f"μ={mu} hors [{min(fs)}, {max(fs)}]")
        p = maxent_moyenne(fs, mu)
    return (MAXENT, {"p": p, "entropie": entropie(p), "mu": mu})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de maxent : {res[1]}."
    i = res[1]
    base = "uniforme (support seul)" if i["mu"] is None else f"exponentielle (E[f]={i['mu']})"
    return (f"Loi de maximum d'entropie {base} : H={i['entropie']:.3f}. Adopter une loi plus piquée injecterait une "
            f"information non justifiée (sur-confiance).")


if __name__ == "__main__":
    print("=== MAXIMUM D'ENTROPIE (Jaynes) ===\n")
    fs = [0, 1, 2, 3, 4, 5]
    print(f"  Support seul (K=6) → uniforme, H={entropie(uniforme(6)):.3f} (= ln 6 = {math.log(6):.3f})")
    for mu in (2.5, 3.5, 4.5):
        p = maxent_moyenne(fs, mu)
        print(f"  E[f]={mu} → maxent p={[round(x,3) for x in p]}, H={entropie(p):.3f}, moyenne réelle={_moyenne(p,fs):.3f}")
    p_me = maxent_moyenne(fs, 3.5); p_2pt = deux_points(fs, 3.5)
    print(f"\n  À E[f]=3.5 : maxent H={entropie(p_me):.3f} ; loi 2-points H={entropie(p_2pt):.3f} (plus faible = sur-confiante, assigne 0 au milieu)")
    print(" ", formule(analyse(fs, 3.5)))
