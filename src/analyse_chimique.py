"""
ANALYSE CHIMIQUE BORNÉE — méthodes d'analyse (spectroscopie UV-visible, chromatographie).

Même posture FAUX=0 que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (loi physico-chimique) est EXACT — garantie structurelle.
  • ABSTENTION STRUCTURELLE : toute entrée hors domaine (type, signe, plage) lève ValueError,
    JAMAIS un résultat faux. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.
  • Sortie ARRONDIE à 10 chiffres significatifs — précision honnête (pas de faux exact au-delà).

COUVERTURE :
  ── Spectroscopie d'absorption (loi de Beer-Lambert) ──
    A = ε·l·c                       absorbance (sans dimension)
        ε = coefficient d'absorption molaire (L·mol⁻¹·cm⁻¹), l = trajet optique (cm), c = concentration (mol·L⁻¹)
    c = A / (ε·l)                   concentration retrouvée depuis l'absorbance
    T = 10^(−A)                     transmittance, T ∈ ]0, 1]   (A = −log₁₀ T, relation inverse exacte)
  ── Chromatographie sur couche mince (CCM) ──
    Rf = d_soluté / d_solvant       facteur de rétention, Rf ∈ ]0, 1]   (le soluté ne dépasse jamais le front)

GARDES DE DOMAINE (vérifiées en adverse par valide_analyse_chimique.py) :
  - ε ≤ 0  -> ValueError   (un coefficient d'absorption est strictement positif)
  - l ≤ 0  -> ValueError   (un trajet optique est strictement positif)
  - c < 0  -> ValueError   (une concentration est ≥ 0 ; c = 0 -> A = 0 admis)
  - A < 0  -> ValueError   (l'absorbance d'un échantillon est ≥ 0 ; A < 0 -> T > 1 impossible)
  - distances ≤ 0 -> ValueError, et d_soluté > d_solvant -> ValueError (Rf ≤ 1 par construction physique)
  - type non numérique (ou booléen) -> ValueError
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _reel(x) -> float:
    """Renvoie x comme float si c'est un nombre réel (pas un booléen), sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"valeur non numérique : {x!r}")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"valeur non finie : {x!r}")
    return v


# ── SPECTROSCOPIE : loi de Beer-Lambert ─────────────────────────────────────────────────────────────────────────

def absorbance(epsilon, l, c) -> float:
    """A = ε·l·c. ε > 0, l > 0, c ≥ 0. Renvoie l'absorbance (sans dimension)."""
    e, ll, cc = _reel(epsilon), _reel(l), _reel(c)
    if e <= 0:
        raise ValueError("epsilon doit être > 0")
    if ll <= 0:
        raise ValueError("l (trajet optique) doit être > 0")
    if cc < 0:
        raise ValueError("c (concentration) doit être >= 0")
    return _sig(e * ll * cc)


def concentration_depuis_absorbance(A, epsilon, l) -> float:
    """c = A / (ε·l). A ≥ 0, ε > 0, l > 0. Renvoie la concentration (mol·L⁻¹)."""
    a, e, ll = _reel(A), _reel(epsilon), _reel(l)
    if a < 0:
        raise ValueError("A (absorbance) doit être >= 0")
    if e <= 0:
        raise ValueError("epsilon doit être > 0")
    if ll <= 0:
        raise ValueError("l (trajet optique) doit être > 0")
    return _sig(a / (e * ll))


def transmittance(A) -> float:
    """T = 10^(−A). A ≥ 0 -> T ∈ ]0, 1]. Renvoie la transmittance (fraction)."""
    a = _reel(A)
    if a < 0:
        raise ValueError("A (absorbance) doit être >= 0 (sinon T > 1, impossible)")
    return _sig(10.0 ** (-a))


# ── CHROMATOGRAPHIE : facteur de rétention (CCM) ────────────────────────────────────────────────────────────────

def facteur_retention_rf(distance_solute, distance_solvant) -> float:
    """Rf = d_soluté / d_solvant. Distances > 0 et d_soluté ≤ d_solvant -> Rf ∈ ]0, 1]."""
    ds, df = _reel(distance_solute), _reel(distance_solvant)
    if ds <= 0:
        raise ValueError("distance_solute doit être > 0")
    if df <= 0:
        raise ValueError("distance_solvant doit être > 0")
    if ds > df:
        raise ValueError("distance_solute ne peut dépasser distance_solvant (Rf <= 1)")
    return _sig(ds / df)
