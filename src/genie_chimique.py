"""GÉNIE CHIMIQUE — réacteurs et distillation, FAUX=0 (mission formule/concept 2026-06-29).

Temps de séjour (τ = V/Q), taux de conversion d'un réacteur (CSTR/PFR pour une cinétique d'ordre 1), nombre minimal
d'étages théoriques de distillation (équation de Fenske), volatilité relative. Mécanisme EXACT, sortie 6 chiffres
significatifs. Abstention STRUCTURELLE : débit/volume ≤ 0, fractions hors ]0,1[, volatilité ≤ 1 -> ValueError.

Couvre le sujet borné « Réacteurs, distillation ».
Vérifié en adverse par `valide_genie_chimique.py` (τ, conversion ordre 1, Fenske).
"""
from __future__ import annotations

import math

_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _pos(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0:
            raise ValueError("grandeur strictement positive requise")


def temps_sejour(volume, debit) -> float:
    """Temps de séjour moyen τ = V/Q (s). V,Q > 0."""
    _pos(volume, debit)
    return _sig(volume / debit)


def conversion_cstr_ordre1(k, tau) -> float:
    """Taux de conversion d'un réacteur parfaitement agité (CSTR) pour une cinétique d'ordre 1 : X = kτ/(1+kτ) ∈ [0,1)."""
    _pos(k, tau)
    return _sig(k * tau / (1 + k * tau))


def conversion_pfr_ordre1(k, tau) -> float:
    """Taux de conversion d'un réacteur piston (PFR) pour une cinétique d'ordre 1 : X = 1 − e^(−kτ) ∈ [0,1)."""
    _pos(k, tau)
    return _sig(1 - math.exp(-k * tau))


def etages_fenske(x_distillat, x_residu, volatilite_relative) -> float:
    """Nombre minimal d'étages théoriques (reflux total) — équation de Fenske :
    N_min = ln[(xD/(1−xD))·((1−xB)/xB)] / ln(α). 0 < xB < xD < 1, α > 1."""
    if not (0 < x_residu < x_distillat < 1):
        raise ValueError("0 < x_résidu < x_distillat < 1 requis")
    if isinstance(volatilite_relative, bool) or not isinstance(volatilite_relative, (int, float)) or volatilite_relative <= 1:
        raise ValueError("volatilité relative α > 1 requise")
    num = math.log((x_distillat / (1 - x_distillat)) * ((1 - x_residu) / x_residu))
    return _sig(num / math.log(volatilite_relative))


if __name__ == "__main__":
    print("τ = 100 L / 5 L/s :", temps_sejour(100, 5), "s")
    print("conversion CSTR k=0.5,τ=4 :", conversion_cstr_ordre1(0.5, 4), "(= 2/3)")
    print("conversion PFR k=0.5,τ=4 :", conversion_pfr_ordre1(0.5, 4))
    print("PFR > CSTR (même k,τ) :", conversion_pfr_ordre1(0.5, 4) > conversion_cstr_ordre1(0.5, 4))
    print("Fenske xD=0.95,xB=0.05,α=2 :", etages_fenske(0.95, 0.05, 2))
