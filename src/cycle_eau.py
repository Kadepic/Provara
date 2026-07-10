"""
CYCLE DE L'EAU — mécanisme (étapes, changements d'état, moteurs) + bilan (réservoirs, flux, résidence).

Même posture FAUX=0 que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est un enchaînement physique établi, pas une corrélation :
      – chaque ÉTAPE du cycle porte son CHANGEMENT D'ÉTAT (évaporation : liquide->gaz ; condensation :
        gaz->liquide ; sublimation : solide->gaz ; fonte : solide->liquide ; les transports — précipitation,
        infiltration, ruissellement, écoulement souterrain — ne changent pas l'état) et son MOTEUR
        énergétique (énergie solaire pour les passages vers le gaz et la fonte ; refroidissement pour la
        condensation ; gravité pour la chute et les écoulements) ;
      – le BILAN est une CONSERVATION : à l'échelle du globe, l'eau évaporée retombe intégralement
        (évaporation totale = précipitation totale ≈ 486 000 km³/an), et le déficit océanique
        (413 000 évaporés − 373 000 précipités = 40 000 km³/an) revient par les fleuves ;
      – le TEMPS DE RÉSIDENCE d'un réservoir est T = V / F (volume / flux traversant), définition standard
        du bilan de masse en régime permanent.
  • Les RÉSERVOIRS sont des FAITS MESURÉS (volumes en km³ et % du total ≈ 1,386·10⁹ km³) repris du bilan
    hydrologique classique (USGS / Gleick 1996) : océans 96,5 %, glaciers/calottes 1,74 %, eaux
    souterraines 1,69 %, lacs 0,013 %, atmosphère 0,001 %, rivières 0,0002 %. Ces volumes sont des
    estimations APPROCHÉES (3-4 chiffres significatifs dans la littérature) et sont présentés comme tels.
  • Les sorties numériques calculées (temps de résidence) sont ARRONDIES à 10 chiffres significatifs —
    précision honnête (les volumes/flux d'entrée sont des estimations, on ne prétend pas au-delà).

GARANTIES (vérifiées en adverse par `valide_cycle_eau.py`) :
  - étape hors catalogue -> ValueError (jamais un changement d'état ou un moteur deviné) ;
  - réservoir hors catalogue -> ValueError (jamais un volume inventé) ;
  - temps_residence : volume ≤ 0 ou flux ≤ 0 -> ValueError (un réservoir/flux physique est > 0) ;
  - types invalides (bool, str là où un nombre est requis, NaN, ±inf, non-str là où un nom est requis)
    -> ValueError ;
  - INVARIANT DUR (RuntimeError si violé, vérifié à l'import et exposé par `verifie_invariants()`) :
      · la somme des pourcentages des réservoirs vaut 100 % à ±0,1 près ;
      · évaporation totale (océan + continent) = précipitation totale (océan + continent) ;
      · le déficit océanique (évap. océan − précip. océan) = flux des fleuves vers l'océan ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `unicodedata` (stdlib).
"""
from __future__ import annotations

import math
import unicodedata

SOURCE = (
    "bilan hydrologique global classique (USGS Water Science School / Gleick 1996, 'Water in Crisis') : "
    "répartition des réservoirs (~1,386e9 km³) et flux annuels évaporation/précipitation (~486 000 km³/an)"
)

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _normalise(nom) -> str:
    """Nom -> clé canonique : minuscules, accents retirés, espaces/tirets -> '_'. Non-str -> ValueError."""
    if not isinstance(nom, str):
        raise ValueError("nom invalide : une chaîne de caractères est requise")
    decompose = unicodedata.normalize("NFD", nom.strip().lower())
    sans_accents = "".join(c for c in decompose if not unicodedata.combining(c))
    return sans_accents.replace(" ", "_").replace("-", "_")


# ── (a) MÉCANISME : catalogue des ÉTAPES ─────────────────────────────────────────────────────────────────────
# clé canonique -> (changement d'état, moteur énergétique, successeurs possibles dans le cycle)
# 'aucun' = pas de changement d'état (l'eau reste liquide, elle est seulement transportée).
_ETAPES = {
    "evaporation": ("liquide->gaz", "energie_solaire", ("condensation",)),
    "evapotranspiration": ("liquide->gaz", "energie_solaire", ("condensation",)),
    "condensation": ("gaz->liquide", "refroidissement", ("precipitation",)),
    "precipitation": ("aucun", "gravite", ("infiltration", "ruissellement")),
    "infiltration": ("aucun", "gravite", ("ecoulement_souterrain",)),
    "ruissellement": ("aucun", "gravite", ("evaporation",)),
    "ecoulement_souterrain": ("aucun", "gravite", ("evaporation",)),
    "sublimation": ("solide->gaz", "energie_solaire", ("condensation",)),
    "fonte": ("solide->liquide", "energie_solaire", ("infiltration", "ruissellement")),
}

# Ordre canonique (boucle principale puis branches solides) — figé, restitué par etapes().
_ORDRE_ETAPES = (
    "evaporation",
    "evapotranspiration",
    "condensation",
    "precipitation",
    "infiltration",
    "ruissellement",
    "ecoulement_souterrain",
    "sublimation",
    "fonte",
)


def _exige_etape(etape) -> str:
    cle = _normalise(etape)
    if cle not in _ETAPES:
        raise ValueError(f"étape inconnue : {etape!r} n'est pas dans le catalogue {_ORDRE_ETAPES}")
    return cle


def etapes() -> tuple:
    """Tuple ordonné des étapes du cycle de l'eau (clés canoniques sans accents)."""
    return _ORDRE_ETAPES


def changement_etat(etape: str) -> str:
    """Changement d'état de l'étape : 'liquide->gaz', 'gaz->liquide', 'solide->gaz', 'solide->liquide'
    ou 'aucun' (transport sans changement d'état). Étape hors catalogue -> ValueError."""
    return _ETAPES[_exige_etape(etape)][0]


def moteur(etape: str) -> str:
    """Moteur énergétique de l'étape : 'energie_solaire', 'refroidissement' ou 'gravite'.
    Étape hors catalogue -> ValueError."""
    return _ETAPES[_exige_etape(etape)][1]


def suivante(etape: str) -> tuple:
    """Successeur(s) possibles de l'étape dans le cycle (tuple : le cycle bifurque, p. ex. la précipitation
    mène à l'infiltration OU au ruissellement — on refuse de choisir arbitrairement, on rend les deux).
    Étape hors catalogue -> ValueError."""
    return _ETAPES[_exige_etape(etape)][2]


# ── (b) BILAN : RÉSERVOIRS (faits mesurés, valeurs APPROCHÉES de la littérature) ─────────────────────────────
VOLUME_TOTAL_KM3 = 1.386e9  # volume total d'eau terrestre ≈ 1,386 milliard de km³ (USGS/Gleick, approché)

# clé canonique -> (volume mesuré en km³ [approché], % du total [approché]) — VALEURS DE LA LITTÉRATURE,
# pas dérivées l'une de l'autre ici (les % publiés sont arrondis ; les volumes sont les estimations publiées).
_RESERVOIRS = {
    "oceans": (1.338e9, 96.5),
    "glaciers": (2.4064e7, 1.74),          # glaciers + calottes polaires
    "eaux_souterraines": (2.34e7, 1.69),
    "lacs": (1.764e5, 0.013),
    "atmosphere": (1.29e4, 0.001),
    "rivieres": (2.12e3, 0.0002),
}


def _exige_reservoir(nom) -> str:
    cle = _normalise(nom)
    if cle not in _RESERVOIRS:
        raise ValueError(f"réservoir inconnu : {nom!r} n'est pas dans le catalogue {tuple(_RESERVOIRS)}")
    return cle


def reservoirs() -> tuple:
    """Tuple des noms canoniques des réservoirs catalogués."""
    return tuple(_RESERVOIRS)


def reservoir(nom: str) -> tuple:
    """(volume_km3, pourcentage) du réservoir — valeurs mesurées APPROCHÉES (littérature USGS/Gleick).
    Réservoir hors catalogue -> ValueError."""
    return _RESERVOIRS[_exige_reservoir(nom)]


# ── (c) BILAN : FLUX GLOBAUX (km³/an, approchés) et TEMPS DE RÉSIDENCE ───────────────────────────────────────
FLUX_EVAPORATION_OCEAN_KM3_AN = 413_000        # évaporation depuis les océans
FLUX_PRECIPITATION_OCEAN_KM3_AN = 373_000      # précipitations sur les océans
FLUX_EVAPOTRANSPIRATION_CONTINENT_KM3_AN = 73_000   # évapotranspiration des continents
FLUX_PRECIPITATION_CONTINENT_KM3_AN = 113_000  # précipitations sur les continents
FLUX_FLEUVES_KM3_AN = 40_000                   # retour continents -> océans par les fleuves


def temps_residence(volume_km3: float, flux_km3_par_an: float) -> float:
    """Temps de résidence T = V / F (en ANNÉES) : volume du réservoir / flux qui le traverse.

    Définition standard du bilan de masse en régime permanent. Résultat arrondi à 10 chiffres
    significatifs. volume ≤ 0 ou flux ≤ 0 -> ValueError ; bool/NaN/inf/str -> ValueError."""
    if not _est_reel(volume_km3) or volume_km3 <= 0:
        raise ValueError("volume invalide : un réel strictement positif (km³) est requis")
    if not _est_reel(flux_km3_par_an) or flux_km3_par_an <= 0:
        raise ValueError("flux invalide : un réel strictement positif (km³/an) est requis")
    return _sig(float(volume_km3) / float(flux_km3_par_an))


def bilan_global() -> tuple:
    """(évaporation_totale, précipitation_totale) en km³/an — DOIVENT être égales (conservation de l'eau).

    RuntimeError si la conservation est violée (jamais un bilan faux rendu silencieusement)."""
    evaporation = FLUX_EVAPORATION_OCEAN_KM3_AN + FLUX_EVAPOTRANSPIRATION_CONTINENT_KM3_AN
    precipitation = FLUX_PRECIPITATION_OCEAN_KM3_AN + FLUX_PRECIPITATION_CONTINENT_KM3_AN
    if evaporation != precipitation:
        raise RuntimeError("conservation violée : évaporation totale != précipitation totale")
    return (evaporation, precipitation)


# ── (d) INVARIANTS DURS ──────────────────────────────────────────────────────────────────────────────────────
def verifie_invariants() -> bool:
    """Invariants durs du bilan — RuntimeError si l'un est violé, True sinon.

    1) Σ pourcentages des réservoirs = 100 % à ±0,1 près ;
    2) évaporation totale = précipitation totale (conservation globale) ;
    3) déficit océanique (évap. océan − précip. océan) = flux des fleuves (le retour boucle le cycle)."""
    somme_pct = sum(pct for _, pct in _RESERVOIRS.values())
    if abs(somme_pct - 100.0) > 0.1:
        raise RuntimeError(f"invariant violé : somme des pourcentages = {somme_pct} (attendu 100 ± 0,1)")
    bilan_global()  # RuntimeError si non conservé
    deficit_ocean = FLUX_EVAPORATION_OCEAN_KM3_AN - FLUX_PRECIPITATION_OCEAN_KM3_AN
    if deficit_ocean != FLUX_FLEUVES_KM3_AN:
        raise RuntimeError("invariant violé : le déficit océanique n'est pas compensé par les fleuves")
    return True


# Les invariants sont vérifiés dès l'import : un catalogue incohérent ne peut pas servir.
verifie_invariants()
