"""
EFFET DE SERRE — mécanisme RADIATIF (équilibre planétaire, modèle une couche, forçage CO₂).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux).
NE PAS confondre : `rayonnement_thermique.py` traite le corps noir NU (Wien / Stefan-Boltzmann) et
`habitabilite.py` une température d'équilibre SANS atmosphère ; ICI, c'est le MÉCANISME de l'effet de
serre lui-même qui est modélisé, en QUATRE briques exactes :

  (a) ÉQUILIBRE SANS ATMOSPHÈRE : une planète d'albédo α recevant S (W/m²) absorbe S(1−α)/4 par m²
      (facteur 4 = rapport disque intercepté πR² / sphère émettrice 4πR²) et rayonne σT⁴ ; l'équilibre donne
            T_eq = ( S(1−α) / (4σ) )^(1/4).
      Pour la Terre (S=1361 W/m², α=0.306) : T_eq ≈ 254 K (−19 °C).
  (b) MODÈLE À UNE COUCHE : une couche atmosphérique parfaitement absorbante dans l'infrarouge et
      transparente au visible ré-émet la moitié du flux vers le sol ; le bilan donne EXACTEMENT
            T_surface = 2^(1/4) · T_eq  ≈ 302 K pour la Terre.
      HONNÊTETÉ : la température de surface OBSERVÉE est ≈ 288 K (15 °C). Le modèle à une couche
      SURESTIME (302 > 288) car l'atmosphère réelle n'est ni isotherme ni parfaitement absorbante ;
      le module le DIT explicitement (drapeau `modele_surestime`) au lieu de cacher l'écart.
      L'écart T_observée − T_eq ≈ 288 − 254 ≈ 33 K EST l'effet de serre (fait mesuré).
  (c) FORÇAGE RADIATIF DU CO₂ (Myhre et al. 1998, adopté par le GIEC) :
            ΔF = 5.35 · ln(C/C₀)   [W/m²]   — doublement de CO₂ : 5.35·ln 2 ≈ 3.708 W/m².
  (d) SENSIBILITÉ CLIMATIQUE : ΔT = λ·ΔF avec λ INCERTAIN (fourchette GIEC AR6 « likely » :
      ECS 2.5–4.0 K pour un doublement à ΔF₂ₓ ≈ 3.7 W/m², soit λ ∈ [2.5/3.7, 4.0/3.7] ≈ [0.68, 1.08]
      K/(W/m²), valeur centrale ≈ 0.8). Le module rend donc TOUJOURS un INTERVALLE (borne basse,
      borne haute), JAMAIS un scalaire unique — la valeur est MARQUÉE APPROCHÉE (SENSIBILITE_STATUT).
  (e) CATALOGUE des gaz à effet de serre (H₂O, CO₂, CH₄, N₂O, O₃) avec leur PRG à 100 ans (GIEC AR5) ;
      H₂O et O₃ n'ont PAS de PRG défini (durées de vie courtes / distribution non uniforme) :
      leur PRG est None avec la raison — abstention, pas une valeur inventée.

Les sorties flottantes sont ARRONDIES à 10 chiffres significatifs (précision honnête : les entrées
sont des mesures flottantes, on ne prétend pas à l'exactitude au-delà).

GARANTIES (vérifiées en adverse par `valide_effet_de_serre.py`) :
  - albédo hors [0, 1]  -> ValueError (une réflectivité est une fraction) ;
  - S ≤ 0               -> ValueError (un flux solaire incident est strictement positif) ;
  - C ≤ 0 ou C₀ ≤ 0     -> ValueError (une concentration de CO₂ est strictement positive) ;
  - la sensibilité climatique est un INTERVALLE ordonné (basse ≤ haute), jamais un point ;
  - types invalides (bool, str, complexe, NaN, ±inf) -> ValueError partout ;
  - le catalogue des gaz est rendu par COPIE (pas d'état global mutable exposé) ;
  - fonctions pures et déterministes ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = (
    "équilibre radiatif σT⁴ = S(1−α)/4 + modèle à une couche grise (classiques, cf. Goody & Walker) ; "
    "forçage CO₂ ΔF = 5.35·ln(C/C₀) : Myhre et al. 1998 (GRL 25, adopté par le GIEC) ; "
    "S = 1361 W/m² : constante solaire totale SORCE/TIM (Kopp & Lean 2011) ; α = 0.306 : albédo de Bond "
    "terrestre (NASA Earth Fact Sheet) ; σ = 5.670374419e-8 : CODATA 2018 (exacte, dérivée de h, c, k_B) ; "
    "PRG à 100 ans : GIEC AR5 (CH₄ = 28, N₂O = 265) ; fourchette de sensibilité : GIEC AR6, "
    "ECS « likely » 2.5–4.0 K par doublement"
)

# ── constantes sourcées (voir SOURCE) ─────────────────────────────────────────────────────────────────────────
SIGMA = 5.670374419e-8            # W·m⁻²·K⁻⁴ — constante de Stefan-Boltzmann (CODATA 2018, exacte)
CONSTANTE_SOLAIRE_TERRE = 1361.0  # W/m² — irradiance solaire totale au sommet de l'atmosphère (SORCE/TIM)
ALBEDO_TERRE = 0.306              # albédo de Bond de la Terre (NASA Earth Fact Sheet)
T_SURFACE_OBSERVEE_TERRE = 288.0  # K — température moyenne de surface MESURÉE (~15 °C) ; fait, pas un modèle
COEF_MYHRE_CO2 = 5.35             # W/m² — coefficient du forçage logarithmique du CO₂ (Myhre et al. 1998)

# Sensibilité climatique λ = ΔT/ΔF : INCERTAINE. Fourchette dérivée du GIEC AR6 (ECS « likely » 2.5–4.0 K
# pour un doublement, avec ΔF₂ₓ ≈ 3.7 W/m²). La valeur centrale usuelle ≈ 0.8 K/(W/m²) est DANS la fourchette.
LAMBDA_MIN = 2.5 / 3.7            # ≈ 0.676 K/(W/m²)
LAMBDA_MAX = 4.0 / 3.7            # ≈ 1.081 K/(W/m²)
SENSIBILITE_STATUT = "APPROCHE (fourchette GIEC AR6 ; intervalle, jamais un scalaire)"

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_flux(S) -> float:
    if not _est_reel(S) or S <= 0:
        raise ValueError("constante solaire S invalide : un réel strictement positif (W/m²) est requis")
    return float(S)


def _exige_albedo(albedo) -> float:
    if not _est_reel(albedo) or not (0.0 <= albedo <= 1.0):
        raise ValueError("albédo invalide : un réel dans [0, 1] est requis (fraction réfléchie)")
    return float(albedo)


def _exige_concentration(c, nom: str) -> float:
    if not _est_reel(c) or c <= 0:
        raise ValueError(f"concentration {nom} invalide : un réel strictement positif (ppm) est requis")
    return float(c)


# ── (a) ÉQUILIBRE RADIATIF SANS ATMOSPHÈRE ────────────────────────────────────────────────────────────────────
def temperature_equilibre_sans_atmosphere(S: float, albedo: float) -> float:
    """T_eq = ( S(1−α) / (4σ) )^(1/4)  en kelvins — équilibre radiatif d'une planète SANS atmosphère.

    S ≤ 0 -> ValueError ; albédo hors [0, 1] -> ValueError. Terre (1361, 0.306) -> ≈ 254 K."""
    S = _exige_flux(S)
    albedo = _exige_albedo(albedo)
    return _sig((S * (1.0 - albedo) / (4.0 * SIGMA)) ** 0.25)


# ── (b) MODÈLE À UNE COUCHE ───────────────────────────────────────────────────────────────────────────────────
def temperature_surface_une_couche(S: float, albedo: float) -> float:
    """T_surface = 2^(1/4) · T_eq — modèle à UNE couche atmosphérique parfaitement absorbante dans l'IR.

    Résultat EXACT dans le modèle, mais le modèle lui-même est trop simple : pour la Terre il donne
    ≈ 302 K alors que la surface observée est ≈ 288 K (il SURESTIME) — cf. bilan_effet_de_serre_terre()."""
    S = _exige_flux(S)
    albedo = _exige_albedo(albedo)
    t_eq = (S * (1.0 - albedo) / (4.0 * SIGMA)) ** 0.25
    return _sig((2.0 ** 0.25) * t_eq)


def bilan_effet_de_serre_terre() -> dict:
    """Bilan HONNÊTE de l'effet de serre terrestre (constantes sourcées du module).

    Rend : t_eq_K (≈254), t_une_couche_K (≈302), t_observee_K (288, MESURÉE), ecart_effet_de_serre_K
    (= observée − T_eq ≈ 33 K : c'est L'EFFET DE SERRE), modele_surestime (True : 302 > 288 — le modèle
    à une couche est trop simple, l'écart est DIT, pas caché), et une note explicite."""
    t_eq = temperature_equilibre_sans_atmosphere(CONSTANTE_SOLAIRE_TERRE, ALBEDO_TERRE)
    t_couche = temperature_surface_une_couche(CONSTANTE_SOLAIRE_TERRE, ALBEDO_TERRE)
    return {
        "t_eq_K": t_eq,
        "t_une_couche_K": t_couche,
        "t_observee_K": T_SURFACE_OBSERVEE_TERRE,
        "ecart_effet_de_serre_K": _sig(T_SURFACE_OBSERVEE_TERRE - t_eq),
        "modele_surestime": bool(t_couche > T_SURFACE_OBSERVEE_TERRE),
        "note": ("le modèle à une couche SURESTIME la surface (≈302 K contre 288 K observés) : "
                 "l'atmosphère réelle n'est ni isotherme ni parfaitement absorbante ; "
                 "l'effet de serre mesuré est l'écart observée − T_eq ≈ 33 K"),
    }


# ── (c) FORÇAGE RADIATIF DU CO₂ (Myhre et al. 1998) ──────────────────────────────────────────────────────────
def forcage_radiatif_co2(C_ppm: float, C0_ppm: float) -> float:
    """ΔF = 5.35 · ln(C/C₀)  en W/m² (Myhre et al. 1998, adopté par le GIEC).

    C ≤ 0 ou C₀ ≤ 0 -> ValueError. Doublement (C = 2·C₀) -> 5.35·ln 2 ≈ 3.708 W/m²."""
    C = _exige_concentration(C_ppm, "C")
    C0 = _exige_concentration(C0_ppm, "C0")
    return _sig(COEF_MYHRE_CO2 * math.log(C / C0))


# ── (d) SENSIBILITÉ CLIMATIQUE : INTERVALLE, JAMAIS UN SCALAIRE ──────────────────────────────────────────────
def sensibilite_climatique(delta_F: float) -> tuple:
    """ΔT = λ·ΔF avec λ INCERTAIN (fourchette GIEC AR6) : rend l'INTERVALLE (borne basse, borne haute) en K.

    JAMAIS un scalaire unique — la sensibilité climatique n'est pas connue en un point (cf.
    SENSIBILITE_STATUT). Les bornes sont ordonnées (basse ≤ haute), y compris pour ΔF < 0.
    delta_F non fini / bool / str -> ValueError."""
    if not _est_reel(delta_F):
        raise ValueError("forçage delta_F invalide : un réel fini (W/m²) est requis")
    b1 = LAMBDA_MIN * float(delta_F)
    b2 = LAMBDA_MAX * float(delta_F)
    basse, haute = (b1, b2) if b1 <= b2 else (b2, b1)
    return (_sig(basse), _sig(haute))


# ── (e) CATALOGUE DES GAZ À EFFET DE SERRE (PRG à 100 ans, GIEC AR5) ─────────────────────────────────────────
_GAZ = {
    "H2O": {"nom": "vapeur d'eau", "prg_100": None,
            "note": "PRG NON DÉFINI (durée de vie ~jours, concentration asservie à la température : "
                    "rétroaction, pas forçage) — abstention, pas une valeur inventée"},
    "CO2": {"nom": "dioxyde de carbone", "prg_100": 1.0,
            "note": "gaz de référence du PRG (par définition PRG(CO2) = 1)"},
    "CH4": {"nom": "méthane", "prg_100": 28.0,
            "note": "GIEC AR5, horizon 100 ans (sans rétroactions carbone-climat)"},
    "N2O": {"nom": "protoxyde d'azote", "prg_100": 265.0,
            "note": "GIEC AR5, horizon 100 ans"},
    "O3": {"nom": "ozone (troposphérique)", "prg_100": None,
           "note": "PRG NON DÉFINI (gaz à courte durée de vie, non émis directement, distribution "
                   "hétérogène) — abstention, pas une valeur inventée"},
}


def gaz_a_effet_de_serre() -> dict:
    """Catalogue des principaux gaz à effet de serre avec leur PRG à 100 ans (GIEC AR5 ; CO₂ = 1).

    H₂O et O₃ ont prg_100 = None avec la raison (pas de PRG défini) : abstention explicite.
    Rend une COPIE profonde à chaque appel (aucun état global mutable exposé)."""
    return {symbole: dict(fiche) for symbole, fiche in _GAZ.items()}
