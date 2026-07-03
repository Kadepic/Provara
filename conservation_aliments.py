"""
CONSERVATION DES ALIMENTS — catalogue de méthodes et seuils ÉTABLIS (mandat Yohan : « tous les sujets bornés,
chirurgical, FAUX=0 »).

Domaine BORNÉ par des conventions et faits SOURCÉS et certains (microbiologie alimentaire / réglementation
hygiène / HACCP). On ne calcule rien d'inventé : on restitue des paramètres établis, et toute entrée hors
référentiel -> abstention (ValueError).

  1) MÉTHODES DE CONSERVATION (principe physico-microbiologique + paramètre de référence) :
        refrigeration      froid positif, ralentit la prolifération microbienne          0 à 4 °C
        congelation        froid négatif, eau cristallisée -> croissance arrêtée          -18 °C
        pasteurisation     chauffage modéré, détruit les formes végétatives (pas spores)  72 °C / 15 s (HTST)
        sterilisation/UHT  chauffage très haute température, détruit aussi les spores      135 °C (quelques s)
        sechage            abaisse l'activité de l'eau (aw) par déshydratation
        salaison           abaisse l'aw par le sel (pression osmotique)
        fumage             composés antimicrobiens de la fumée + déshydratation de surface
        appertisation      traitement thermique en récipient hermétiquement clos (conserve)

  2) ZONE DE DANGER TEMPÉRATURE — entre +4 °C et +63 °C la prolifération bactérienne est rapide (fait
     HACCP / réglementation : liaison froide ≤ 4 °C, liaison chaude ≥ 63 °C). zone_danger_temperature() = (4, 63).

  3) ACTIVITÉ DE L'EAU (aw) — la plupart des bactéries sont inhibées si aw < 0.91 (seuil de microbiologie
     alimentaire ; les principes du séchage / de la salaison reposent sur l'abaissement de l'aw).

GARANTIES (vérifiées en adverse par `valide_conservation_aliments.py`) :
  - méthode hors catalogue / entrée non textuelle / chaîne vide -> ValueError (jamais une méthode devinée) ;
  - activité de l'eau hors [0, 1] / non numérique / non finie / booléenne -> ValueError (jamais un faux) ;
  - sorties déterministes ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

import math
import unicodedata
from collections import namedtuple

SOURCE = ("microbiologie alimentaire + réglementation hygiène / HACCP "
          "(méthodes de conservation, zone de danger température, activité de l'eau)")

# Description d'une méthode : nom canonique, principe, paramètre de référence (texte), et données numériques
# établies (température caractéristique, plage de température, durée). None là où il n'y a pas de valeur unique.
Methode = namedtuple("Methode", ["nom", "principe", "parametre", "temperature_c", "plage_c", "duree_s"])

# Zone de danger : prolifération bactérienne rapide entre min_c et max_c (°C).
ZoneDanger = namedtuple("ZoneDanger", ["min_c", "max_c"])

# Seuil d'activité de l'eau : la plupart des bactéries sont inhibées en dessous (microbiologie alimentaire).
SEUIL_AW_BACTERIES = 0.91

# Bornes établies de la zone de danger température (°C) — fait HACCP / réglementation.
_ZONE_DANGER = ZoneDanger(4, 63)

# Catalogue SOURCÉ. Clé = nom canonique normalisé (minuscules, sans accents). Méthode absente -> abstention.
_CATALOGUE = {
    "refrigeration": Methode(
        "refrigeration",
        "Froid positif : ralentit la prolifération microbienne sans la stopper (les micro-organismes survivent).",
        "0 à 4 °C",
        None, (0.0, 4.0), None),
    "congelation": Methode(
        "congelation",
        "Froid négatif : l'eau cristallise et devient indisponible, la croissance microbienne est arrêtée "
        "(germes non détruits, en dormance).",
        "-18 °C",
        -18.0, None, None),
    "pasteurisation": Methode(
        "pasteurisation",
        "Chauffage modéré : détruit les formes végétatives des micro-organismes ; les spores survivent "
        "(produit non stérile).",
        "72 °C pendant 15 s (HTST, haute température courte durée)",
        72.0, None, 15.0),
    "sterilisation/uht": Methode(
        "sterilisation/uht",
        "Chauffage à très haute température : détruit tous les micro-organismes, spores comprises (produit "
        "stérile).",
        "135 °C pendant quelques secondes (UHT, ultra-haute température)",
        135.0, None, None),
    "sechage": Methode(
        "sechage",
        "Déshydratation : abaisse l'activité de l'eau (aw), ce qui inhibe la croissance microbienne.",
        "abaissement de l'activité de l'eau (aw)",
        None, None, None),
    "salaison": Methode(
        "salaison",
        "Ajout de sel : abaisse l'activité de l'eau par pression osmotique, inhibant les micro-organismes.",
        "apport de chlorure de sodium (sel)",
        None, None, None),
    "fumage": Methode(
        "fumage",
        "Fumée de combustion du bois : composés antimicrobiens (phénols, aldéhydes) et déshydratation de "
        "surface.",
        "exposition à la fumée",
        None, None, None),
    "appertisation": Methode(
        "appertisation",
        "Traitement thermique en récipient hermétiquement clos : permet la conservation longue à température "
        "ambiante (conserve, procédé d'Appert).",
        "chauffage stérilisant en contenant étanche (conserve)",
        None, None, None),
}

# Synonymes stricts (réfèrent EXACTEMENT à la même entrée). On reste conservateur : pas de synonyme ambigu.
_ALIAS = {
    "uht": "sterilisation/uht",
}


def _normalise(nom) -> str:
    """Normalise un nom de méthode : texte -> minuscules, sans accents, espaces réduits. Lève sinon."""
    if isinstance(nom, bool) or not isinstance(nom, str):
        raise ValueError(f"nom de méthode non textuel ({nom!r})")
    # Retire les accents (NFD puis suppression des diacritiques) pour tolérer « réfrigération ».
    decompose = unicodedata.normalize("NFD", nom)
    sans_accent = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    cle = " ".join(sans_accent.lower().split())
    if not cle:
        raise ValueError("nom de méthode vide")
    return cle


def methode(nom) -> Methode:
    """Renvoie la description ÉTABLIE d'une méthode de conservation (principe + paramètre).

    Méthode hors catalogue / entrée invalide -> ValueError (abstention, jamais une méthode devinée).
    """
    cle = _normalise(nom)
    cle = _ALIAS.get(cle, cle)
    if cle not in _CATALOGUE:
        raise ValueError(f"méthode de conservation inconnue ({nom!r})")
    return _CATALOGUE[cle]


def methodes() -> tuple:
    """Liste triée des noms canoniques des méthodes du catalogue."""
    return tuple(sorted(_CATALOGUE))


def zone_danger_temperature() -> ZoneDanger:
    """Zone de danger température (°C) : prolifération bactérienne rapide entre 4 et 63 °C (fait HACCP)."""
    return _ZONE_DANGER


def dans_zone_danger(temperature_c) -> bool:
    """True ssi la température (°C) est dans la zone de danger ]4, 63[ (bornes exclues : ≤4 froid, ≥63 chaud).

    Température non numérique / non finie / booléenne -> ValueError.
    """
    t = _reel(temperature_c, "temperature_c")
    return _ZONE_DANGER.min_c < t < _ZONE_DANGER.max_c


def activite_eau_limite() -> float:
    """Seuil d'activité de l'eau : la plupart des bactéries sont inhibées en dessous (aw < 0.91)."""
    return SEUIL_AW_BACTERIES


def bacteries_inhibees(aw) -> bool:
    """True ssi l'activité de l'eau inhibe la plupart des bactéries (aw < 0.91, seuil strict).

    aw hors de [0, 1] / non numérique / non finie / booléenne -> ValueError (jamais un faux).
    """
    a = _reel(aw, "aw")
    if not (0.0 <= a <= 1.0):
        raise ValueError(f"activité de l'eau hors de [0, 1] ({aw!r})")
    return a < SEUIL_AW_BACTERIES


def _reel(x, nom: str) -> float:
    """Renvoie le flottant fini réel ou lève ValueError (pas de coercition de chaîne, pas de booléen/NaN/inf)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : valeur non numérique ({x!r})")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"{nom} : valeur non finie ({x!r})")
    return v
