"""
SÉISMOLOGIE — noyau BORNÉ des séismes (magnitude, énergie), lois établies, pur stdlib (2026-07-02).

POURQUOI (sujet borné B-PHY « Séismes » : borné par la physique/mesure) : la relation magnitude<->moment sismique et
magnitude<->énergie sont des LOIS ÉTABLIES (Hanks & Kanamori 1979 ; échelle IASPEI ; Gutenberg-Richter). Calculs
EXACTS et déterministes, aucune donnée-événement inventée (on ne prétend PAS connaître la magnitude d'un séisme
donné — ça, c'est de la donnée à ingérer ; on fournit les CONVERSIONS et la classification conventionnelle).

FAUX=0 :
  • Formules EXACTES : magnitude de moment Mw = (2/3)·(log10(M0) − 9.1), M0 en N·m (standard IASPEI/Hanks-Kanamori) ;
    énergie rayonnée log10(E_J) = 1.5·M + 4.8 (Gutenberg-Richter) ; réciproques exactes.
  • Invariants re-dérivables : +1 magnitude -> ×10 d'amplitude, ×10^1.5 (~31.6) d'énergie.
  • Abstention (ValueError) hors domaine physique : M0 ≤ 0, argument non fini.
  • Classification (`classe`) = référentiel FERMÉ sourcé (USGS), pas une opinion ; hors échelle -> ValueError.
Souverain, offline, stdlib pur.
"""
from __future__ import annotations

import math

_C_MW = 9.1               # constante IASPEI (M0 en N·m)
_A_E, _B_E = 1.5, 4.8     # log10(E_joules) = 1.5·M + 4.8 (Gutenberg-Richter)


def _fini(x, nom):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{nom} doit être un nombre fini (vu {x!r})")
    return float(x)


def magnitude_moment(moment_sismique) -> float:
    """Mw = (2/3)·(log10(M0) − 9.1), M0 = moment sismique scalaire en N·m (> 0)."""
    m0 = _fini(moment_sismique, "moment_sismique")
    if m0 <= 0:
        raise ValueError("moment sismique doit être > 0 N·m")
    return (2.0 / 3.0) * (math.log10(m0) - _C_MW)


def moment_depuis_magnitude(mw) -> float:
    """Réciproque exacte : M0 = 10^(1.5·Mw + 9.1) N·m."""
    mw = _fini(mw, "mw")
    return 10 ** (1.5 * mw + _C_MW)


def energie_joules(magnitude) -> float:
    """Énergie sismique rayonnée E = 10^(1.5·M + 4.8) joules (Gutenberg-Richter)."""
    m = _fini(magnitude, "magnitude")
    return 10 ** (_A_E * m + _B_E)


def magnitude_depuis_energie(energie) -> float:
    """Réciproque : M = (log10(E) − 4.8) / 1.5, E en joules (> 0)."""
    e = _fini(energie, "energie")
    if e <= 0:
        raise ValueError("énergie doit être > 0 J")
    return (math.log10(e) - _B_E) / _A_E


def rapport_amplitude(m1, m2) -> float:
    """Rapport d'amplitude entre deux magnitudes : 10^(m1 − m2) (définition logarithmique de l'échelle)."""
    return 10 ** (_fini(m1, "m1") - _fini(m2, "m2"))


def rapport_energie(m1, m2) -> float:
    """Rapport d'énergie entre deux magnitudes : 10^(1.5·(m1 − m2)) (~31.6× par unité)."""
    return 10 ** (_A_E * (_fini(m1, "m1") - _fini(m2, "m2")))


# Classification descriptive USGS (référentiel fermé, bornes conventionnelles).
_CLASSES = (
    (2.0, "micro"),
    (4.0, "mineur"),
    (5.0, "léger"),
    (6.0, "modéré"),
    (7.0, "fort"),
    (8.0, "majeur"),
    (float("inf"), "exceptionnel"),
)


def classe(magnitude) -> str:
    """Catégorie descriptive USGS d'une magnitude (< 2 micro … ≥ 8 exceptionnel). Hors plausible [-2, 12] -> ValueError."""
    m = _fini(magnitude, "magnitude")
    if not (-2.0 <= m <= 12.0):
        raise ValueError(f"magnitude {m} hors échelle plausible [-2, 12]")
    for borne, nom in _CLASSES:
        if m < borne:
            return nom
    return "exceptionnel"
