"""
ÉQUATIONS DE MAXWELL — conséquences quantitatives EXACTES de l'électromagnétisme du vide.

Même posture que `physique.py` / `chimie.py` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (les formules issues des équations de Maxwell dans le vide) est EXACT — garantie structurelle.
  • Les deux CONSTANTES de structure du vide sont des DONNÉES SOURCÉES (CODATA) :
        µ0  = 1.256 637 062 12e-6  H/m   (perméabilité magnétique du vide)
        ε0  = 8.854 187 8128e-12   F/m   (permittivité électrique du vide)
    À partir d'elles, les équations de Maxwell IMPOSENT :
        - la vitesse des ondes électromagnétiques  c = 1/√(µ0·ε0)  (≈ 299 792 458 m/s) ;
        - l'impédance caractéristique du vide       Z0 = √(µ0/ε0)  (≈ 376.730 Ω = µ0·c) ;
        - la densité d'énergie du champ électrique   u_E = ½·ε0·E² ;
        - la densité d'énergie du champ magnétique   u_B = B²/(2µ0).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision HONNÊTE (CODATA porte une incertitude).

ABSTENTION STRUCTURELLE (vérifiée en adverse par `valide_maxwell.py`) :
  - un champ non numérique (str, None, bool) -> ValueError : on ne devine pas une entrée ;
  - un champ négatif est ACCEPTÉ (la densité d'énergie dépend du CARRÉ — physiquement licite) ;
  - déterministe ; conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

Stdlib uniquement (math). Aucun chargement lourd à l'import.
"""
from __future__ import annotations

import math

# ── CONSTANTES SOURCÉES (CODATA) ───────────────────────────────────────────────────────────────────────────────
MU0 = 1.256_637_062_12e-6      # H/m — perméabilité magnétique du vide (CODATA 2018)
EPS0 = 8.854_187_8128e-12      # F/m — permittivité électrique du vide (CODATA 2018)

SOURCE = "CODATA 2018 (µ0, ε0)"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> float:
    """Valide qu'une entrée est un nombre réel fini (PAS un bool, PAS un str). Sinon ValueError (abstention)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"champ non numérique : {x!r}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"champ non fini : {x!r}")
    return xf


# ── CONSÉQUENCES DES ÉQUATIONS DE MAXWELL DANS LE VIDE ─────────────────────────────────────────────────────────
def vitesse_lumiere_calculee() -> float:
    """c = 1/√(µ0·ε0) — la vitesse des ondes EM imposée par les équations de Maxwell (≈ 299 792 458 m/s)."""
    return _sig(1.0 / math.sqrt(MU0 * EPS0))


def impedance_vide() -> float:
    """Z0 = √(µ0/ε0) — impédance caractéristique du vide (≈ 376.730 Ω). Égale aussi µ0·c."""
    return _sig(math.sqrt(MU0 / EPS0))


def densite_energie_E(E) -> float:
    """u_E = ½·ε0·E² — densité d'énergie du champ électrique (J/m³). E en V/m (signe indifférent : carré)."""
    Ef = _num(E)
    return _sig(0.5 * EPS0 * Ef * Ef)


def densite_energie_B(B) -> float:
    """u_B = B²/(2µ0) — densité d'énergie du champ magnétique (J/m³). B en T (signe indifférent : carré)."""
    Bf = _num(B)
    return _sig(Bf * Bf / (2.0 * MU0))


def densite_energie_totale(E, B) -> float:
    """u = ½·ε0·E² + B²/(2µ0) — densité d'énergie EM totale (J/m³)."""
    Ef = _num(E)
    Bf = _num(B)
    return _sig(0.5 * EPS0 * Ef * Ef + Bf * Bf / (2.0 * MU0))
