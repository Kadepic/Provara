"""LIAISONS CHIMIQUES — nature de la liaison par électronégativité, FAUX=0 (mission formule/concept 2026-06-29).

À partir des électronégativités (échelle de Pauling) de deux éléments, on détermine la NATURE de la liaison :
covalente non polaire (Δχ < 0.4), covalente polaire (0.4 ≤ Δχ < 1.7), ionique (Δχ ≥ 1.7), et le pourcentage de
caractère ionique (formule de Pauling : 1 − e^(−(Δχ/2)²)). Mécanisme EXACT (comparaisons + formule). Abstention
STRUCTURELLE : électronégativité ≤ 0 -> ValueError.

Couvre le sujet borné « Liaisons chimiques ».
Vérifié en adverse par `valide_liaisons_chimiques.py` (NaCl ionique, H₂ covalente, HCl polaire).
"""
from __future__ import annotations

import math

_SIG = 6


def _en(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0:
            raise ValueError("électronégativité > 0 requise")


def difference_electronegativite(chi1, chi2) -> float:
    """Différence d'électronégativité |χ₁ − χ₂|."""
    _en(chi1, chi2)
    return round(abs(chi1 - chi2), 4)


def nature_liaison(chi1, chi2) -> str:
    """Nature de la liaison : 'covalente_non_polaire' (Δχ<0.4), 'covalente_polaire' (0.4≤Δχ<1.7), 'ionique' (Δχ≥1.7)."""
    d = difference_electronegativite(chi1, chi2)
    if d < 0.4:
        return "covalente_non_polaire"
    if d < 1.7:
        return "covalente_polaire"
    return "ionique"


def pourcentage_ionique(chi1, chi2) -> float:
    """Caractère ionique d'après Pauling : %ionique = 100·(1 − e^(−(Δχ/2)²))."""
    d = difference_electronegativite(chi1, chi2)
    pct = 100 * (1 - math.exp(-((d / 2) ** 2)))
    return float(f"{pct:.{_SIG}g}")


if __name__ == "__main__":
    # χ : H=2.20, C=2.55, N=3.04, O=3.44, F=3.98, Na=0.93, Cl=3.16, Cs=0.79
    print("H–H (2.20,2.20) :", nature_liaison(2.20, 2.20), "| Δχ :", difference_electronegativite(2.20, 2.20))
    print("H–Cl (2.20,3.16) :", nature_liaison(2.20, 3.16), "| %ionique :", pourcentage_ionique(2.20, 3.16))
    print("Na–Cl (0.93,3.16) :", nature_liaison(0.93, 3.16), "| %ionique :", pourcentage_ionique(0.93, 3.16))
    print("C–H (2.55,2.20) :", nature_liaison(2.55, 2.20))
    print("Cs–F (0.79,3.98) :", nature_liaison(0.79, 3.98), "| %ionique :", pourcentage_ionique(0.79, 3.98))
