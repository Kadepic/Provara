"""
CYCLES BIOGÉOCHIMIQUES — temps de résidence, bilans de réservoir et catalogue des grands cycles
(capacité de calcul/preuve, mandat Yohan : couvrir le borné « FORMULE/CONCEPT »).

Même posture que `physique` / `chimie` / `astronautique` (la réalité juge, JAMAIS un faux) :
  • Le MÉCANISME est EXACT — ce sont des identités de conservation de la matière dans un réservoir :
      temps de résidence τ = M/Φ  (masse du réservoir / flux qui le traverse) ;
      bilan stationnaire  ⇔  flux entrant = flux sortant (la masse du réservoir ne varie pas).
    Aucune constante physique n'intervient (rapports purs) -> la sortie est EXACTE, pas arrondie.
  • Le CATALOGUE `cycle(nom)` ne contient que des FAITS SOURCÉS CERTAINS (réservoir dominant de chaque
    grand cycle, fractions de manuel). Hors des 4 cycles connus -> ValueError (abstention, jamais d'invention).

COUVRE :
  - temps_residence(reservoir, flux_sortant) : τ = reservoir / flux  [mêmes unités de temps que le flux]
  - bilan_equilibre(flux_entrant, flux_sortant) : True ssi entrée == sortie (à tolérance) -> état stationnaire
  - cycle(nom) : 'carbone' | 'azote' | 'eau' | 'phosphore' -> réservoir principal + faits certains

GARANTIES (vérifiées en adverse par `valide_cycles_biogeochimiques.py`) :
  - ABSTENTION STRUCTURELLE : flux_sortant ≤ 0, réservoir < 0, flux < 0, cycle inconnu,
    type non numérique (bool/str/None/NaN/inf) -> ValueError. JAMAIS un nombre/fait faux.
  - déterministe ; pur (le catalogue est recopié, l'appelant ne peut pas le muter).
"""
from __future__ import annotations

import copy
import math

# ── CATALOGUE — faits sourcés CERTAINS sur les 4 grands cycles biogéochimiques ───────────────────────────────────
# Sources : manuels de biogéochimie (Schlesinger & Bernhardt, « Biogeochemistry ») / chiffres standard.
#   • Carbone : l'OCÉAN est le plus grand réservoir ACTIF (~38 000 Gt C, carbone inorganique dissous),
#     loin devant l'atmosphère (~750–870 Gt C, sous forme de CO2). Phase gazeuse : CO2.
#   • Azote : le diazote N2 atmosphérique constitue ~78 % de l'air (en volume) -> réservoir principal.
#   • Eau : les OCÉANS contiennent ~97 % de l'eau de la planète -> réservoir principal. Phase gazeuse : vapeur.
#   • Phosphore : cycle SÉDIMENTAIRE — réservoir principal = roches/sédiments (lithosphère) ;
#     UNIQUE parmi les grands cycles à NE PAS avoir de phase gazeuse significative.
_CYCLES = {
    "carbone": {
        "reservoir_principal": "océans",
        "phase_gazeuse": True,
        "note": "océan ≈ 38 000 Gt C (plus grand réservoir actif) ; atmosphère ≈ 750 Gt C (CO2)",
    },
    "azote": {
        "reservoir_principal": "atmosphère (N2)",
        "fraction_atmospherique_N2": 0.78,   # ≈ 78 % de l'air en volume (78,08 % air sec)
        "phase_gazeuse": True,
        "note": "N2 ≈ 78 % de l'atmosphère en volume -> réservoir principal de l'azote",
    },
    "eau": {
        "reservoir_principal": "océans",
        "fraction_eau_oceans": 0.97,         # ≈ 97 % de l'eau de la Terre
        "phase_gazeuse": True,
        "note": "océans ≈ 97 % de l'eau de la planète ; phase gazeuse = vapeur d'eau",
    },
    "phosphore": {
        "reservoir_principal": "roches/sédiments",
        "phase_gazeuse": False,
        "note": "cycle sédimentaire : réservoir principal = lithosphère ; PAS de phase gazeuse notable",
    },
}

SOURCE = "Schlesinger & Bernhardt, Biogeochemistry (réservoirs/fractions standard de manuel)"


def _num(x) -> float:
    """Convertit en float réel un nombre VALIDE ; lève ValueError pour bool / str / None / NaN / inf.

    bool est explicitement rejeté (True n'est PAS le nombre 1) : abstention structurelle plutôt qu'un faux."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("entrée non numérique")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("entrée non finie")
    return v


# ── TEMPS DE RÉSIDENCE ──────────────────────────────────────────────────────────────────────────────────────────
def temps_residence(reservoir, flux_sortant) -> float:
    """Temps de résidence τ = M/Φ : masse du réservoir divisée par le flux qui en sort.

    Unité : celle du flux (si Φ est en unités/an, τ est en années). Identité de conservation -> EXACT.
    Domaine : reservoir ≥ 0, flux_sortant > 0. Sinon ValueError (un flux nul/négatif n'a pas de τ défini)."""
    r = _num(reservoir)
    f = _num(flux_sortant)
    if r < 0:
        raise ValueError("réservoir négatif")
    if f <= 0:
        raise ValueError("flux sortant doit être > 0")
    return r / f


# ── BILAN DE RÉSERVOIR ──────────────────────────────────────────────────────────────────────────────────────────
def bilan_equilibre(flux_entrant, flux_sortant, tol_rel: float = 1e-9, tol_abs: float = 1e-12) -> bool:
    """État STATIONNAIRE ssi flux entrant = flux sortant (à tolérance) : la masse du réservoir ne varie pas.

    Domaine : flux_entrant ≥ 0, flux_sortant ≥ 0 (un flux est une grandeur physique non négative)."""
    e = _num(flux_entrant)
    s = _num(flux_sortant)
    if e < 0 or s < 0:
        raise ValueError("flux négatif")
    return abs(e - s) <= tol_rel * max(abs(e), abs(s)) + tol_abs


# ── CATALOGUE DES CYCLES ────────────────────────────────────────────────────────────────────────────────────────
def cycles_connus() -> tuple:
    """Noms des cycles catalogués (faits sourcés certains)."""
    return tuple(sorted(_CYCLES))


def cycle(nom) -> dict:
    """Réservoir principal + faits certains d'un grand cycle : 'carbone' | 'azote' | 'eau' | 'phosphore'.

    Insensible à la casse / aux espaces de bordure. Tout autre nom -> ValueError (abstention)."""
    if isinstance(nom, bool) or not isinstance(nom, str):
        raise ValueError("nom de cycle invalide")
    cle = nom.strip().lower()
    if cle not in _CYCLES:
        raise ValueError(f"cycle inconnu : {nom!r}")
    return copy.deepcopy(_CYCLES[cle])
