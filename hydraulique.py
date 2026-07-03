"""HYDRAULIQUE — écoulement des fluides, FAUX=0 (mission formule/concept 2026-06-29).

Débit volumique (Q = v·A), équation de continuité (v₁A₁ = v₂A₂), nombre de Reynolds (régime laminaire/turbulent),
charge de Bernoulli. Mécanisme EXACT, sortie 6 chiffres significatifs. Abstention STRUCTURELLE : section / viscosité
≤ 0 -> ValueError.

Couvre le sujet borné « Hydraulique ».
Vérifié en adverse par `valide_hydraulique.py` (débit, continuité, Reynolds laminaire/turbulent).
"""
from __future__ import annotations

G_PESANTEUR = 9.80665
_SIG = 6


def _sig(x):
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


def debit_volumique(vitesse, section) -> float:
    """Débit volumique Q = v·A (m³/s). v ≥ 0, A > 0."""
    _num(vitesse)
    if vitesse < 0:
        raise ValueError("vitesse ≥ 0 requise")
    _pos(section)
    return _sig(vitesse * section)


def vitesse_continuite(v1, a1, a2) -> float:
    """Équation de continuité (fluide incompressible) : v₂ = v₁·A₁/A₂. A₁,A₂ > 0."""
    _num(v1)
    if v1 < 0:
        raise ValueError("vitesse ≥ 0 requise")
    _pos(a1, a2)
    return _sig(v1 * a1 / a2)


def nombre_reynolds(masse_volumique, vitesse, diametre, viscosite) -> float:
    """Nombre de Reynolds Re = ρ·v·D/μ (sans dimension). ρ,D,μ > 0."""
    _pos(masse_volumique, diametre, viscosite)
    _num(vitesse)
    if vitesse < 0:
        raise ValueError("vitesse ≥ 0 requise")
    return _sig(masse_volumique * vitesse * diametre / viscosite)


def regime_ecoulement(reynolds) -> str:
    """Régime d'écoulement d'après Re : 'laminaire' (Re < 2000), 'transitoire' (2000–4000), 'turbulent' (> 4000)."""
    _num(reynolds)
    if reynolds < 0:
        raise ValueError("Re ≥ 0 requis")
    if reynolds < 2000:
        return "laminaire"
    if reynolds <= 4000:
        return "transitoire"
    return "turbulent"


def charge_bernoulli(vitesse, pression, hauteur, masse_volumique=1000.0) -> float:
    """Charge totale de Bernoulli H = p/(ρg) + v²/(2g) + z (m). ρ > 0."""
    _num(vitesse, pression, hauteur)
    _pos(masse_volumique)
    return _sig(pression / (masse_volumique * G_PESANTEUR) + vitesse ** 2 / (2 * G_PESANTEUR) + hauteur)


if __name__ == "__main__":
    print("débit v=2,A=0.5 :", debit_volumique(2, 0.5))
    print("continuité v1=2,A1=1,A2=0.5 :", vitesse_continuite(2, 1, 0.5))
    print("Reynolds eau ρ=1000,v=1,D=0.1,μ=0.001 :", nombre_reynolds(1000, 1, 0.1, 0.001))
    print("régime Re=500 :", regime_ecoulement(500), "| Re=100000 :", regime_ecoulement(100000))
