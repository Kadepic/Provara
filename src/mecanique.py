"""MÉCANIQUE (frottements, oscillateurs, fluides) — grandeurs CALCULABLES par formule, FAUX=0 (formule/concept 2026-06-29).

Complète `physique.py` (qui couvre énergie/forces de base) sur : frottement sec (F=μN), oscillateur harmonique
(période/pulsation/fréquence d'un système masse-ressort, pendule simple), énergie élastique, et statique des fluides
(pression, pression hydrostatique, poussée d'Archimède). Mécanisme EXACT, constante g sourcée (BIPM 9.80665).
Sortie arrondie à 6 chiffres significatifs (précision honnête). Abstention STRUCTURELLE : domaine invalide
(masse/raideur/surface ≤ 0, coefficient < 0…) -> ValueError, jamais un nombre absurde.

Couvre les sujets bornés « Forces, frottements », « Oscillateurs, résonance », « Mécanique des fluides ».
Vérifié en adverse par `valide_mecanique.py` (ancres : T(masse-ressort), pression, Archimède…).
"""
from __future__ import annotations

import math

G_PESANTEUR = 9.80665     # m/s² — gravité standard (BIPM, conventionnelle)
_SIG = 6


def _sig(x: float) -> float:
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def _pos(*xs):
    _num(*xs)
    if any(x <= 0 for x in xs):
        raise ValueError("grandeur strictement positive requise")


# ── FROTTEMENT SEC ──
def force_frottement(mu, force_normale) -> float:
    """Force de frottement F = μ·N. μ ≥ 0, N ≥ 0."""
    _num(mu, force_normale)
    if mu < 0 or force_normale < 0:
        raise ValueError("μ et N ≥ 0 requis")
    return _sig(mu * force_normale)


# ── OSCILLATEUR HARMONIQUE ──
def pulsation_ressort(m, k) -> float:
    """Pulsation propre ω = √(k/m) (rad/s) d'un système masse-ressort. m,k > 0."""
    _pos(m, k)
    return _sig(math.sqrt(k / m))


def periode_ressort(m, k) -> float:
    """Période T = 2π·√(m/k) (s). m,k > 0."""
    _pos(m, k)
    return _sig(2 * math.pi * math.sqrt(m / k))


def frequence_ressort(m, k) -> float:
    """Fréquence propre f = (1/2π)·√(k/m) (Hz). m,k > 0."""
    _pos(m, k)
    return _sig(math.sqrt(k / m) / (2 * math.pi))


def periode_pendule(longueur, g=G_PESANTEUR) -> float:
    """Période d'un pendule simple T = 2π·√(L/g) (s, petites oscillations). L,g > 0."""
    _pos(longueur, g)
    return _sig(2 * math.pi * math.sqrt(longueur / g))


def energie_ressort(k, deplacement) -> float:
    """Énergie élastique E = ½·k·x² (J). k ≥ 0."""
    _num(k, deplacement)
    if k < 0:
        raise ValueError("raideur k ≥ 0 requise")
    return _sig(0.5 * k * deplacement ** 2)


# ── STATIQUE DES FLUIDES ──
def pression(force, surface) -> float:
    """Pression P = F/A (Pa). surface > 0."""
    _num(force)
    _pos(surface)
    return _sig(force / surface)


def pression_hydrostatique(masse_volumique, profondeur, g=G_PESANTEUR) -> float:
    """Pression hydrostatique P = ρ·g·h (Pa). ρ > 0, h ≥ 0."""
    _pos(masse_volumique, g)
    _num(profondeur)
    if profondeur < 0:
        raise ValueError("profondeur ≥ 0 requise")
    return _sig(masse_volumique * g * profondeur)


def poussee_archimede(masse_volumique_fluide, volume_immerge, g=G_PESANTEUR) -> float:
    """Poussée d'Archimède F = ρ·V·g (N). ρ,V > 0."""
    _pos(masse_volumique_fluide, volume_immerge, g)
    return _sig(masse_volumique_fluide * volume_immerge * g)


if __name__ == "__main__":
    print("frottement μ=0.5,N=100 :", force_frottement(0.5, 100))
    print("période ressort m=1,k=1 :", periode_ressort(1, 1), "(2π)")
    print("période pendule L=1 :", periode_pendule(1), "s")
    print("fréquence ressort m=1,k=4π² :", frequence_ressort(1, 4 * math.pi ** 2), "Hz")
    print("énergie ressort k=200,x=0.1 :", energie_ressort(200, 0.1), "J")
    print("pression F=100,A=2 :", pression(100, 2), "Pa")
    print("Archimède ρ=1000,V=0.001 :", poussee_archimede(1000, 0.001), "N")
    print("P hydrostatique 10m d'eau :", pression_hydrostatique(1000, 10), "Pa")
