"""MARITIME — architecture navale, FAUX=0 (mission formule/concept 2026-06-29).

Trois mécanismes EXACTS et établis de l'hydrostatique / hydrodynamique du navire :

  • vitesse_coque (hull speed) — vitesse limite théorique d'une carène en déplacement, fixée par la longueur d'onde
    du sillage de Kelvin égale à la longueur de flottaison. Formule classique de l'architecture navale :
        V_coque (noeuds) = 1.34 · √(LWL en pieds)
    soit, en mètres, V_coque = (1.34/√0.3048) · √(LWL_m) ≈ 2.427 · √(LWL_m). Le coefficient 1.34 et le pied
    international 0.3048 m sont des CONSTANTES établies ; la version mètre est DÉRIVÉE exactement (pas un faux).

  • poussee_archimede — principe d'Archimède : la poussée verticale ascendante vaut le poids du fluide déplacé,
        F = ρ_eau · V_immergé · g .
    Un corps FLOTTE si son poids peut être équilibré avant immersion totale, c.-à-d. masse < ρ_eau · V_carène.

  • nombre_froude — nombre de Froude (sans dimension), rapport des forces d'inertie aux forces de gravité :
        Fr = v / √(g · L) .
    Il gouverne la similitude des vagues ; Fr ≈ 0.4 correspond au régime de la vitesse de coque.

Posture (la réalité juge, jamais un faux) :
  - mécanisme EXACT, constantes SOURCÉES (pied international 0.3048 m exact ; g = 9.80665 m/s² gravité standard BIPM ;
    ρ eau de mer ≈ 1025 kg/m³, eau douce 1000 kg/m³) ;
  - sortie ARRONDIE à 6 chiffres significatifs (précision honnête) ;
  - fonctions PURES, DÉTERMINISTES ;
  - SOUNDNESS structurelle : longueur ≤ 0, volume ≤ 0, masse volumique ≤ 0, g ≤ 0, vitesse < 0, ou entrée
    non numérique -> ValueError (abstention ; jamais un nombre absurde).

Couvre le sujet borné « Maritime ». Vérifié en adverse par `valide_maritime.py`.
"""
from __future__ import annotations

import math

# ── CONSTANTES SOURCÉES ──────────────────────────────────────────────────────────────────────────────────────
PIED = 0.3048                      # m — pied international (EXACT, par définition)
NOEUD_PAR_RAC_PIED = 1.34          # noeuds / √pied — coefficient de vitesse de coque (architecture navale classique)
NOEUD_PAR_RAC_METRE = NOEUD_PAR_RAC_PIED / math.sqrt(PIED)   # ≈ 2.427153 noeuds / √m — DÉRIVÉ exactement
G = 9.806_65                       # m/s² — gravité standard (BIPM, conventionnelle)
RHO_MER = 1025.0                   # kg/m³ — masse volumique typique de l'eau de mer
RHO_DOUCE = 1000.0                 # kg/m³ — masse volumique de l'eau douce (≈ 4 °C)

SOURCE = "pied int. 0.3048 m exact ; coeff hull-speed 1.34 noeud/√ft ; g=9.80665 m/s² (BIPM) ; ρ_mer≈1025 kg/m³"

_SIG = 6


def _sig(x: float) -> float:
    """Arrondit à 6 chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs) -> None:
    """Refuse toute entrée non numérique (bool exclu) -> ValueError (jamais un calcul sur du n'importe quoi)."""
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")
        if not math.isfinite(x):
            raise ValueError("valeur non finie")


def _pos(*xs) -> None:
    """Exige une grandeur strictement positive -> ValueError sinon."""
    _num(*xs)
    if any(x <= 0 for x in xs):
        raise ValueError("grandeur strictement positive requise")


# ── VITESSE DE COQUE (hull speed) ────────────────────────────────────────────────────────────────────────────
def vitesse_coque(longueur_flottaison_m: float) -> float:
    """Vitesse de coque en NOEUDS d'après la longueur de flottaison (LWL) en mètres.

        V = (1.34/√0.3048) · √(LWL_m) ≈ 2.42715 · √(LWL_m)      (= 1.34 · √(LWL_pieds))

    LWL > 0 (sinon ValueError). LWL=9 m -> ≈ 7.28 noeuds.
    """
    _pos(longueur_flottaison_m)
    return _sig(NOEUD_PAR_RAC_METRE * math.sqrt(longueur_flottaison_m))


def vitesse_coque_max(longueur_flottaison_m: float) -> float:
    """Vitesse maximale de coque (noeuds) d'une carène en déplacement — alias explicite de `vitesse_coque`.

    C'est la vitesse THÉORIQUE limite (le sillage atteint la longueur de la carène). LWL > 0 (sinon ValueError).
    """
    return vitesse_coque(longueur_flottaison_m)


def vitesse_coque_depuis_pieds(longueur_flottaison_pieds: float) -> float:
    """Vitesse de coque (noeuds) directement depuis LWL en PIEDS : V = 1.34·√(LWL_ft). LWL > 0 sinon ValueError."""
    _pos(longueur_flottaison_pieds)
    return _sig(NOEUD_PAR_RAC_PIED * math.sqrt(longueur_flottaison_pieds))


# ── POUSSÉE D'ARCHIMÈDE / FLOTTABILITÉ ───────────────────────────────────────────────────────────────────────
def poussee_archimede(volume_immerge: float, rho_eau: float = RHO_MER) -> float:
    """Poussée d'Archimède F = ρ_eau · V_immergé · g, en NEWTONS.

    V_immergé > 0, ρ_eau > 0 (sinon ValueError). Défaut ρ = 1025 kg/m³ (eau de mer).
    """
    _pos(volume_immerge, rho_eau)
    return _sig(rho_eau * volume_immerge * G)


def masse_max_flottante(volume_carene: float, rho_eau: float = RHO_MER) -> float:
    """Masse maximale (kg) qu'une carène de volume `volume_carene` peut soutenir avant immersion totale = ρ_eau·V.

    V > 0, ρ > 0 sinon ValueError. Au-delà de cette masse, le corps coule.
    """
    _pos(volume_carene, rho_eau)
    return _sig(rho_eau * volume_carene)


def flotte(masse: float, volume_carene: float, rho_eau: float = RHO_MER) -> bool:
    """True ssi le corps FLOTTE : masse < ρ_eau · V_carène (poids équilibré avant immersion totale).

    masse ≥ 0, V_carène > 0, ρ_eau > 0 (sinon ValueError). À l'égalité (neutre / juste submergé) -> False.
    """
    _num(masse)
    if masse < 0:
        raise ValueError("masse ≥ 0 requise")
    _pos(volume_carene, rho_eau)
    return masse < rho_eau * volume_carene


# ── NOMBRE DE FROUDE ─────────────────────────────────────────────────────────────────────────────────────────
def nombre_froude(v: float, longueur: float, g: float = 9.81) -> float:
    """Nombre de Froude (sans dimension) Fr = v / √(g·L).

    v ≥ 0 (vitesse en m/s), L > 0 (longueur caractéristique en m), g > 0 (accélération de pesanteur, défaut 9.81).
    Domaine invalide -> ValueError.
    """
    _num(v)
    if v < 0:
        raise ValueError("vitesse ≥ 0 requise")
    _pos(longueur, g)
    return _sig(v / math.sqrt(g * longueur))
