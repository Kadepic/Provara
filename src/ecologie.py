"""
ÉCOLOGIE BORNÉE — écosystèmes & chaînes alimentaires : transfert d'énergie trophique + dynamique proies/prédateurs.

Même posture que `physique` / `maths_discretes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la formule écologique) est EXACT — c'est la garantie structurelle.
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête, qui efface le bruit binaire des flottants
    (10000·0.1² = 100.0000…1 -> 100.0) sans jamais inventer de précision.
  • ABSTENTION STRUCTURELLE : toute entrée hors domaine (niveau trophique < 1 ou non entier, énergie < 0,
    paramètre de Lotka-Volterra ≤ 0, abondance < 0) lève ValueError — JAMAIS un nombre faux.
  • déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

CE QUE ÇA COUVRE
  1. Règle des 10 % de Lindeman (efficacité écologique trophique) :
       energie_niveau(E0, n) = E0 · 0.1^(n−1)     (niveau 1 = producteur)
       Un producteur de 10000 J transmet ~1000 J au niveau 2, ~100 J au niveau 3, etc.
     efficacite_ecologique(E_sup, E_inf) = E_sup / E_inf   (rendement entre deux maillons consécutifs).

  2. Modèle proie–prédateur de Lotka–Volterra :
       dproie/dt      = α·proie − β·proie·predateur
       dpredateur/dt  = δ·proie·predateur − γ·predateur
     Point d'équilibre non trivial (les deux dérivées nulles) :
       proie*     = γ/δ
       predateur* = α/β
     α = taux de croissance des proies ; β = taux de prédation ; γ = mortalité des prédateurs ;
     δ = efficacité de conversion proie -> prédateur.
"""
from __future__ import annotations

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _est_entier(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


# ── 1) TRANSFERT D'ÉNERGIE TROPHIQUE (règle des 10 %) ─────────────────────────────────────────────────────────────
def energie_niveau(energie_base: float, niveau: int, efficacite: float = 0.1) -> float:
    """Énergie disponible au niveau trophique `niveau` (1 = producteur) en partant de `energie_base` au niveau 1.

    E(n) = energie_base · efficacite^(niveau−1). Par défaut efficacite = 0.1 (règle des 10 % de Lindeman).
    ABSTENTION : niveau non entier ou < 1, énergie_base < 0, efficacite hors ]0, 1].
    """
    if not _est_entier(niveau) or niveau < 1:
        raise ValueError("niveau trophique : entier ≥ 1 requis (1 = producteur)")
    if not _est_reel(energie_base) or energie_base < 0:
        raise ValueError("energie_base : réel ≥ 0 requis (énergie)")
    if not _est_reel(efficacite) or not (0 < efficacite <= 1):
        raise ValueError("efficacite : réel dans ]0, 1] requis")
    return _sig(energie_base * (efficacite ** (niveau - 1)))


def efficacite_ecologique(e_niveau_sup: float, e_niveau_inf: float) -> float:
    """Rendement écologique entre deux maillons consécutifs : E_supérieur / E_inférieur (≈ 0.1 attendu).

    ABSTENTION : E_inférieur ≤ 0 (division impossible / niveau vide), E_supérieur < 0.
    """
    if not _est_reel(e_niveau_inf) or e_niveau_inf <= 0:
        raise ValueError("e_niveau_inf : réel > 0 requis (niveau inférieur)")
    if not _est_reel(e_niveau_sup) or e_niveau_sup < 0:
        raise ValueError("e_niveau_sup : réel ≥ 0 requis")
    return _sig(e_niveau_sup / e_niveau_inf)


# ── 2) MODÈLE PROIE–PRÉDATEUR DE LOTKA–VOLTERRA ───────────────────────────────────────────────────────────────────
def _garde_params(alpha: float, beta: float, gamma: float, delta: float) -> None:
    for nom, v in (("alpha", alpha), ("beta", beta), ("gamma", gamma), ("delta", delta)):
        if not _est_reel(v) or v <= 0:
            raise ValueError(f"{nom} : réel > 0 requis (paramètre de Lotka-Volterra)")


def _garde_abondance(proie: float, predateur: float) -> None:
    for nom, v in (("proie", proie), ("predateur", predateur)):
        if not _est_reel(v) or v < 0:
            raise ValueError(f"{nom} : réel ≥ 0 requis (abondance)")


def derivee_proie(alpha: float, beta: float, proie: float, predateur: float) -> float:
    """dproie/dt = α·proie − β·proie·predateur. ABSTENTION : α,β ≤ 0 ; proie, predateur < 0."""
    if not _est_reel(alpha) or alpha <= 0:
        raise ValueError("alpha : réel > 0 requis")
    if not _est_reel(beta) or beta <= 0:
        raise ValueError("beta : réel > 0 requis")
    _garde_abondance(proie, predateur)
    return _sig(alpha * proie - beta * proie * predateur)


def derivee_predateur(gamma: float, delta: float, proie: float, predateur: float) -> float:
    """dpredateur/dt = δ·proie·predateur − γ·predateur. ABSTENTION : γ,δ ≤ 0 ; proie, predateur < 0."""
    if not _est_reel(gamma) or gamma <= 0:
        raise ValueError("gamma : réel > 0 requis")
    if not _est_reel(delta) or delta <= 0:
        raise ValueError("delta : réel > 0 requis")
    _garde_abondance(proie, predateur)
    return _sig(delta * proie * predateur - gamma * predateur)


def equilibre_lotka_volterra(alpha: float, beta: float, gamma: float, delta: float):
    """Point d'équilibre non trivial (proie*, predateur*) = (γ/δ, α/β). ABSTENTION : tout paramètre ≤ 0."""
    _garde_params(alpha, beta, gamma, delta)
    return (_sig(gamma / delta), _sig(alpha / beta))


def proie_equilibre(alpha: float, beta: float, gamma: float, delta: float) -> float:
    """Abondance d'équilibre des proies : proie* = γ/δ. ABSTENTION : tout paramètre ≤ 0."""
    _garde_params(alpha, beta, gamma, delta)
    return _sig(gamma / delta)


def predateur_equilibre(alpha: float, beta: float, gamma: float, delta: float) -> float:
    """Abondance d'équilibre des prédateurs : predateur* = α/β. ABSTENTION : tout paramètre ≤ 0."""
    _garde_params(alpha, beta, gamma, delta)
    return _sig(alpha / beta)
