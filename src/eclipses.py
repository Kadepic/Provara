"""
eclipses.py — Mécanique des phases lunaires et conditions d'éclipse.

Mécanismes EXACTS / établis (géométrie élémentaire + définitions astronomiques conventionnelles) :

  • periode_synodique(T1, T2) = 1 / |1/T1 − 1/T2|
      Période de reconjonction de deux mobiles de périodes T1, T2 (formule du mouvement
      synodique). Ex. Lune (T=27.32 j) / Soleil-apparent (T=365.25 j) -> mois synodique ≈ 29.53 j.

  • phase_lune(angle_elongation_deg) : nom de phase selon l'élongation (angle Soleil-Terre-Lune),
      convention standard à 8 phases. Cardinaux : 0->'nouvelle', 90->'premier_quartier',
      180->'pleine', 270->'dernier_quartier' ; intervalles -> croissant/gibbeuse.

  • fraction_illuminee(angle) = (1 − cos angle) / 2
      Fraction du disque lunaire éclairée vue de la Terre. 0°->0, 90°->0.5, 180°->1.

  • condition_eclipse(latitude_lune_deg, seuil=1.5) = (|latitude| < seuil)
      Une éclipse n'est possible que si la Lune est assez proche d'un nœud de son orbite
      (faible latitude écliptique). Renvoie un booléen.

ABSTENTION STRUCTURELLE (faux positif INTERDIT) :
  • T <= 0, ou T1 == T2 (période synodique infinie/indéfinie) -> ValueError.
  • angle hors [0, 360) -> ValueError.
  • latitude hors [-90, 90], seuil <= 0 -> ValueError.

stdlib uniquement.
"""

import math

__all__ = [
    "periode_synodique",
    "phase_lune",
    "fraction_illuminee",
    "condition_eclipse",
]

# Tolérance d'identification des angles cardinaux (un float « 90.0 » reste cardinal).
_EPS = 1e-9


def _verifie_angle(angle):
    """Valide qu'un angle est un réel fini dans [0, 360). Renvoie le float, sinon ValueError."""
    try:
        a = float(angle)
    except (TypeError, ValueError):
        raise ValueError(f"angle non numérique : {angle!r}")
    if not math.isfinite(a):
        raise ValueError(f"angle non fini : {angle!r}")
    if a < 0.0 or a >= 360.0:
        raise ValueError(f"angle hors [0, 360) : {a}")
    return a


def periode_synodique(T1, T2):
    """
    Période synodique = 1 / |1/T1 − 1/T2|.

    T1, T2 : périodes sidérales strictement positives (mêmes unités).
    Renvoie la période synodique dans la même unité.
    T <= 0, non fini, ou T1 == T2 -> ValueError.
    """
    try:
        t1 = float(T1)
        t2 = float(T2)
    except (TypeError, ValueError):
        raise ValueError(f"périodes non numériques : {T1!r}, {T2!r}")
    if not (math.isfinite(t1) and math.isfinite(t2)):
        raise ValueError("période non finie")
    if t1 <= 0.0 or t2 <= 0.0:
        raise ValueError(f"période non strictement positive : T1={t1}, T2={t2}")
    diff = abs(1.0 / t1 - 1.0 / t2)
    if diff == 0.0:
        # T1 == T2 : aucune reconjonction relative -> période infinie, indéfinie.
        raise ValueError("T1 == T2 : période synodique indéfinie (infinie)")
    return 1.0 / diff


def phase_lune(angle_elongation_deg):
    """
    Nom de la phase lunaire selon l'élongation (deg), convention 8 phases.

    0  -> 'nouvelle'
    ]0,90[   -> 'premier_croissant'   (croissant montant)
    90 -> 'premier_quartier'
    ]90,180[ -> 'gibbeuse_croissante'
    180-> 'pleine'
    ]180,270[-> 'gibbeuse_decroissante'
    270-> 'dernier_quartier'
    ]270,360[-> 'dernier_croissant'

    angle hors [0,360) -> ValueError.
    """
    a = _verifie_angle(angle_elongation_deg)
    if abs(a - 0.0) < _EPS:
        return "nouvelle"
    if abs(a - 90.0) < _EPS:
        return "premier_quartier"
    if abs(a - 180.0) < _EPS:
        return "pleine"
    if abs(a - 270.0) < _EPS:
        return "dernier_quartier"
    if a < 90.0:
        return "premier_croissant"
    if a < 180.0:
        return "gibbeuse_croissante"
    if a < 270.0:
        return "gibbeuse_decroissante"
    return "dernier_croissant"


def fraction_illuminee(angle_elongation_deg):
    """
    Fraction illuminée du disque lunaire = (1 − cos(angle)) / 2.

    Renvoie un réel dans [0, 1]. 0°->0, 90°->0.5, 180°->1.
    angle hors [0,360) -> ValueError.
    """
    a = _verifie_angle(angle_elongation_deg)
    f = (1.0 - math.cos(math.radians(a))) / 2.0
    # Bornage numérique strict (clamp d'arrondi flottant).
    if f < 0.0:
        f = 0.0
    elif f > 1.0:
        f = 1.0
    return f


def condition_eclipse(latitude_lune_deg, seuil=1.5):
    """
    Éclipse géométriquement possible ssi |latitude écliptique de la Lune| < seuil.

    latitude_lune_deg : latitude écliptique de la Lune en degrés, dans [-90, 90].
    seuil : demi-largeur de la zone d'éclipse autour d'un nœud (> 0), défaut 1.5°.
    Renvoie un booléen. latitude hors [-90,90] ou seuil <= 0 -> ValueError.
    """
    try:
        lat = float(latitude_lune_deg)
        s = float(seuil)
    except (TypeError, ValueError):
        raise ValueError(f"paramètres non numériques : {latitude_lune_deg!r}, {seuil!r}")
    if not (math.isfinite(lat) and math.isfinite(s)):
        raise ValueError("paramètre non fini")
    if lat < -90.0 or lat > 90.0:
        raise ValueError(f"latitude hors [-90, 90] : {lat}")
    if s <= 0.0:
        raise ValueError(f"seuil non strictement positif : {s}")
    return abs(lat) < s
