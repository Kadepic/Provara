"""RELATIVITÉ GÉNÉRALE — primitives EXACTES, directement appelables, FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `physique`/`maths_discretes`/`chimie`) : le MÉCANISME est exact (formules de la métrique de
Schwarzschild), l'abstention est STRUCTURELLE — toute entrée invalide (type, domaine) lève `ValueError`, JAMAIS un
résultat faux. Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

MÉCANISME COUVERT (métrique de Schwarzschild, masse ponctuelle non chargée, non tournante) :
  • rayon de Schwarzschild        r_s(M) = 2·G·M / c²
        — le rayon de l'horizon des événements d'un trou noir de masse M.
  • dilatation gravitationnelle   τ(t, M, r) = t·√(1 − r_s/r) = t·√(1 − 2GM/(r·c²))
        — temps propre τ mesuré à la distance r d'une masse M, pour un temps coordonnée t (loin de la masse).
          √(1 − r_s/r) < 1 : le temps s'écoule plus lentement au fond du puits de gravité (red-shift gravitationnel).

CONSTANTES (données SOURCÉES, comme les masses atomiques de `chimie` : le mécanisme est garanti, la donnée sourcée) :
  G = 6.6743e-11 m³·kg⁻¹·s⁻² (CODATA 2018, mesurée) ; c = 299792458 m/s (EXACT, définition SI du mètre).

SOUNDNESS (vérifiée en adverse par `valide_relativite_generale.py`) :
  - M ≤ 0  -> ValueError (pas de masse négative/nulle) ;
  - r ≤ 0  -> ValueError (distance non physique) ;
  - r ≤ r_s(M) -> ValueError : à/sous l'horizon le facteur √(1 − r_s/r) n'est plus réel (≤ 0) ; on s'abstient
    plutôt que de renvoyer 0 ou un imaginaire — la métrique de Schwarzschild extérieure n'y est pas valide ;
  - type non numérique (ou bool) -> ValueError.
La sortie est arrondie à 10 chiffres significatifs (précision honnête : G n'est connue qu'à ~5 chiffres).
"""
from __future__ import annotations

import math

# ── CONSTANTES SOURCÉES ─────────────────────────────────────────────────────────────────────────────────────────
G = 6.6743e-11          # m³·kg⁻¹·s⁻² — CODATA 2018 (mesurée)
C = 299_792_458.0       # m/s — EXACT (définition SI)
C2 = C * C              # m²/s²

SOURCE = "G = CODATA 2018 (6.6743e-11) ; c = 299792458 m/s (SI exact)"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def rayon_schwarzschild(M: float) -> float:
    """Rayon de Schwarzschild r_s = 2·G·M / c² (m). M en kg, > 0.

    M ≤ 0 ou non numérique -> ValueError (jamais un rayon absurde).
    """
    if not _num(M):
        raise ValueError(f"masse numérique attendue, reçu {M!r}")
    if M <= 0:
        raise ValueError(f"masse strictement positive attendue, reçu {M!r}")
    return _sig(2.0 * G * M / C2)


def dilatation_gravitationnelle(t: float, M: float, r: float) -> float:
    """Temps propre τ = t·√(1 − 2GM/(r·c²)) (s) à la distance r (m) d'une masse M (kg), pour un temps coordonnée t.

    Abstention (ValueError) si : type non numérique ; M ≤ 0 ; r ≤ 0 ; ou r ≤ r_s(M) (à/sous l'horizon : facteur
    non réel, métrique extérieure invalide). Conservateur : jamais 0 ni imaginaire, on lève.
    """
    if not (_num(t) and _num(M) and _num(r)):
        raise ValueError("arguments numériques attendus (t, M, r)")
    if M <= 0:
        raise ValueError(f"masse strictement positive attendue, reçu {M!r}")
    if r <= 0:
        raise ValueError(f"distance strictement positive attendue, reçu {r!r}")
    rs = 2.0 * G * M / C2
    if r <= rs:
        raise ValueError(f"r ({r!r}) ≤ rayon de Schwarzschild ({rs!r}) : à/sous l'horizon, facteur non réel")
    facteur = math.sqrt(1.0 - rs / r)
    return _sig(t * facteur)
