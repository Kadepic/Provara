"""
NUCLÉOSYNTHÈSE — énergie nucléaire bornée (équivalence masse↔énergie, défaut de masse, énergie de liaison).

Même posture FAUX=0 que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (Δm·c² ; E_liaison/A ; Q de réaction) est EXACT — garantie structurelle.
  • La CONSTANTE d'équivalence est SOURCÉE : 1 u = 931.494 MeV/c² (CODATA, valeur conventionnelle du sujet).
  • Le PIC DE FER est un FAIT établi de la courbe d'Aston : ⁵⁶Fe ≈ 8.79 MeV/nucléon (sommet de la liaison).

GARANTIES (vérifiées en adverse par `valide_nucleosynthese.py`) :
  - défaut de masse négatif, masse réactif/produit ≤ 0, nombre de masse A non entier-positif,
    énergie de liaison négative, entrée non numérique / NaN / inf  ->  ValueError (jamais un nombre faux) ;
  - déterministe et pur (mêmes entrées -> même sortie) ;
  - conservateur : on s'abstient (ValueError) au moindre doute plutôt que d'inventer une valeur.

Conventions de signe :
  - energie_liaison / energie_liaison_par_nucleon : énergie POSITIVE (cohésion du noyau).
  - q_reaction : Q = (Σ masses réactifs − Σ masses produits)·931.494 MeV.
        Q > 0  -> réaction EXOTHERMIQUE (de la masse a été convertie en énergie, ex. fusion H→He) ;
        Q < 0  -> réaction ENDOTHERMIQUE (au-delà du pic de fer).
"""
from __future__ import annotations

import math

# ── CONSTANTE SOURCÉE ──────────────────────────────────────────────────────────────────────────────────────────
# Équivalence masse↔énergie de l'unité de masse atomique unifiée : 1 u·c² = 931.494 MeV (CODATA, valeur du sujet).
U_EN_MEV = 931.494  # MeV par unité de masse atomique (1 u = 931.494 MeV/c²)

# ── FAIT ÉTABLI : PIC DE FER (courbe d'Aston) ──────────────────────────────────────────────────────────────────
# ⁵⁶Fe est au sommet de la courbe énergie de liaison par nucléon : E_l(56Fe) = 492.254 MeV -> /56 = 8.7903 MeV.
# C'est la raison physique pour laquelle la fusion libère de l'énergie jusqu'au fer puis la fission au-delà.
_PIC_FER = {"nuclide": "Fe-56", "Z": 26, "A": 56,
            "energie_liaison_MeV": 492.254, "energie_par_nucleon_MeV": 8.7903}


def _num(x) -> float:
    """Valide un scalaire réel fini (rejette bool, non numérique, NaN, inf). -> float, sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"valeur non numérique : {x!r}")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"valeur non finie : {x!r}")
    return f


def energie_liaison(defaut_masse_u: float) -> float:
    """Énergie de liaison d'un noyau à partir de son défaut de masse Δm (en u).

    E_liaison = Δm · 931.494  (MeV).  Le défaut de masse est la masse « manquante » convertie en énergie
    de cohésion ; il est par définition POSITIF (ou nul). Δm < 0 -> ValueError (jamais un nombre faux).

    Ex. ⁴He : Δm ≈ 0.0304 u -> E ≈ 28.3 MeV.
    """
    dm = _num(defaut_masse_u)
    if dm < 0:
        raise ValueError(f"défaut de masse négatif impossible : {dm}")
    return dm * U_EN_MEV


def energie_liaison_par_nucleon(E_liaison: float, A: int) -> float:
    """Énergie de liaison par nucléon = E_liaison / A (MeV/nucléon).

    A = nombre de masse (nucléons) : entier strictement positif. A non entier-positif -> ValueError.
    E_liaison < 0 (énergie de cohésion) -> ValueError.

    Ex. ⁴He : 28.3 MeV / 4 ≈ 7.07 MeV/nucléon ; sommet ⁵⁶Fe ≈ 8.79 MeV/nucléon.
    """
    el = _num(E_liaison)
    if el < 0:
        raise ValueError(f"énergie de liaison négative impossible : {el}")
    if isinstance(A, bool) or not isinstance(A, int):
        raise ValueError(f"nombre de masse A doit être un entier : {A!r}")
    if A <= 0:
        raise ValueError(f"nombre de masse A doit être strictement positif : {A}")
    return el / A


def q_reaction(masse_reactifs_u: float, masse_produits_u: float) -> float:
    """Énergie Q d'une réaction nucléaire (MeV) à partir des masses totales (en u).

    Q = (Σ masses réactifs − Σ masses produits) · 931.494.
        Q > 0 -> exothermique (ex. fusion D+T→⁴He+n ≈ +17.6 MeV) ; Q < 0 -> endothermique.

    Les masses totales sont des grandeurs physiques strictement positives : ≤ 0 -> ValueError.
    """
    mr = _num(masse_reactifs_u)
    mp = _num(masse_produits_u)
    if mr <= 0:
        raise ValueError(f"masse totale des réactifs doit être > 0 : {mr}")
    if mp <= 0:
        raise ValueError(f"masse totale des produits doit être > 0 : {mp}")
    return (mr - mp) * U_EN_MEV


def pic_fer() -> dict:
    """FAIT : ⁵⁶Fe est au sommet de la courbe d'énergie de liaison par nucléon (≈ 8.79 MeV/nucléon).

    Renvoie une COPIE du fait (nuclide, Z, A, énergie de liaison totale et par nucléon). C'est le pivot de la
    nucléosynthèse stellaire : fusion exothermique jusqu'au fer, puis seule la fission/capture libère de l'énergie.
    """
    return dict(_PIC_FER)
