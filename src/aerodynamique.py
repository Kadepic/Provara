"""
AÉRONAUTIQUE — vol, aérodynamique (mandat Yohan : couvrir le borné, bloc « FORMULE »).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (les formules d'aérodynamique) est EXACT — garantie structurelle, mécanique des fluides établie.
  • La sortie est ARRONDIE à 6 chiffres significatifs — précision HONNÊTE, pas un faux exact.
  • Toute entrée hors domaine physique lève ValueError (ABSTENTION) — jamais un nombre absurde.

FORMULES (établies, mécanique des fluides) :
  - Portance       L = ½·ρ·v²·S·Cz        (N)   — équation de portance
  - Traînée        D = ½·ρ·v²·S·Cx        (N)   — équation de traînée
  - Finesse        f = Cz/Cx              (—)   — rapport portance/traînée (L/D)
  - Reynolds       Re = ρ·v·L/μ           (—)   — nombre de Reynolds (sans dimension)
  - Vol en palier  L = poids  ⇒  v = √(2·poids/(ρ·S·Cz))   (m/s)  — vitesse d'équilibre

CONVENTIONS / repères (NON utilisés dans le calcul, documentaires) :
  • Air au niveau de la mer (ISA, 15 °C) : ρ ≈ 1.225 kg/m³ ; viscosité dynamique μ ≈ 1.81e-5 Pa·s.
  • Portance ∝ v² (doubler la vitesse quadruple la portance, à ρ, S, Cz constants).

SOUNDNESS (vérifiée en adverse par `valide_aerodynamique.py`) :
  - ρ ≤ 0, S ≤ 0, v < 0           -> ValueError ;
  - Cx ≤ 0 (traînée, finesse)     -> ValueError (coefficient de traînée toujours strictement positif) ;
  - L ≤ 0, μ ≤ 0 (Reynolds)       -> ValueError ;
  - Cz ≤ 0, poids ≤ 0 (palier)    -> ValueError (pas d'équilibre sans portance positive) ;
  - tout argument non numérique / booléen / non fini -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math

RHO_AIR_NIVEAU_MER = 1.225          # kg/m³ — masse volumique de l'air, ISA niveau mer 15 °C
MU_AIR_NIVEAU_MER = 1.81e-5         # Pa·s  — viscosité dynamique de l'air, ~15 °C
SOURCE = "mécanique des fluides (équations de portance/traînée, Reynolds) ; air ISA niveau mer"

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> float:
    """Convertit x en float fini en REFUSANT booléens / non numériques / non finis -> ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"argument non numérique : {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"argument non fini : {x!r}")
    return f


def portance(rho, v, surface, cz) -> float:
    """Portance L = ½·ρ·v²·S·Cz (N). Cz quelconque (déportance Cz<0 admise). ρ≤0, S≤0, v<0 -> ValueError."""
    rho, v, surface, cz = _num(rho), _num(v), _num(surface), _num(cz)
    if rho <= 0:
        raise ValueError("rho (masse volumique) doit être > 0")
    if surface <= 0:
        raise ValueError("surface doit être > 0")
    if v < 0:
        raise ValueError("v (vitesse) doit être >= 0")
    return _sig(0.5 * rho * v * v * surface * cz)


def trainee(rho, v, surface, cx) -> float:
    """Traînée D = ½·ρ·v²·S·Cx (N). ρ≤0, S≤0, v<0, Cx≤0 -> ValueError."""
    rho, v, surface, cx = _num(rho), _num(v), _num(surface), _num(cx)
    if rho <= 0:
        raise ValueError("rho (masse volumique) doit être > 0")
    if surface <= 0:
        raise ValueError("surface doit être > 0")
    if v < 0:
        raise ValueError("v (vitesse) doit être >= 0")
    if cx <= 0:
        raise ValueError("cx (coefficient de traînée) doit être > 0")
    return _sig(0.5 * rho * v * v * surface * cx)


def finesse(cz, cx) -> float:
    """Finesse f = Cz/Cx (rapport portance/traînée, L/D). Cz quelconque ; Cx≤0 -> ValueError."""
    cz, cx = _num(cz), _num(cx)
    if cx <= 0:
        raise ValueError("cx (coefficient de traînée) doit être > 0")
    return _sig(cz / cx)


def reynolds(rho, v, longueur, mu) -> float:
    """Nombre de Reynolds Re = ρ·v·L/μ (sans dimension). ρ≤0, v<0, L≤0, μ≤0 -> ValueError."""
    rho, v, longueur, mu = _num(rho), _num(v), _num(longueur), _num(mu)
    if rho <= 0:
        raise ValueError("rho (masse volumique) doit être > 0")
    if v < 0:
        raise ValueError("v (vitesse) doit être >= 0")
    if longueur <= 0:
        raise ValueError("longueur caractéristique doit être > 0")
    if mu <= 0:
        raise ValueError("mu (viscosité dynamique) doit être > 0")
    return _sig(rho * v * longueur / mu)


def vol_equilibre(rho, surface, cz, poids) -> float:
    """Vitesse de vol en palier : portance = poids ⇒ v = √(2·poids/(ρ·S·Cz)) (m/s).

    poids en newtons (= m·g). ρ≤0, S≤0, Cz≤0, poids≤0 -> ValueError (pas d'équilibre sans portance positive).
    """
    rho, surface, cz, poids = _num(rho), _num(surface), _num(cz), _num(poids)
    if rho <= 0:
        raise ValueError("rho (masse volumique) doit être > 0")
    if surface <= 0:
        raise ValueError("surface doit être > 0")
    if cz <= 0:
        raise ValueError("cz (coefficient de portance) doit être > 0")
    if poids <= 0:
        raise ValueError("poids doit être > 0")
    return _sig(math.sqrt(2.0 * poids / (rho * surface * cz)))
