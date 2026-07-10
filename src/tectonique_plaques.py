"""TECTONIQUE DES PLAQUES — mouvements MESURÉS (géodésie spatiale), catalogue clos, FAUX=0.

Même posture FAUX=0 que `physique` / `galois` (la mesure juge, jamais un faux) :
  • CATALOGUE de FAITS MESURÉS, pas un modèle prédictif :
      – FRONTIÈRES MAJEURES NOMMÉES entre plaques, avec leur TYPE (fait géologique établi) :
          dorsale médio-atlantique  = DIVERGENTE   (Amérique du Nord / Eurasie),
          dorsale est-Pacifique     = DIVERGENTE   (Pacifique / Nazca) — la plus rapide,
          rift est-africain         = DIVERGENTE   (Nubie / Somalie),
          fosse du Japon            = CONVERGENTE  (Pacifique / Okhotsk — subduction),
          Himalaya                  = CONVERGENTE  (Inde / Eurasie — collision continentale),
          faille de San Andreas     = TRANSFORMANTE (Pacifique / Amérique du Nord — coulissage).
      – VITESSES RELATIVES MESURÉES par géodésie spatiale (GPS/DORIS, modèles NUVEL-1A / MORVEL) :
          expansion médio-atlantique ≈ 2.5 cm/an ; dorsale est-Pacifique ≈ 15 cm/an (la plus rapide au monde) ;
          convergence Inde-Eurasie ≈ 5 cm/an ; glissement San Andreas ≈ 3.4 cm/an.
        ⚠ Ces vitesses sont des MOYENNES RÉGIONALES (elles varient le long de la frontière et dans le temps
        géologique) — ce ne sont PAS des constantes universelles. Elles sont marquées APPROCHÉES ici.
        Frontière cataloguée SANS vitesse consolidée (fosse du Japon, rift est-africain) -> ValueError
        (on s'abstient plutôt que d'inventer un chiffre).
  • MÉCANISME arithmétique EXACT (cinématique uniforme) :
        distance (km) = vitesse (cm/an) × durée (Ma) × 10        [1 Ma = 10⁶ an ; 10⁵ cm = 1 km]
        âge (Ma)      = distance (km) / (10 × vitesse (cm/an))
    Calcul mené en `fractions.Fraction` (les flottants d'entrée sont lus via leur écriture décimale, donc
    2.5 vaut exactement 5/2) ; la sortie est ARRONDIE à 10 chiffres significatifs et c'est DIT ici.
  • PHÉNOMÈNES ATTENDUS par type de frontière (géologie classique) :
        divergente    -> dorsale, volcanisme effusif ;
        convergente   -> subduction, séisme profond, chaîne de montagnes ;
        transformante -> séisme superficiel, PAS de volcanisme.

GARANTIES (vérifiées en adverse par `valide_tectonique_plaques.py`) :
  - plaque ou paire de plaques HORS catalogue -> ValueError (abstention structurelle, jamais une devinette) ;
  - même plaque des deux côtés -> ValueError (pas de frontière d'une plaque avec elle-même) ;
  - frontière nommée inconnue -> ValueError ; frontière sans vitesse consolidée -> ValueError ;
  - vitesse ≤ 0, durée ≤ 0, distance ≤ 0 -> ValueError ;
  - types invalides (bool, str là où un nombre est requis, NaN, ±inf, non-str là où un nom est requis)
    -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (fractions, unicodedata).
"""
from __future__ import annotations

import unicodedata
from fractions import Fraction

SOURCE = ("géodésie spatiale GPS/DORIS + modèles cinématiques NUVEL-1A / MORVEL (DeMets et al.) ; "
          "types de frontières = géologie structurale classique (Le Pichon 1968)")

_CHIFFRES_SIGNIFICATIFS = 10

DIVERGENTE = "divergente"
CONVERGENTE = "convergente"
TRANSFORMANTE = "transformante"


# ── helpers internes ─────────────────────────────────────────────────────────────────────────────────────────────
def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _exige_nom(s, quoi: str) -> str:
    """Nom (str non vide) normalisé : accents retirés, casse pliée, espaces/traits unifiés."""
    if not isinstance(s, str) or not s.strip():
        raise ValueError(f"{quoi} invalide : une chaîne non vide est requise, reçu {s!r}")
    d = unicodedata.normalize("NFD", s)
    d = "".join(c for c in d if not unicodedata.combining(c))
    d = d.casefold().replace("-", " ").replace("'", " ").replace("’", " ")
    return " ".join(d.split())


def _exige_positif(x, quoi: str) -> Fraction:
    """Réel (ou Fraction) fini strictement positif -> Fraction EXACTE (float lu via son écriture décimale)."""
    if isinstance(x, bool) or not isinstance(x, (int, float, Fraction)):
        raise ValueError(f"{quoi} invalide : un nombre réel strictement positif est requis, reçu {x!r}")
    if isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")):
            raise ValueError(f"{quoi} invalide : NaN/inf refusés")
        x = Fraction(str(x))  # 2.5 -> 5/2 exactement (écriture décimale, pas le binaire sous-jacent)
    else:
        x = Fraction(x)
    if x <= 0:
        raise ValueError(f"{quoi} invalide : strictement positif requis")
    return x


# ── CATALOGUE (clos) ─────────────────────────────────────────────────────────────────────────────────────────────
# nom normalisé -> (plaque_a, plaque_b, type, vitesse cm/an APPROCHÉE — moyenne régionale — ou None si
# non consolidée dans ce catalogue). Les vitesses sont celles mesurées par géodésie (cf. SOURCE).
_FRONTIERES = {
    "dorsale medio atlantique": ("amerique du nord", "eurasie", DIVERGENTE, Fraction(5, 2)),    # ≈ 2.5 cm/an
    "dorsale est pacifique":    ("pacifique", "nazca", DIVERGENTE, Fraction(15)),               # ≈ 15 cm/an
    "rift est africain":        ("nubie", "somalie", DIVERGENTE, None),
    "fosse du japon":           ("pacifique", "okhotsk", CONVERGENTE, None),
    "himalaya":                 ("inde", "eurasie", CONVERGENTE, Fraction(5)),                  # ≈ 5 cm/an
    "faille de san andreas":    ("pacifique", "amerique du nord", TRANSFORMANTE, Fraction(17, 5)),  # ≈ 3.4 cm/an
}

_PAR_PAIRE = {frozenset((a, b)): (nom, typ) for nom, (a, b, typ, _v) in _FRONTIERES.items()}

_PHENOMENES = {
    DIVERGENTE: "dorsale, volcanisme effusif",
    CONVERGENTE: "subduction, séisme profond, chaîne de montagnes",
    TRANSFORMANTE: "séisme superficiel, pas de volcanisme",
}


# ── ACCESSEURS DU CATALOGUE ──────────────────────────────────────────────────────────────────────────────────────
def frontieres_cataloguees() -> tuple:
    """Noms (normalisés) des frontières majeures du catalogue, triés — catalogue CLOS."""
    return tuple(sorted(_FRONTIERES))


def plaques_cataloguees() -> tuple:
    """Noms (normalisés) des plaques apparaissant dans le catalogue, triés."""
    return tuple(sorted({p for a, b, _t, _v in _FRONTIERES.values() for p in (a, b)}))


# ── (a) TYPE DE FRONTIÈRE ────────────────────────────────────────────────────────────────────────────────────────
def type_frontiere(plaque_a: str, plaque_b: str) -> str:
    """Type de la frontière majeure cataloguée entre deux plaques : 'divergente' | 'convergente' | 'transformante'.

    L'ordre des deux plaques est indifférent. Paire hors catalogue, plaque inconnue, ou même plaque
    des deux côtés -> ValueError (abstention : on ne devine JAMAIS un type de frontière)."""
    a = _exige_nom(plaque_a, "plaque_a")
    b = _exige_nom(plaque_b, "plaque_b")
    if a == b:
        raise ValueError(f"pas de frontière d'une plaque avec elle-même : {a!r}")
    cle = frozenset((a, b))
    if cle not in _PAR_PAIRE:
        raise ValueError(f"paire de plaques hors catalogue : ({a!r}, {b!r}) — abstention")
    return _PAR_PAIRE[cle][1]


def frontiere_entre(plaque_a: str, plaque_b: str) -> str:
    """Nom (normalisé) de la frontière majeure cataloguée entre deux plaques. Hors catalogue -> ValueError."""
    a = _exige_nom(plaque_a, "plaque_a")
    b = _exige_nom(plaque_b, "plaque_b")
    if a == b:
        raise ValueError(f"pas de frontière d'une plaque avec elle-même : {a!r}")
    cle = frozenset((a, b))
    if cle not in _PAR_PAIRE:
        raise ValueError(f"paire de plaques hors catalogue : ({a!r}, {b!r}) — abstention")
    return _PAR_PAIRE[cle][0]


# ── (b) VITESSES MESURÉES ────────────────────────────────────────────────────────────────────────────────────────
def vitesse_mesuree(nom_frontiere: str) -> float:
    """Vitesse relative MESURÉE (cm/an) de la frontière nommée — valeur APPROCHÉE (moyenne régionale).

    Frontière inconnue -> ValueError ; frontière cataloguée mais sans vitesse consolidée ici
    (fosse du Japon, rift est-africain) -> ValueError (abstention, jamais un chiffre inventé)."""
    nom = _exige_nom(nom_frontiere, "nom_frontiere")
    if nom not in _FRONTIERES:
        raise ValueError(f"frontière hors catalogue : {nom!r} — abstention")
    v = _FRONTIERES[nom][3]
    if v is None:
        raise ValueError(f"vitesse non consolidée dans ce catalogue pour {nom!r} — abstention")
    return _sig(float(v))


# ── (c) MÉCANISME CINÉMATIQUE (arithmétique exacte) ──────────────────────────────────────────────────────────────
def distance_parcourue(vitesse_cm_an, millions_annees) -> float:
    """Distance (km) parcourue à vitesse constante : d = v (cm/an) × t (Ma) × 10.

    [v cm/an × t·10⁶ an = v·t·10⁶ cm ; 10⁵ cm = 1 km ; d'où v·t·10 km.] Calcul exact en Fraction,
    sortie arrondie à 10 chiffres significatifs. vitesse ≤ 0 ou durée ≤ 0 -> ValueError."""
    v = _exige_positif(vitesse_cm_an, "vitesse_cm_an")
    t = _exige_positif(millions_annees, "millions_annees")
    return _sig(float(v * t * 10))


def age_depuis_distance(vitesse_cm_an, distance_km) -> float:
    """Durée (Ma) pour parcourir `distance_km` à vitesse constante : t = d / (10·v).

    [Inverse exact de `distance_parcourue`.] Calcul exact en Fraction, sortie arrondie à 10 chiffres
    significatifs. vitesse ≤ 0 ou distance ≤ 0 -> ValueError."""
    v = _exige_positif(vitesse_cm_an, "vitesse_cm_an")
    d = _exige_positif(distance_km, "distance_km")
    return _sig(float(d / (10 * v)))


# ── (d) PHÉNOMÈNES ATTENDUS ──────────────────────────────────────────────────────────────────────────────────────
def phenomene_attendu(type_de_frontiere: str) -> str:
    """Phénomènes géologiques attendus pour un type de frontière (géologie classique) :

      divergente    -> 'dorsale, volcanisme effusif' ;
      convergente   -> 'subduction, séisme profond, chaîne de montagnes' ;
      transformante -> 'séisme superficiel, pas de volcanisme'.

    Type inconnu -> ValueError."""
    t = _exige_nom(type_de_frontiere, "type_de_frontiere")
    if t not in _PHENOMENES:
        raise ValueError(f"type de frontière inconnu : {t!r} (attendu : divergente/convergente/transformante)")
    return _PHENOMENES[t]
