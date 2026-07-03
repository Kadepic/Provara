"""
POLYMÈRES / PLASTIQUES — identification et propriétés (mandat Yohan : « tous les sujets bornés, FAUX=0 »).

Domaine BORNÉ par des CONVENTIONS et des FAITS établis :
  • le CODE D'IDENTIFICATION DES RÉSINES (Resin Identification Code, ASTM D7611 / norme SPI) est une
    CONVENTION fixe : PET=1, PEHD(HDPE)=2, PVC=3, PEBD(LDPE)=4, PP=5, PS=6, autres=7 ;
  • la classe THERMIQUE (thermoplastique refondable vs thermodurcissable réticulé irréversible) est une
    propriété ÉTABLIE de chaque polymère ;
  • la TEMPÉRATURE DE TRANSITION VITREUSE (Tg) est une DONNÉE SOURCÉE (valeur représentative de la
    littérature ; varie légèrement selon la source et la cristallinité) — rendue pour quelques polymères.

GARANTIES (vérifiées en adverse par valide_plastiques.py) :
  - le MÉCANISME (table de conventions + normalisation tolérante des noms) est EXACT ;
  - plastique / code HORS du référentiel connu -> ValueError (abstention) : JAMAIS une réponse inventée ;
  - un polymère générique sans code unique (PE = PEHD ou PEBD ?) ou sans classe (« autres ») -> ValueError ;
  - déterministe.

SOURCES :
  - code de recyclage : ASTM D7611 (ex-SPI Resin Identification Code), convention internationale ;
  - classe thermique : définition matériaux (thermoplastique vs thermodurcissable) ;
  - Tg : valeurs représentatives de la littérature des polymères (PS ~100 °C, etc.).
"""
from __future__ import annotations

import re
import unicodedata

# --- Référentiel des polymères ------------------------------------------------
# code : code de recyclage (1..7) ; None = pas de code unique défini (PE générique, thermodurcissables, "autres").
# thermo : "thermoplastique" | "thermodurcissable" | None (None = catégorie générique sans classe propre).
# complet : nom développé (fait/convention de nomenclature).
# tg : température de transition vitreuse en °C (donnée sourcée), absente si non répertoriée.
PLASTIQUES = {
    # --- Codes 1 à 6 (conventionnels) ---
    "PET":  {"code": 1, "thermo": "thermoplastique", "complet": "polyéthylène téréphtalate", "tg": 70.0},
    "PEHD": {"code": 2, "thermo": "thermoplastique", "complet": "polyéthylène haute densité"},
    "PVC":  {"code": 3, "thermo": "thermoplastique", "complet": "polychlorure de vinyle", "tg": 80.0},
    "PEBD": {"code": 4, "thermo": "thermoplastique", "complet": "polyéthylène basse densité"},
    "PP":   {"code": 5, "thermo": "thermoplastique", "complet": "polypropylène"},
    "PS":   {"code": 6, "thermo": "thermoplastique", "complet": "polystyrène", "tg": 100.0},
    # --- Code 7 « autres » : thermoplastiques techniques classés sous la catégorie 7 ---
    "PC":   {"code": 7, "thermo": "thermoplastique", "complet": "polycarbonate", "tg": 147.0},
    "ABS":  {"code": 7, "thermo": "thermoplastique", "complet": "acrylonitrile butadiène styrène"},
    "PMMA": {"code": 7, "thermo": "thermoplastique", "complet": "polyméthacrylate de méthyle", "tg": 105.0},
    "PA":   {"code": 7, "thermo": "thermoplastique", "complet": "polyamide"},
    "PLA":  {"code": 7, "thermo": "thermoplastique", "complet": "acide polylactique", "tg": 60.0},
    "PTFE": {"code": 7, "thermo": "thermoplastique", "complet": "polytétrafluoroéthylène"},
    # --- Polyéthylène générique : thermoplastique, MAIS pas de code unique (2 ou 4) ---
    "PE":   {"code": None, "thermo": "thermoplastique", "complet": "polyéthylène"},
    # --- Thermodurcissables (réticulés, non refondables) : pas de code de recyclage standard ---
    "BAKELITE":           {"code": None, "thermo": "thermodurcissable", "complet": "résine phénol-formaldéhyde (bakélite)"},
    "EPOXY":              {"code": None, "thermo": "thermodurcissable", "complet": "résine époxyde"},
    "MELAMINE":           {"code": None, "thermo": "thermodurcissable", "complet": "résine mélamine-formaldéhyde"},
    "PHENOPLASTE":        {"code": None, "thermo": "thermodurcissable", "complet": "résine phénoplaste (phénol-formaldéhyde)"},
    "POLYESTERINSATURE":  {"code": None, "thermo": "thermodurcissable", "complet": "polyester insaturé"},
    # --- Catégorie 7 en tant que NOM (« autres ») : code 7, mais pas de classe thermique propre ---
    "AUTRES": {"code": 7, "thermo": None, "complet": "autres plastiques (catégorie 7)"},
}

# Aliases (formes normalisées -> clé canonique). La clé canonique elle-même est ajoutée plus bas.
_ALIAS_BRUT = {
    "PET":  ["PETE", "polyéthylène téréphtalate", "polytéréphtalate d'éthylène"],
    "PEHD": ["HDPE", "polyéthylène haute densité", "polyethylene haute densite"],
    "PVC":  ["V", "polychlorure de vinyle", "chlorure de polyvinyle", "polyvinyl chloride"],
    "PEBD": ["LDPE", "polyéthylène basse densité", "polyethylene basse densite"],
    "PP":   ["polypropylène", "polypropylene"],
    "PS":   ["polystyrène", "polystyrene"],
    "PC":   ["polycarbonate"],
    "ABS":  ["acrylonitrile butadiène styrène", "acrylonitrile butadiene styrene"],
    "PMMA": ["polyméthacrylate de méthyle", "plexiglas", "PMMA"],
    "PA":   ["polyamide", "nylon"],
    "PLA":  ["acide polylactique", "polylactide"],
    "PTFE": ["polytétrafluoroéthylène", "téflon", "teflon"],
    "PE":   ["polyéthylène", "polyethylene", "polyéthène"],
    "BAKELITE":          ["bakélite", "bakelite"],
    "EPOXY":             ["époxy", "époxyde", "résine époxy", "résine époxyde"],
    "MELAMINE":          ["mélamine", "résine mélamine"],
    "PHENOPLASTE":       ["phénoplaste", "phénol-formaldéhyde"],
    "POLYESTERINSATURE": ["polyester insaturé", "UP"],
    "AUTRES":            ["autres", "autre", "other", "divers"],
}

# Nom de chaque code de recyclage (convention ASTM D7611 / SPI).
_CODE_NOM = {1: "PET", 2: "PEHD", 3: "PVC", 4: "PEBD", 5: "PP", 6: "PS", 7: "autres"}


def _norme(s):
    """Normalise un nom : sans accents, majuscules, seulement [A-Z0-9]. ValueError si non-str."""
    if not isinstance(s, str):
        raise ValueError(f"nom de plastique invalide (attendu str) : {s!r}")
    d = unicodedata.normalize("NFD", s)
    d = "".join(c for c in d if unicodedata.category(c) != "Mn")  # ôte les diacritiques
    return re.sub(r"[^A-Z0-9]", "", d.upper())


# Table d'alias normalisée -> clé canonique (construite une fois).
_ALIAS = {}
for _cle in PLASTIQUES:
    _ALIAS[_norme(_cle)] = _cle
for _cle, _formes in _ALIAS_BRUT.items():
    for _f in _formes:
        _ALIAS[_norme(_f)] = _cle


def _resout(nom):
    """Résout un nom de plastique vers sa clé canonique. ValueError si hors référentiel."""
    cle = _norme(nom)
    if cle not in _ALIAS:
        raise ValueError(f"plastique inconnu du référentiel : {nom!r}")
    return _ALIAS[cle]


def code_recyclage(plastique):
    """Code d'identification de résine (1..7) du plastique. ValueError si inconnu ou sans code unique."""
    fiche = PLASTIQUES[_resout(plastique)]
    code = fiche["code"]
    if code is None:
        raise ValueError(f"pas de code de recyclage unique défini pour {plastique!r}")
    return code


def nom_depuis_code(n):
    """Nom conventionnel du code de recyclage (1->PET ... 7->autres). ValueError sinon."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"code de recyclage invalide (attendu entier 1..7) : {n!r}")
    if n not in _CODE_NOM:
        raise ValueError(f"code de recyclage hors plage 1..7 : {n}")
    return _CODE_NOM[n]


def classe_thermique(nom):
    """'thermoplastique' ou 'thermodurcissable'. ValueError si inconnu / sans classe propre."""
    t = PLASTIQUES[_resout(nom)]["thermo"]
    if t is None:
        raise ValueError(f"pas de classe thermique propre pour {nom!r}")
    return t


def est_thermoplastique(nom):
    """True si le polymère est thermoplastique (refondable). ValueError si inconnu."""
    return classe_thermique(nom) == "thermoplastique"


def est_thermodurcissable(nom):
    """True si le polymère est thermodurcissable (réticulé, non refondable). ValueError si inconnu."""
    return classe_thermique(nom) == "thermodurcissable"


def temperature_transition_vitreuse(nom):
    """Tg en °C (donnée sourcée, valeur représentative). ValueError si inconnu / non répertoriée."""
    fiche = PLASTIQUES[_resout(nom)]
    if "tg" not in fiche:
        raise ValueError(f"Tg non répertoriée pour {nom!r}")
    return fiche["tg"]


def nom_complet(nom):
    """Nom développé du polymère (nomenclature). ValueError si inconnu."""
    return PLASTIQUES[_resout(nom)]["complet"]
