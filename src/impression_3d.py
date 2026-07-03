"""
IMPRESSION 3D (FDM) — paramètres de tranchage CALCULABLES par formule établie (mandat Yohan : couvrir le borné).

Même posture que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la formule géométrique) est EXACT — c'est la garantie structurelle.
  • Les conventions d'unités sont des DONNÉES SOURCÉES, standard du FDM (Fused Deposition Modeling) :
      - dimensions en millimètres (mm), volumes en mm³ ;
      - débit volumique en mm³/s (sortie de buse) ;
      - densité du filament en g/cm³ (1 cm³ = 1000 mm³) ;
      - section du filament circulaire = π·(d/2)².

GARANTIES (vérifiées en adverse par `valide_impression_3d.py`) :
  - paramètre NON numérique / booléen -> ValueError : on ne devine pas une entrée ;
  - hauteur de couche ≤ 0, débit ≤ 0, hauteur d'objet ≤ 0, volume ≤ 0, diamètre ≤ 0, densité ≤ 0 -> ValueError
    (jamais un nombre absurde : pas de division par zéro, pas de longueur/masse négative) ;
  - déterministe ; conservateur (abstention sur le moindre doute, jamais un faux positif).

FORMULES (établies, exactes) :
  - nombre_couches(hauteur_objet, hauteur_couche)   = ceil(hauteur_objet / hauteur_couche)        [couches]
  - temps_impression(volume_mm3, debit_mm3_s)       = volume_mm3 / debit_mm3_s                     [s]
  - masse_filament(volume_mm3, densite_g_cm3)       = (volume_mm3 / 1000) · densite_g_cm3          [g]
  - longueur_filament(volume_mm3, diametre_mm)      = volume_mm3 / (π · (diametre_mm/2)²)          [mm]
"""
from __future__ import annotations

import math

SOURCE = "conventions FDM standard (mm, mm³, mm³/s, g/cm³ ; section filament = π·(d/2)²)"

# Tolérance relative pour absorber le bruit binaire des flottants avant un ceil (ex. 20/0.2 = 99.999… ou 100.000…1).
_EPS_REL = 1e-9


def _nombre(x) -> bool:
    """Vrai si x est un réel (int/float), en EXCLUANT explicitement les booléens."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _exige_positif(nom: str, x) -> float:
    """Renvoie x en float si x est un réel STRICTEMENT positif, sinon ValueError (abstention)."""
    if not _nombre(x):
        raise ValueError(f"{nom} : valeur non numérique ({x!r})")
    if not math.isfinite(x):
        raise ValueError(f"{nom} : valeur non finie ({x!r})")
    if x <= 0:
        raise ValueError(f"{nom} : doit être strictement positif (reçu {x})")
    return float(x)


def nombre_couches(hauteur_objet, hauteur_couche) -> int:
    """Nombre de couches FDM = ceil(hauteur_objet / hauteur_couche). Entier ≥ 1.

    >>> nombre_couches(20, 0.2)
    100
    """
    h = _exige_positif("hauteur_objet", hauteur_objet)
    hc = _exige_positif("hauteur_couche", hauteur_couche)
    n = h / hc
    # Snap à l'entier si le ratio en est indiscernable (bruit flottant) ; sinon ceil exact.
    n_arr = round(n)
    if abs(n - n_arr) <= _EPS_REL * max(1.0, abs(n_arr)):
        return int(n_arr)
    return int(math.ceil(n))


def temps_impression(volume_mm3, debit_mm3_s) -> float:
    """Temps d'impression (s) = volume_mm3 / debit_mm3_s.

    >>> temps_impression(1000, 5)
    200.0
    """
    v = _exige_positif("volume_mm3", volume_mm3)
    d = _exige_positif("debit_mm3_s", debit_mm3_s)
    return v / d


def masse_filament(volume_mm3, densite_g_cm3) -> float:
    """Masse de filament (g) = (volume_mm3 / 1000) · densite_g_cm3. (1 cm³ = 1000 mm³.)

    >>> masse_filament(1000, 1.24)   # PLA, 1 cm³
    1.24
    """
    v = _exige_positif("volume_mm3", volume_mm3)
    rho = _exige_positif("densite_g_cm3", densite_g_cm3)
    return (v / 1000.0) * rho


def longueur_filament(volume_mm3, diametre_mm) -> float:
    """Longueur de filament consommée (mm) = volume_mm3 / (π · (diametre_mm/2)²).

    >>> round(longueur_filament(1000, 1.75), 2)   # filament Ø1.75 mm
    415.75
    """
    v = _exige_positif("volume_mm3", volume_mm3)
    d = _exige_positif("diametre_mm", diametre_mm)
    section = math.pi * (d / 2.0) ** 2
    return v / section


__all__ = ["nombre_couches", "temps_impression", "masse_filament", "longueur_filament", "SOURCE"]
