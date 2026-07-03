"""
teledetection.py — Télédétection (satellites, imagerie).

Mécanismes EXACTS / établis (définitions métrologiques standard de l'observation de la Terre) :

  • resolution_spatiale(largeur_fauchee_m, nb_pixels) = largeur_fauchée / nb_pixels
      Taille au sol d'un pixel (GSD, Ground Sampling Distance), en mètres/pixel.
      La largeur de fauchée (swath) imagée est répartie sur le nombre de détecteurs.
      Ex. fauchée 60 000 m répartie sur 6 000 pixels -> 10 m/pixel.

  • ndvi(proche_infrarouge, rouge) = (NIR − R) / (NIR + R)
      Normalized Difference Vegetation Index (Rouse et al., 1974). Valeur ∈ [−1, 1]
      garantie pour des réflectances NIR ≥ 0 et R ≥ 0 non simultanément nulles.
      Végétation dense -> NDVI élevé (forte réflectance NIR, faible rouge),
      sol nu -> NDVI ≈ 0 (NIR ≈ R), eau/nuage/neige -> NDVI < 0 (NIR < R).
      Ex. NDVI(0.5, 0.1) = 0.4 / 0.6 ≈ 0.6667.

  • resolution_temporelle(periode_revisite_un_satellite_jours, nb_satellites)
        = période_revisite / nb_satellites
      Temps de revisite (cadence d'observation) d'une constellation de N satellites
      également déphasés sur la même orbite : la revisite d'un seul satellite est
      divisée par N. Ex. Sentinel-2 : 10 j (1 satellite) / 2 satellites -> 5 j.

ABSTENTION STRUCTURELLE (faux positif INTERDIT — on lève ValueError plutôt que de mentir) :
  • largeur_fauchee_m <= 0, ou nb_pixels <= 0           -> ValueError.
  • NIR + R == 0 (indice indéfini), ou NIR < 0, ou R < 0 -> ValueError.
  • periode_revisite <= 0, ou nb_satellites <= 0         -> ValueError.
  • toute entrée non numérique ou non finie              -> ValueError.

Fonctions pures, déterministes, stdlib uniquement. Sorties arrondies à 6 décimales.
"""

import math

__all__ = [
    "resolution_spatiale",
    "ndvi",
    "resolution_temporelle",
]

_NDECIMALES = 6


def _reel_fini(x, nom):
    """Convertit x en float fini, sinon ValueError (abstention)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def resolution_spatiale(largeur_fauchee_m, nb_pixels):
    """GSD (m/pixel) = largeur de fauchée / nombre de pixels.

    largeur_fauchee_m > 0 et nb_pixels > 0, sinon ValueError.
    """
    largeur = _reel_fini(largeur_fauchee_m, "largeur_fauchee_m")
    pixels = _reel_fini(nb_pixels, "nb_pixels")
    if largeur <= 0.0:
        raise ValueError(f"largeur_fauchee_m <= 0 : {largeur}")
    if pixels <= 0.0:
        raise ValueError(f"nb_pixels <= 0 : {pixels}")
    return round(largeur / pixels, _NDECIMALES)


def ndvi(proche_infrarouge, rouge):
    """NDVI = (NIR − R) / (NIR + R), valeur dans [−1, 1].

    NIR ≥ 0, R ≥ 0 et NIR + R > 0, sinon ValueError.
    """
    nir = _reel_fini(proche_infrarouge, "proche_infrarouge")
    r = _reel_fini(rouge, "rouge")
    if nir < 0.0:
        raise ValueError(f"proche_infrarouge < 0 : {nir}")
    if r < 0.0:
        raise ValueError(f"rouge < 0 : {r}")
    somme = nir + r
    if somme == 0.0:
        raise ValueError("NIR + R == 0 : NDVI indéfini")
    val = (nir - r) / somme
    # Borne dure : avec NIR>=0, R>=0 le résultat est mathématiquement dans [-1, 1].
    # On la garantit numériquement (jamais hors borne par arrondi flottant).
    if val < -1.0:
        val = -1.0
    elif val > 1.0:
        val = 1.0
    return round(val, _NDECIMALES)


def resolution_temporelle(periode_revisite_un_satellite_jours, nb_satellites):
    """Temps de revisite d'une constellation = revisite_un_satellite / nb_satellites.

    periode_revisite > 0 et nb_satellites > 0, sinon ValueError.
    """
    periode = _reel_fini(periode_revisite_un_satellite_jours,
                         "periode_revisite_un_satellite_jours")
    n = _reel_fini(nb_satellites, "nb_satellites")
    if periode <= 0.0:
        raise ValueError(f"periode_revisite <= 0 : {periode}")
    if n <= 0.0:
        raise ValueError(f"nb_satellites <= 0 : {n}")
    return round(periode / n, _NDECIMALES)
