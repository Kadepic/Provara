"""
ASTRONAUTIQUE — mécanique du vol (capacité de calcul/preuve, mandat Yohan : couvrir le borné « FORMULE »).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (équations de la mécanique du vol) est EXACT — garantie structurelle.
  • La seule CONSTANTE est G (constante gravitationnelle de Newton), DONNÉE SOURCÉE (CODATA 2018). Les masses/rayons
    d'astres fournis par défaut sont des données conventionnelles ; l'appelant passe ses propres valeurs.
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision HONNÊTE (G n'est connue qu'à ~5 chiffres ; on ne
    prétend pas à l'exactitude au-delà de la source). Le mécanisme reste exact ; l'arrondi borne la prétention.

COUVRE :
  - delta_v(ve, m0, mf)        : équation de Tsiolkovsky   Δv = ve·ln(m0/mf)        [m/s]
  - rapport_de_masse(ve, dv)   : m0/mf nécessaire pour un Δv donné = exp(dv/ve)     [sans dimension]
  - masse_finale(ve, m0, dv)   : masse après combustion    mf = m0·exp(-dv/ve)      [kg]
  - vitesse_orbitale(M, r)     : orbite circulaire          v = √(G·M/r)             [m/s]
  - vitesse_liberation(M, r)   : libération                 v = √(2·G·M/r)           [m/s]
  - periode_orbitale(M, r)     : 3e loi de Kepler           T = 2π·√(r³/(G·M))       [s]

GARANTIES (vérifiées en adverse par `valide_astronautique.py`) :
  - ABSTENTION STRUCTURELLE : toute entrée hors domaine lève ValueError — JAMAIS un nombre faux.
      ve ≤ 0, m0 ≤ 0, mf ≤ 0, m0 ≤ mf (Δv) ; dv < 0 ; M ≤ 0 ; r ≤ 0 ; type non numérique (bool/str/None) -> ValueError.
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).
"""
from __future__ import annotations

import math

# ── CONSTANTE SOURCÉE ───────────────────────────────────────────────────────────────────────────────────────────
G_NEWTON = 6.674_3e-11           # m^3 kg^-1 s^-2 — constante gravitationnelle (CODATA 2018, ~5 chiffres)

# ── DONNÉES CONVENTIONNELLES (commodité d'appel — l'appelant reste libre de passer les siennes) ──────────────────
MASSE_TERRE = 5.972e24           # kg
RAYON_TERRE = 6.371e6            # m (rayon moyen)

SOURCE = "G = constante gravitationnelle CODATA 2018"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> float:
    """Convertit en float réel un nombre VALIDE ; lève ValueError pour bool / str / None / NaN / inf.

    bool est explicitement rejeté (True n'est PAS la masse 1) : abstention structurelle plutôt qu'un faux."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("entrée non numérique")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("entrée non finie")
    return v


# ── ÉQUATION DE TSIOLKOVSKY ─────────────────────────────────────────────────────────────────────────────────────
def delta_v(ve, m0, mf) -> float:
    """Δv = ve·ln(m0/mf). ve vitesse d'éjection (m/s), m0 masse initiale, mf masse finale (kg).

    Domaine : ve > 0, mf > 0, m0 > mf (on brûle des ergols, donc m0 > mf). Sinon ValueError."""
    ve = _num(ve)
    m0 = _num(m0)
    mf = _num(mf)
    if ve <= 0:
        raise ValueError("vitesse d'éjection ve doit être > 0")
    if mf <= 0:
        raise ValueError("masse finale mf doit être > 0")
    if m0 <= mf:
        raise ValueError("masse initiale m0 doit être > masse finale mf")
    return _sig(ve * math.log(m0 / mf))


def rapport_de_masse(ve, dv) -> float:
    """Rapport de masse m0/mf nécessaire pour atteindre un Δv donné : m0/mf = exp(dv/ve).

    Domaine : ve > 0, dv ≥ 0 (Δv = 0 -> rapport 1, aucune combustion). Sinon ValueError."""
    ve = _num(ve)
    dv = _num(dv)
    if ve <= 0:
        raise ValueError("vitesse d'éjection ve doit être > 0")
    if dv < 0:
        raise ValueError("Δv doit être ≥ 0")
    return _sig(math.exp(dv / ve))


def masse_finale(ve, m0, dv) -> float:
    """Masse finale (sèche + charge utile) après avoir dépensé Δv : mf = m0·exp(-dv/ve).

    Domaine : ve > 0, m0 > 0, dv ≥ 0. Sinon ValueError."""
    ve = _num(ve)
    m0 = _num(m0)
    dv = _num(dv)
    if ve <= 0:
        raise ValueError("vitesse d'éjection ve doit être > 0")
    if m0 <= 0:
        raise ValueError("masse initiale m0 doit être > 0")
    if dv < 0:
        raise ValueError("Δv doit être ≥ 0")
    return _sig(m0 * math.exp(-dv / ve))


# ── MÉCANIQUE ORBITALE ──────────────────────────────────────────────────────────────────────────────────────────
def vitesse_orbitale(M, r) -> float:
    """Vitesse d'une orbite circulaire de rayon r autour d'un astre de masse M : v = √(G·M/r) [m/s].

    Domaine : M > 0, r > 0. Sinon ValueError."""
    M = _num(M)
    r = _num(r)
    if M <= 0:
        raise ValueError("masse M doit être > 0")
    if r <= 0:
        raise ValueError("rayon orbital r doit être > 0")
    return _sig(math.sqrt(G_NEWTON * M / r))


def vitesse_liberation(M, r) -> float:
    """Vitesse de libération depuis le rayon r autour d'un astre de masse M : v = √(2·G·M/r) [m/s].

    Domaine : M > 0, r > 0. Sinon ValueError."""
    M = _num(M)
    r = _num(r)
    if M <= 0:
        raise ValueError("masse M doit être > 0")
    if r <= 0:
        raise ValueError("rayon r doit être > 0")
    return _sig(math.sqrt(2.0 * G_NEWTON * M / r))


def periode_orbitale(M, r) -> float:
    """Période d'une orbite circulaire (3e loi de Kepler) : T = 2π·√(r³/(G·M)) [s].

    Domaine : M > 0, r > 0. Sinon ValueError."""
    M = _num(M)
    r = _num(r)
    if M <= 0:
        raise ValueError("masse M doit être > 0")
    if r <= 0:
        raise ValueError("rayon orbital r doit être > 0")
    return _sig(2.0 * math.pi * math.sqrt(r ** 3 / (G_NEWTON * M)))
