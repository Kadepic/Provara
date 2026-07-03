"""
MÉCANIQUE QUANTIQUE — relations fondamentales EXACTES, appelables directement, FAUX=0
(mission formule/concept 2026-06-29 ; même posture que physique.py / maths_discretes.py).

MÉCANISME (formules exactes — c'est la garantie structurelle) :
  • energie_photon(f)             = h·f             — relation de Planck-Einstein (E = h·ν)
  • longueur_onde_broglie(p)      = h/p             — longueur d'onde de de Broglie (λ = h/p)
  • niveaux_puits_infini(n, L, m) = n²·h²/(8·m·L²)  — énergies propres du puits de potentiel infini 1D
  • borne_heisenberg(Δx)          = ħ/(2·Δx)        — borne inférieure de Δp (principe : Δp·Δx ≥ ħ/2)

CONSTANTES SOURCÉES (comme les masses atomiques de chimie : mécanisme garanti, constante sourcée) :
  • h  = 6.626 070 15e-34 J·s   — EXACTE (redéfinition SI 2019)
  • ħ  = h/(2π)                 — constante réduite (dérivée exacte de h)
  • c  = 299 792 458 m/s        — EXACTE (définition SI du mètre)
  • mₑ = 9.109e-31 kg           — masse de l'électron (valeur sourcée)

ABSTENTION STRUCTURELLE (conservateur : faux négatif/abstention toléré, faux POSITIF interdit) :
  toute entrée invalide lève ValueError — JAMAIS un résultat faux :
    f ≤ 0, p ≤ 0, Δx ≤ 0, L ≤ 0, m ≤ 0 ; n non entier ou < 1 ; type non numérique ; booléen ; non fini.

Sorties arrondies à 10 chiffres significatifs (précision honnête — pas de faux exact au-delà des constantes).
Imports stdlib uniquement (math) ; rien de lourd. Vérifié en adverse par valide_quantique.py
(ancres physiques externes connues + soundness : entrée invalide -> ValueError + déterminisme).
"""
from __future__ import annotations

import math

# ── CONSTANTES SOURCÉES ──────────────────────────────────────────────────────────────────────────────────────────
H_PLANCK = 6.626_070_15e-34            # J·s — EXACTE (SI 2019)
HBAR = H_PLANCK / (2.0 * math.pi)      # J·s — réduite (dérivée exacte de h)
C_LUMIERE = 299_792_458.0              # m/s — EXACTE (définition SI du mètre)
MASSE_ELECTRON = 9.109e-31             # kg  — masse de l'électron (sourcée)

SOURCE = "constantes SI 2019 (h, c exactes) ; ħ = h/2π ; mₑ sourcée"

_SIG = 10


def _sig(x: float, n: int = _SIG) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _reel_pos(x) -> float:
    """Valide un réel STRICTEMENT positif et fini. Rejette bool, type non numérique, ≤ 0, inf/nan."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"réel > 0 attendu, reçu {x!r}")
    xf = float(x)
    if not math.isfinite(xf) or xf <= 0.0:
        raise ValueError(f"réel > 0 et fini attendu, reçu {x!r}")
    return xf


def energie_photon(frequence) -> float:
    """E = h·ν (Planck-Einstein). frequence ν en hertz (> 0). Retour : énergie en joules."""
    f = _reel_pos(frequence)
    return _sig(H_PLANCK * f)


def longueur_onde_broglie(p) -> float:
    """λ = h/p (de Broglie). p = quantité de mouvement en kg·m/s (> 0). Retour : longueur d'onde en mètres."""
    pp = _reel_pos(p)
    return _sig(H_PLANCK / pp)


def niveaux_puits_infini(n, L, m) -> float:
    """Eₙ = n²·h²/(8·m·L²) — énergie du niveau n d'un puits infini 1D.

    n : nombre quantique entier ≥ 1 ; L : largeur du puits en mètres (> 0) ; m : masse en kg (> 0).
    Retour : énergie du niveau en joules. n non entier / < 1 -> ValueError (un niveau est quantifié).
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"n entier ≥ 1 attendu, reçu {n!r}")
    LL = _reel_pos(L)
    mm = _reel_pos(m)
    return _sig(n * n * H_PLANCK * H_PLANCK / (8.0 * mm * LL * LL))


def borne_heisenberg(delta_x) -> float:
    """Δp_min = ħ/(2·Δx) — borne inférieure du principe d'incertitude (Δp·Δx ≥ ħ/2).

    delta_x = incertitude en position Δx en mètres (> 0). Retour : incertitude minimale Δp en kg·m/s.
    """
    dx = _reel_pos(delta_x)
    return _sig(HBAR / (2.0 * dx))
