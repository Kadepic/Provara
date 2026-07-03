"""CHIMIE QUANTITATIVE — solutions, thermochimie, électrochimie, FAUX=0 (formule/concept 2026-06-29).

Concentrations (molarité, dilution c₁V₁=c₂V₂, concentration massique), thermochimie (loi de Hess :
ΔH_réaction = ΣΔH_f(produits) − ΣΔH_f(réactifs)), électrochimie (potentiel de pile E = E_cathode − E_anode,
spontanéité). Mécanisme EXACT, sortie arrondie 6 chiffres significatifs. Abstention STRUCTURELLE : volume/quantité
≤ 0 -> ValueError (jamais un nombre absurde).

Couvre les sujets bornés « Solutions, concentrations », « Thermochimie », « Électrochimie ».
Vérifié en adverse par `valide_chimie_quantitative.py` (combustion CH₄ = −890 kJ/mol, pile Daniell = 1.10 V…).
"""
from __future__ import annotations

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
        raise ValueError("valeur strictement positive requise")


# ── SOLUTIONS / CONCENTRATIONS ──
def molarite(moles, volume_litres) -> float:
    """Concentration molaire c = n/V (mol/L). n ≥ 0, V > 0."""
    _num(moles)
    if moles < 0:
        raise ValueError("quantité de matière ≥ 0 requise")
    _pos(volume_litres)
    return _sig(moles / volume_litres)


def dilution(c1, v1, v2) -> float:
    """Concentration après dilution : c₂ = c₁·V₁/V₂ (c₁V₁ = c₂V₂). c1 ≥ 0, V1 ≥ 0, V2 > 0."""
    _num(c1, v1)
    if c1 < 0 or v1 < 0:
        raise ValueError("c1, V1 ≥ 0 requis")
    _pos(v2)
    return _sig(c1 * v1 / v2)


def volume_dilution(c1, v1, c2) -> float:
    """Volume final V₂ = c₁·V₁/c₂ pour atteindre la concentration c₂. c2 > 0."""
    _num(c1, v1)
    if c1 < 0 or v1 < 0:
        raise ValueError("c1, V1 ≥ 0 requis")
    _pos(c2)
    return _sig(c1 * v1 / c2)


def concentration_massique(masse_g, volume_litres) -> float:
    """Concentration massique = m/V (g/L). m ≥ 0, V > 0."""
    _num(masse_g)
    if masse_g < 0:
        raise ValueError("masse ≥ 0 requise")
    _pos(volume_litres)
    return _sig(masse_g / volume_litres)


# ── THERMOCHIMIE (loi de Hess) ──
def enthalpie_reaction(hf_produits, hf_reactifs) -> float:
    """ΔH_réaction = ΣΔH_f(produits) − ΣΔH_f(réactifs) (loi de Hess). Les listes contiennent les ΔH_f déjà
    pondérés par les coefficients stœchiométriques (kJ/mol). ΔH_f d'un corps simple = 0."""
    if not isinstance(hf_produits, (list, tuple)) or not isinstance(hf_reactifs, (list, tuple)):
        raise ValueError("listes de ΔH_f attendues")
    _num(*hf_produits, *hf_reactifs)
    return _sig(sum(hf_produits) - sum(hf_reactifs))


def est_exothermique(delta_h) -> bool:
    """Une réaction est exothermique ssi ΔH < 0 (libère de la chaleur)."""
    _num(delta_h)
    return delta_h < 0


# ── ÉLECTROCHIMIE ──
def potentiel_cellule(e_cathode, e_anode) -> float:
    """f.é.m. d'une pile E°_cell = E°_cathode − E°_anode (V). Pile spontanée ssi E°_cell > 0."""
    _num(e_cathode, e_anode)
    return _sig(e_cathode - e_anode)


def est_spontanee(e_cellule) -> bool:
    """Réaction électrochimique spontanée ssi E°_cell > 0 (ΔG = −nFE < 0)."""
    _num(e_cellule)
    return e_cellule > 0


if __name__ == "__main__":
    print("molarité 0.5 mol / 2 L :", molarite(0.5, 2))
    print("dilution c1=2,V1=0.1,V2=0.5 :", dilution(2, 0.1, 0.5))
    print("V pour diluer 2 M·0.1 L à 0.25 M :", volume_dilution(2, 0.1, 0.25))
    # combustion du méthane : CH4 + 2O2 -> CO2 + 2H2O(l)
    dh = enthalpie_reaction([-393.5, 2 * -285.8], [-74.8, 0])
    print("ΔH combustion CH4 :", dh, "kJ/mol (≈ -890) | exo ?", est_exothermique(dh))
    # pile Daniell : cathode Cu²⁺/Cu (+0.34), anode Zn²⁺/Zn (-0.76)
    e = potentiel_cellule(0.34, -0.76)
    print("pile Daniell :", e, "V | spontanée ?", est_spontanee(e))
