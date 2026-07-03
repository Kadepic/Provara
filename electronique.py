"""ÉLECTRONIQUE (circuits) — grandeurs CALCULABLES, FAUX=0 (mission formule/concept 2026-06-29).

Associations de résistances (série / parallèle), diviseur de tension, constante de temps RC, impédances
(condensateur 1/2πfC, bobine 2πfL), fréquence de résonance LC. Complète `physique.py` (loi d'Ohm U=RI, P=UI).
Mécanisme EXACT, sortie 6 chiffres significatifs. Abstention STRUCTURELLE : résistance/fréquence/capacité ≤ 0,
liste vide -> ValueError (jamais un nombre absurde).

Couvre le sujet borné « Circuits électroniques » (le compteur ne tenait que Ohm + puissance).
Vérifié en adverse par `valide_electronique.py` (série/parallèle/diviseur/RC connus).
"""
from __future__ import annotations

import math

_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _pos_liste(xs):
    if not isinstance(xs, (list, tuple)) or not xs:
        raise ValueError("liste non vide de valeurs > 0 requise")
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0:
            raise ValueError(f"valeur > 0 requise, reçu {x!r}")


def _pos(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0:
            raise ValueError("grandeur strictement positive requise")


def resistance_serie(resistances) -> float:
    """Résistance équivalente en SÉRIE = Σ Rᵢ."""
    _pos_liste(resistances)
    return _sig(sum(resistances))


def resistance_parallele(resistances) -> float:
    """Résistance équivalente en PARALLÈLE = 1 / Σ(1/Rᵢ)."""
    _pos_liste(resistances)
    return _sig(1.0 / sum(1.0 / r for r in resistances))


def diviseur_tension(v_entree, r1, r2) -> float:
    """Tension de sortie d'un pont diviseur : V_out = V_in·R₂/(R₁+R₂)."""
    if isinstance(v_entree, bool) or not isinstance(v_entree, (int, float)):
        raise ValueError("tension numérique requise")
    _pos(r1, r2)
    return _sig(v_entree * r2 / (r1 + r2))


def constante_temps_rc(r, c) -> float:
    """Constante de temps d'un circuit RC : τ = R·C (s)."""
    _pos(r, c)
    return _sig(r * c)


def impedance_condensateur(frequence, capacite) -> float:
    """Réactance capacitive : X_C = 1/(2π·f·C) (Ω)."""
    _pos(frequence, capacite)
    return _sig(1.0 / (2 * math.pi * frequence * capacite))


def impedance_bobine(frequence, inductance) -> float:
    """Réactance inductive : X_L = 2π·f·L (Ω)."""
    _pos(frequence, inductance)
    return _sig(2 * math.pi * frequence * inductance)


def frequence_resonance_lc(inductance, capacite) -> float:
    """Fréquence de résonance d'un circuit LC : f = 1/(2π·√(LC)) (Hz)."""
    _pos(inductance, capacite)
    return _sig(1.0 / (2 * math.pi * math.sqrt(inductance * capacite)))


if __name__ == "__main__":
    print("série [10,20,30] :", resistance_serie([10, 20, 30]))
    print("parallèle [2,3,6] :", resistance_parallele([2, 3, 6]))
    print("parallèle [10,10] :", resistance_parallele([10, 10]))
    print("diviseur 12V,1k,2k :", diviseur_tension(12, 1000, 2000))
    print("τ RC 1k·1µF :", constante_temps_rc(1000, 1e-6))
    print("Xc 50Hz,1µF :", impedance_condensateur(50, 1e-6))
    print("f résonance LC 1mH,1µF :", frequence_resonance_lc(1e-3, 1e-6))
