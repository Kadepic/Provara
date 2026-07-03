"""
HOMÉOSTASIE — régulation par rétroaction négative (domaine BORNÉ, mécanisme EXACT).

L'homéostasie biologique maintient une variable physiologique près d'une CONSIGNE (set-point) au moyen d'une
RÉTROACTION NÉGATIVE : un écart à la consigne déclenche une correction de signe OPPOSÉ qui ramène la variable
vers la consigne. Le MÉCANISME est exactement calculable (algèbre du signe) ; les CONSIGNES physiologiques de
référence sont des DONNÉES sourcées (valeurs usuelles de la physiologie humaine) :
  • glycémie à jeun ≈ 1 g/L (≈ 5 mmol/L) ;
  • température corporelle centrale ≈ 37 °C ;
  • pH du sang artériel ≈ 7,4 (intervalle de référence 7,35–7,45).

CE QUI EST EXACT (sound) :
  • ecart_consigne(valeur, consigne) = valeur − consigne (signe = sens du déséquilibre) ;
  • correction(valeur, consigne, gain) = −gain·(valeur − consigne) : proportionnelle et de signe OPPOSÉ à
    l'écart (rétroaction NÉGATIVE), donc ramène la variable vers la consigne ;
  • est_regule(valeur, consigne, tolerance) = |valeur − consigne| ≤ tolerance (la variable est dans la bande
    régulée autour de la consigne).

GARANTIES (vérifiées en adverse par `valide_homeostasie.py`) :
  - gain < 0 -> ValueError (une rétroaction « négative » exige un gain ≥ 0 ; un gain négatif serait une
    rétroaction POSITIVE qui AMPLIFIE l'écart : jamais accepté) ;
  - tolerance < 0 -> ValueError (une bande de tolérance négative n'a pas de sens) ;
  - entrée non numérique / NaN -> ValueError (jamais deviné) ;
  - fonctions PURES, DÉTERMINISTES. Abstention (ValueError) hors référentiel plutôt qu'un faux.
"""
from __future__ import annotations

import math

SOURCE = "rétroaction négative (physiologie) + consignes usuelles de référence (glycémie/température/pH humains)"

# Consignes physiologiques de référence (valeurs usuelles sourcées de la physiologie humaine).
CONSIGNES = {
    "glycemie_g_par_L": 1.0,        # glycémie à jeun ≈ 1 g/L
    "temperature_corporelle_C": 37.0,  # température centrale ≈ 37 °C
    "pH_sang": 7.4,                 # pH artériel ≈ 7,4
}


def _num(x, nom: str) -> float:
    """Convertit en float fini, sinon ValueError (abstention, jamais un faux)."""
    if isinstance(x, bool):  # bool est un int en Python : on le refuse explicitement
        raise ValueError(f"{nom} : booléen refusé")
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} : valeur non numérique ({x!r})")
    if not math.isfinite(v):
        raise ValueError(f"{nom} : valeur non finie ({x!r})")
    return v


def ecart_consigne(valeur, consigne) -> float:
    """Écart à la consigne = valeur − consigne (signe = sens du déséquilibre). EXACT."""
    return _num(valeur, "valeur") - _num(consigne, "consigne")


def correction(valeur, consigne, gain) -> float:
    """Correction par rétroaction négative = −gain·(valeur − consigne).

    De signe OPPOSÉ à l'écart : si valeur > consigne (écart > 0) la correction est négative (fait diminuer),
    si valeur < consigne (écart < 0) la correction est positive (fait augmenter) : ramène vers la consigne.
    gain >= 0 requis (gain < 0 = rétroaction positive qui amplifie l'écart) -> ValueError.
    """
    g = _num(gain, "gain")
    if g < 0:
        raise ValueError("gain < 0 : ce serait une rétroaction positive (amplifie l'écart)")
    return -g * ecart_consigne(valeur, consigne)


def est_regule(valeur, consigne, tolerance) -> bool:
    """La variable est-elle dans la bande régulée ? |valeur − consigne| <= tolerance.

    tolerance >= 0 requis -> ValueError sinon.
    """
    t = _num(tolerance, "tolerance")
    if t < 0:
        raise ValueError("tolerance < 0 : bande de tolérance négative impossible")
    return abs(ecart_consigne(valeur, consigne)) <= t


def consigne_reference(nom: str) -> float:
    """Consigne physiologique de référence par nom, sinon ValueError (hors référentiel)."""
    if not isinstance(nom, str) or nom not in CONSIGNES:
        raise ValueError(f"consigne inconnue : {nom!r}")
    return CONSIGNES[nom]
