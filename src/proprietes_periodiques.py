"""
PROPRIÉTÉS PÉRIODIQUES — rayon atomique et énergie de première ionisation (Z = 1 à 36).

Même posture FAUX=0 que `physique` / `chimie` (la mesure juge, jamais un faux) :
  • Le MÉCANISME est un CATALOGUE DE VALEURS MESURÉES + les TENDANCES établies — PAS une formule prédictive :
      – energie_premiere_ionisation(symbole) : première énergie d'ionisation en kJ/mol, valeurs issues des
        potentiels d'ionisation NIST (eV) convertis par 1 eV = 96,485 kJ/mol, telles que tabulées CRC/NIST.
      – rayon_atomique(symbole) : rayon COVALENT DE LIAISON SIMPLE en picomètres, table de
        Pyykkö & Atsumi (2009). UNE SEULE définition est publiée, et elle est NOMMÉE : c'est le rayon
        covalent (liaison simple), PAS le rayon de van der Waals, PAS le rayon empirique de Slater,
        PAS le rayon ionique. Les valeurs numériques du « rayon atomique » DÉPENDENT de la définition
        choisie (p. ex. H : 32 pm covalent simple vs 120 pm van der Waals) — comparer des rayons issus
        de définitions différentes serait un FAUX.
  • TENDANCES (faits établis, jamais présentés comme des lois strictes) :
      – le long d'une PÉRIODE (gauche -> droite) : le rayon DÉCROÎT, l'énergie d'ionisation CROÎT ;
      – le long d'un GROUPE (haut -> bas) : le rayon CROÎT, l'énergie d'ionisation DÉCROÎT ;
      – ces tendances sont GÉNÉRALES et NON STRICTEMENT MONOTONES : anomalies réelles Be->B (800,6 < 899,5,
        sous-couche 2p entamée) et N->O (1313,9 < 1402,3, appariement dans 2p) — ce module ne prétend
        JAMAIS une monotonie stricte, et ses chaînes de tendance le disent explicitement.

GARANTIES (vérifiées en adverse par `valide_proprietes_periodiques.py`) :
  - élément hors catalogue ('Xx', 'Rb', casse fautive 'he', chaîne vide) -> ValueError :
    JAMAIS d'interpolation, JAMAIS d'extrapolation, JAMAIS de devinette ;
  - symbole non-str (int, bool, None, float, NaN) -> ValueError ;
  - propriété de tendance inconnue -> ValueError (seules 'rayon' et 'ionisation' sont connues) ;
  - compare_* : égalité des valeurs cataloguées -> ValueError (à définition donnée on ne TRANCHE pas
    une égalité de table, ce serait une devinette) ; comparer un élément à lui-même -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que la stdlib (rien).
"""
from __future__ import annotations

SOURCE = (
    "ionisation : NIST Atomic Spectra Database (potentiels en eV, x 96,485 kJ/mol/eV), "
    "telles que tabulées CRC Handbook ; rayon : rayons covalents de liaison simple, "
    "Pyykkö & Atsumi, Chem. Eur. J. 15 (2009) 186-197"
)

RAYON_DEFINITION = "rayon covalent de liaison simple (Pyykkö & Atsumi 2009), en picomètres"

# ── CATALOGUE : première énergie d'ionisation, kJ/mol (NIST/CRC), Z = 1..36 ─────────────────────────────────────
_IONISATION_KJ_MOL: dict[str, float] = {
    "H": 1312.0, "He": 2372.3,
    "Li": 520.2, "Be": 899.5, "B": 800.6, "C": 1086.5, "N": 1402.3,
    "O": 1313.9, "F": 1681.0, "Ne": 2080.7,
    "Na": 495.8, "Mg": 737.7, "Al": 577.5, "Si": 786.5, "P": 1011.8,
    "S": 999.6, "Cl": 1251.2, "Ar": 1520.6,
    "K": 418.8, "Ca": 589.8, "Sc": 633.1, "Ti": 658.8, "V": 650.9,
    "Cr": 652.9, "Mn": 717.3, "Fe": 762.5, "Co": 760.4, "Ni": 737.1,
    "Cu": 745.5, "Zn": 906.4, "Ga": 578.8, "Ge": 762.2, "As": 947.0,
    "Se": 941.0, "Br": 1139.9, "Kr": 1350.8,
}

# ── CATALOGUE : rayon covalent de liaison simple, pm (Pyykkö & Atsumi 2009), Z = 1..36 ──────────────────────────
_RAYON_COVALENT_PM: dict[str, int] = {
    "H": 32, "He": 46,
    "Li": 133, "Be": 102, "B": 85, "C": 75, "N": 71,
    "O": 63, "F": 64, "Ne": 67,
    "Na": 155, "Mg": 139, "Al": 126, "Si": 116, "P": 111,
    "S": 103, "Cl": 99, "Ar": 96,
    "K": 196, "Ca": 171, "Sc": 148, "Ti": 136, "V": 134,
    "Cr": 122, "Mn": 119, "Fe": 116, "Co": 111, "Ni": 110,
    "Cu": 112, "Zn": 118, "Ga": 124, "Ge": 121, "As": 121,
    "Se": 116, "Br": 114, "Kr": 117,
}

# ── TENDANCES établies (faits, jamais des monotonies strictes) ──────────────────────────────────────────────────
_TENDANCES: dict[tuple[str, str], str] = {
    ("rayon", "periode"): (
        "le rayon atomique DÉCROÎT de gauche à droite le long d'une période "
        "(tendance générale, non strictement monotone : la charge nucléaire effective augmente)"
    ),
    ("rayon", "groupe"): (
        "le rayon atomique CROÎT du haut vers le bas le long d'un groupe "
        "(tendance générale : une couche électronique s'ajoute à chaque période)"
    ),
    ("ionisation", "periode"): (
        "l'énergie de première ionisation CROÎT de gauche à droite le long d'une période "
        "(tendance générale, NON strictement monotone : anomalies réelles Be->B et N->O)"
    ),
    ("ionisation", "groupe"): (
        "l'énergie de première ionisation DÉCROÎT du haut vers le bas le long d'un groupe "
        "(tendance générale : l'électron externe s'éloigne du noyau et est plus écranté)"
    ),
}


def _exige_symbole(s, catalogue: dict) -> str:
    """Symbole chimique EXACT (casse comprise) présent au catalogue, sinon ValueError (abstention)."""
    if not isinstance(s, str):
        raise ValueError("symbole invalide : une chaîne ('H', 'Fe', ...) est requise")
    if s not in catalogue:
        raise ValueError(
            f"élément {s!r} hors catalogue (Z=1..36, casse exacte) : abstention — "
            "jamais d'interpolation ni de devinette"
        )
    return s


# ── VALEURS MESURÉES ────────────────────────────────────────────────────────────────────────────────────────────
def energie_premiere_ionisation(symbole: str) -> float:
    """Première énergie d'ionisation (kJ/mol, NIST/CRC) de l'élément. Hors catalogue -> ValueError.

    Valeur MESURÉE tabulée (4 chiffres significatifs ou plus) — pas un calcul."""
    s = _exige_symbole(symbole, _IONISATION_KJ_MOL)
    return _IONISATION_KJ_MOL[s]


def rayon_atomique(symbole: str) -> float:
    """Rayon covalent de liaison simple (pm, Pyykkö & Atsumi 2009). Hors catalogue -> ValueError.

    ATTENTION : c'est LE rayon covalent (liaison simple) — une AUTRE définition (van der Waals,
    empirique, ionique) donnerait d'AUTRES nombres. Cette définition-ci est la seule publiée ici."""
    s = _exige_symbole(symbole, _RAYON_COVALENT_PM)
    return float(_RAYON_COVALENT_PM[s])


# ── TENDANCES ───────────────────────────────────────────────────────────────────────────────────────────────────
def _exige_prop(prop) -> str:
    if not isinstance(prop, str) or prop not in ("rayon", "ionisation"):
        raise ValueError("propriété invalide : 'rayon' ou 'ionisation' est requis")
    return prop


def tendance_periode(prop: str) -> str:
    """Tendance ÉTABLIE de la propriété le long d'une période (gauche -> droite).

    Renvoie une phrase qui dit explicitement que la tendance est générale, PAS strictement monotone."""
    return _TENDANCES[(_exige_prop(prop), "periode")]


def tendance_groupe(prop: str) -> str:
    """Tendance ÉTABLIE de la propriété le long d'un groupe (haut -> bas)."""
    return _TENDANCES[(_exige_prop(prop), "groupe")]


# ── COMPARAISONS (sur valeurs cataloguées uniquement) ───────────────────────────────────────────────────────────
def _compare(a, b, catalogue: dict, nom: str) -> str:
    sa = _exige_symbole(a, catalogue)
    sb = _exige_symbole(b, catalogue)
    if sa == sb:
        raise ValueError(f"comparaison dégénérée : {sa!r} comparé à lui-même")
    va, vb = catalogue[sa], catalogue[sb]
    if va == vb:
        raise ValueError(
            f"{nom} catalogués ÉGAUX pour {sa!r} et {sb!r} ({va}) : abstention — "
            "trancher une égalité de table serait une devinette"
        )
    return sa if va > vb else sb


def compare_rayon(a: str, b: str) -> str:
    """Symbole de l'élément au rayon covalent (liaison simple) le PLUS GRAND parmi {a, b}.

    Égalité des valeurs cataloguées ou a == b -> ValueError (abstention : on ne tranche pas)."""
    return _compare(a, b, _RAYON_COVALENT_PM, "rayons covalents")


def compare_ionisation(a: str, b: str) -> str:
    """Symbole de l'élément à l'énergie de première ionisation la PLUS GRANDE parmi {a, b}.

    Égalité des valeurs cataloguées ou a == b -> ValueError (abstention : on ne tranche pas)."""
    return _compare(a, b, _IONISATION_KJ_MOL, "énergies d'ionisation")
