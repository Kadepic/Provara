"""CONTRÔLE QUALITÉ — maîtrise statistique des procédés (SPC), primitives EXACTES, FAUX=0.

Posture identique à `physique`/`maths_discretes` : le MÉCANISME est exact (formules SPC standard +
fonction de répartition normale via `math.erf`, qui est exacte), et l'abstention est STRUCTURELLE —
toute entrée invalide (σ ≤ 0, LSS ≤ LSI, n ≤ 0, type non numérique, booléen, non fini) lève `ValueError`,
JAMAIS un résultat faux. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

Couvre :
  • indice_capabilite_cp(LSS, LSI, σ) = (LSS−LSI)/(6σ) — capabilité POTENTIELLE (procédé centré idéal).
  • cpk(moyenne, LSS, LSI, σ) = min((LSS−moy)/(3σ), (moy−LSI)/(3σ)) — capabilité RÉELLE (tient compte du
    décentrage). Cpk ≤ Cp toujours ; Cpk = Cp si et seulement si le procédé est parfaitement centré.
  • limites_controle(moyenne, σ, n=3) = (moy − nσ, moy + nσ) — limites de contrôle (carte de Shewhart, ±3σ).
  • phi(z) — fonction de répartition de la loi normale centrée réduite, Φ(z)=½(1+erf(z/√2)) (mécanisme exact).
  • ppm_hors_specs(moyenne, LSS, LSI, σ) — défauts en parties par million pour un procédé normal (P(hors specs)·1e6).
  • six_sigma_ppm(niveau_sigma, derive=1.5) — DPMO long terme convention Six Sigma : 1e6·(1−Φ(niveau−derive)).
    Reproduit la table classique : 6σ→3.4, 5σ→233, 4.5σ→1350, 3σ→66807 DPMO.

Sortie arrondie à 10 chiffres significatifs (précision honnête). Vérifié en adverse par `valide_controle_qualite.py`.
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _nb(x) -> float:
    """Valide un réel fini (rejette bool, str, NaN, inf) ou lève ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"nombre réel attendu, reçu {x!r}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"valeur non finie : {x!r}")
    return xf


def _sigma_pos(sigma) -> float:
    s = _nb(sigma)
    if s <= 0:
        raise ValueError(f"écart-type σ > 0 requis, reçu {sigma!r}")
    return s


def _specs(lss, lsi) -> tuple[float, float]:
    a, b = _nb(lss), _nb(lsi)
    if a <= b:
        raise ValueError(f"LSS > LSI requis, reçu LSS={lss!r} LSI={lsi!r}")
    return a, b


# ── CAPABILITÉ ────────────────────────────────────────────────────────────────────────────────────────────────
def indice_capabilite_cp(LSS, LSI, sigma) -> float:
    """Cp = (LSS − LSI) / (6σ). Capabilité potentielle (procédé supposé centré)."""
    a, b = _specs(LSS, LSI)
    s = _sigma_pos(sigma)
    return _sig((a - b) / (6.0 * s))


def cpk(moyenne, LSS, LSI, sigma) -> float:
    """Cpk = min((LSS − moy)/(3σ), (moy − LSI)/(3σ)). Capabilité réelle (décentrage pris en compte)."""
    moy = _nb(moyenne)
    a, b = _specs(LSS, LSI)
    s = _sigma_pos(sigma)
    return _sig(min((a - moy) / (3.0 * s), (moy - b) / (3.0 * s)))


# ── CARTE DE CONTRÔLE ─────────────────────────────────────────────────────────────────────────────────────────
def limites_controle(moyenne, sigma, n=3) -> tuple[float, float]:
    """Limites de contrôle (LIC, LSC) = (moy − nσ, moy + nσ). n>0 (par défaut ±3σ, carte de Shewhart)."""
    moy = _nb(moyenne)
    s = _sigma_pos(sigma)
    nn = _nb(n)
    if nn <= 0:
        raise ValueError(f"nombre d'écarts-types n > 0 requis, reçu {n!r}")
    return (_sig(moy - nn * s), _sig(moy + nn * s))


# ── LOI NORMALE / DÉFAUTS ─────────────────────────────────────────────────────────────────────────────────────
def phi(z) -> float:
    """Φ(z) = P(Z ≤ z) pour Z ~ N(0,1) = ½(1 + erf(z/√2)). Mécanisme exact (math.erf)."""
    zz = _nb(z)
    return _sig(0.5 * (1.0 + math.erf(zz / math.sqrt(2.0))))


def ppm_hors_specs(moyenne, LSS, LSI, sigma) -> float:
    """Défauts (parties par million) d'un procédé normal : 1e6·[P(X<LSI) + P(X>LSS)]."""
    moy = _nb(moyenne)
    a, b = _specs(LSS, LSI)
    s = _sigma_pos(sigma)
    p_bas = 0.5 * (1.0 + math.erf((b - moy) / (s * math.sqrt(2.0))))          # P(X < LSI)
    p_haut = 0.5 * (1.0 - math.erf((a - moy) / (s * math.sqrt(2.0))))         # P(X > LSS)
    return _sig(1e6 * (p_bas + p_haut))


def six_sigma_ppm(niveau_sigma, derive=1.5) -> float:
    """DPMO long terme (convention Six Sigma, dérive de 1.5σ) : 1e6·(1 − Φ(niveau_sigma − derive)).

    Reproduit la table de référence : 6σ→3.4, 5σ→233, 4.5σ→1350, 4σ→6210, 3σ→66807 DPMO.
    """
    niv = _nb(niveau_sigma)
    d = _nb(derive)
    if niv <= 0:
        raise ValueError(f"niveau sigma > 0 requis, reçu {niveau_sigma!r}")
    if d < 0:
        raise ValueError(f"dérive ≥ 0 requise, reçu {derive!r}")
    z = niv - d
    return _sig(1e6 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))))
