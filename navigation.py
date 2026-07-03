"""NAVIGATION — orientation & positionnement sur le globe, FAUX=0 (mission formule/concept).

Distance ORTHODROMIQUE (grand cercle) par la formule de HAVERSINE :
    a = sin²(Δφ/2) + cos φ₁·cos φ₂·sin²(Δλ/2)
    d = 2·R·asin(√a)            (R = 6371 km, rayon volumétrique moyen de la Terre, UGGI/IUGG)
CAP INITIAL (azimut de départ de l'orthodromie) :
    θ = atan2( sin Δλ·cos φ₂ , cos φ₁·sin φ₂ − sin φ₁·cos φ₂·cos Δλ )   ramené à [0, 360°[.

Mécanisme EXACT (sphère), fonctions PURES déterministes, sortie 6 chiffres significatifs.
Abstention STRUCTURELLE (jamais un faux) : latitude hors [−90, 90], longitude hors [−180, 180],
entrée non numérique -> ValueError.

Couvre le sujet borné « Navigation (orientation, positionnement) ».
Vérifié en adverse par `valide_navigation.py` (Paris→Londres ≈ 344 km, quart d'équateur ≈ 10007 km,
caps cardinaux 0/90/180/270, soundness des bornes lat/lon).
"""
from __future__ import annotations

import math

_R_TERRE_KM = 6371.0  # rayon moyen de la Terre (km) — convention orthodromie/haversine
_SIG = 6


def _sig(x):
    """Arrondi à 6 chiffres significatifs (0.0 reste 0.0)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def _valide_coord(lat, lon):
    _num(lat, lon)
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"latitude hors [-90, 90] : {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"longitude hors [-180, 180] : {lon}")


def distance_orthodromique(lat1, lon1, lat2, lon2) -> float:
    """Distance du grand cercle (km) entre deux points, formule de haversine, R = 6371 km."""
    _valide_coord(lat1, lon1)
    _valide_coord(lat2, lon2)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    # a peut dépasser 1 d'un epsilon flottant pour des antipodes -> on borne avant asin
    a = min(1.0, max(0.0, a))
    d = 2.0 * _R_TERRE_KM * math.asin(math.sqrt(a))
    return _sig(d)


# alias explicite demandé par la spécification
def haversine(lat1, lon1, lat2, lon2) -> float:
    """Alias de `distance_orthodromique` (formule de haversine)."""
    return distance_orthodromique(lat1, lon1, lat2, lon2)


def cap_initial(lat1, lon1, lat2, lon2) -> float:
    """Cap initial (azimut vrai, degrés) de l'orthodromie de (lat1,lon1) vers (lat2,lon2), dans [0, 360°[."""
    _valide_coord(lat1, lon1)
    _valide_coord(lat2, lon2)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    theta = math.degrees(math.atan2(y, x))
    return _sig((theta + 360.0) % 360.0)
