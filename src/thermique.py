"""
THERMIQUE — chaleur sensible, chaleur latente, capacité thermique massique, équilibre thermique.

Même posture FAUX=0 que `physique` / `chimie` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est la CALORIMÉTRIE classique, pas une corrélation :
      – Chaleur SENSIBLE :  Q = m · c · ΔT   (m en kg, c en J·kg⁻¹·K⁻¹, ΔT en K ; Q en J).
        ΔT peut être négatif (refroidissement) : Q < 0 signifie chaleur CÉDÉE — c'est une convention
        de signe, pas une erreur de domaine.
      – Chaleur LATENTE :  Q = m · L   (changement d'état SANS variation de température ; L en J·kg⁻¹).
      – ÉQUILIBRE thermique de deux corps en contact (système isolé, sans changement d'état) :
            T_eq = (m₁c₁T₁ + m₂c₂T₂) / (m₁c₁ + m₂c₂)
        — conséquence directe de la conservation de l'énergie : m₁c₁(T_eq−T₁) + m₂c₂(T_eq−T₂) = 0.
        T_eq est TOUJOURS comprise entre min(T₁,T₂) et max(T₁,T₂) (barycentre à poids positifs).
  • Le CATALOGUE de capacités thermiques massiques est SOURCÉ (valeurs usuelles ~25 °C, manuels de
    physique / CRC Handbook) ; ce sont des valeurs APPROCHÉES (elles varient avec T) — annoncées
    comme telles. Tout matériau HORS catalogue -> ValueError (abstention, jamais une devinette).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (les entrées sont des
    flottants, on ne prétend pas à l'exactitude au-delà).

CATALOGUE (J·kg⁻¹·K⁻¹, ≈ 25 °C, valeurs approchées usuelles) :
    eau 4185 ; glace 2090 ; vapeur d'eau 2010 ; aluminium 897 ; fer 449 ; cuivre 385 ;
    plomb 129 ; verre 840 ; air (cp) 1005.
CHALEURS LATENTES de l'eau (J·kg⁻¹, pression atmosphérique) :
    fusion 334 000 ; vaporisation 2 257 000.

GARANTIES (vérifiées en adverse par `valide_thermique.py`) :
  - masse m ≤ 0 -> ValueError (une masse est strictement positive) ;
  - capacité c ≤ 0 -> ValueError (une capacité thermique massique est strictement positive) ;
  - chaleur latente L ≤ 0 -> ValueError ;
  - température < 0 K (zéro absolu, entrées en kelvins ou en °C > −273.15) -> non imposé ici :
    les températures de `temperature_equilibre` doivent être dans la MÊME échelle LINÉAIRE
    (K ou °C, jamais un mélange) ; on refuse seulement les valeurs non finies ;
  - matériau inconnu / clé non-str -> ValueError (abstention : le catalogue est CLOS) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - OVERFLOW en sortie : si le calcul déborde le flottant (résultat non fini, p.ex. m·c·ΔT -> inf,
    ou inf/inf -> nan dans l'équilibre), le module S'ABSTIENT (ValueError) — jamais un nan/inf rendu ;
    c'est un faux négatif assumé (entrées physiquement absurdes), jamais un faux positif ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = ("calorimétrie classique Q=m·c·ΔT, Q=m·L, T_eq=Σ(mcT)/Σ(mc) (conservation de l'énergie) ; "
          "capacités massiques ~25 °C et chaleurs latentes de l'eau : valeurs usuelles des manuels "
          "de physique / CRC Handbook (APPROCHÉES)")

_CHIFFRES_SIGNIFICATIFS = 10

# Capacités thermiques massiques (J·kg⁻¹·K⁻¹, ≈ 25 °C) — catalogue CLOS, valeurs APPROCHÉES sourcées.
_CAPACITES_MASSIQUES = {
    "eau": 4185.0,          # eau liquide
    "glace": 2090.0,        # eau solide (proche de 0 °C)
    "vapeur": 2010.0,       # vapeur d'eau (cp)
    "aluminium": 897.0,
    "fer": 449.0,
    "cuivre": 385.0,
    "plomb": 129.0,
    "verre": 840.0,
    "air": 1005.0,          # air sec, cp à pression constante
}

# Chaleurs latentes de l'eau (J·kg⁻¹, pression atmosphérique) — valeurs usuelles APPROCHÉES.
CHALEUR_LATENTE_FUSION_EAU = 334000.0        # fondre 1 kg de glace à 0 °C
CHALEUR_LATENTE_VAPORISATION_EAU = 2257000.0  # vaporiser 1 kg d'eau à 100 °C


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude).

    GARDE DE SORTIE : un résultat non fini (overflow -> inf, ou inf/inf -> nan) signifie que le
    flottant a débordé — on S'ABSTIENT (ValueError) au lieu de laisser fuir un nan/inf (FAUX=0)."""
    if not math.isfinite(x):
        raise ValueError("débordement numérique : le résultat n'est pas un flottant fini — "
                         "abstention (entrées hors du domaine représentable)")
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_masse(m) -> float:
    if not _est_reel(m) or m <= 0:
        raise ValueError("masse invalide : un réel strictement positif (kg) est requis")
    return float(m)


def _exige_capacite(c) -> float:
    if not _est_reel(c) or c <= 0:
        raise ValueError("capacité thermique massique invalide : un réel strictement positif "
                         "(J·kg⁻¹·K⁻¹) est requis")
    return float(c)


def _exige_temperature(T) -> float:
    """Température : réel fini (échelle linéaire K ou °C, cohérente entre les deux corps)."""
    if not _est_reel(T):
        raise ValueError("température invalide : un réel fini est requis (K ou °C, échelle cohérente)")
    return float(T)


# ── CHALEUR SENSIBLE : Q = m·c·ΔT ──────────────────────────────────────────────────────────────────────────────
def chaleur_sensible(m: float, c: float, dT: float) -> float:
    """Chaleur sensible Q = m·c·ΔT (J).

    m > 0 (kg) ; c > 0 (J·kg⁻¹·K⁻¹) ; ΔT réel fini (K ou °C — même écart), signé :
    ΔT < 0 -> Q < 0 = chaleur CÉDÉE par le corps. m≤0, c≤0, bool/NaN/inf -> ValueError."""
    m = _exige_masse(m)
    c = _exige_capacite(c)
    if not _est_reel(dT):
        raise ValueError("ΔT invalide : un réel fini est requis (écart de température en K)")
    return _sig(m * c * float(dT))


# ── CHALEUR LATENTE : Q = m·L ──────────────────────────────────────────────────────────────────────────────────
def chaleur_latente(m: float, L: float) -> float:
    """Chaleur latente Q = m·L (J) : changement d'état à température constante.

    m > 0 (kg) ; L > 0 (J·kg⁻¹) — utiliser p.ex. CHALEUR_LATENTE_FUSION_EAU (334 000) ou
    CHALEUR_LATENTE_VAPORISATION_EAU (2 257 000). m≤0, L≤0, bool/NaN/inf -> ValueError."""
    m = _exige_masse(m)
    if not _est_reel(L) or L <= 0:
        raise ValueError("chaleur latente L invalide : un réel strictement positif (J·kg⁻¹) est requis")
    return _sig(m * float(L))


# ── CATALOGUE SOURCÉ ───────────────────────────────────────────────────────────────────────────────────────────
def capacite_massique(materiau: str) -> float:
    """Capacité thermique massique du catalogue CLOS (J·kg⁻¹·K⁻¹, ≈ 25 °C, valeur APPROCHÉE sourcée).

    Matériaux connus : eau, glace, vapeur, aluminium, fer, cuivre, plomb, verre, air.
    Hors catalogue ou clé non-str -> ValueError (abstention, jamais une devinette)."""
    if not isinstance(materiau, str):
        raise ValueError("matériau invalide : une chaîne (nom du matériau) est requise")
    cle = materiau.strip().lower()
    if cle not in _CAPACITES_MASSIQUES:
        raise ValueError(f"matériau hors catalogue : '{materiau}' inconnu — abstention "
                         f"(connus : {', '.join(sorted(_CAPACITES_MASSIQUES))})")
    return _CAPACITES_MASSIQUES[cle]


# ── ÉQUILIBRE THERMIQUE : T_eq = Σ(m·c·T)/Σ(m·c) ───────────────────────────────────────────────────────────────
def temperature_equilibre(m1: float, c1: float, T1: float,
                          m2: float, c2: float, T2: float) -> float:
    """Température d'équilibre de deux corps en contact (système isolé, SANS changement d'état) :

        T_eq = (m₁c₁T₁ + m₂c₂T₂) / (m₁c₁ + m₂c₂)

    (conservation de l'énergie : la chaleur cédée par le chaud = la chaleur reçue par le froid).
    T₁ et T₂ dans la MÊME échelle linéaire (K ou °C) ; T_eq est rendue dans cette échelle et est
    toujours entre min(T₁,T₂) et max(T₁,T₂). m≤0, c≤0, bool/NaN/inf -> ValueError."""
    m1 = _exige_masse(m1)
    c1 = _exige_capacite(c1)
    T1 = _exige_temperature(T1)
    m2 = _exige_masse(m2)
    c2 = _exige_capacite(c2)
    T2 = _exige_temperature(T2)
    T_eq = (m1 * c1 * T1 + m2 * c2 * T2) / (m1 * c1 + m2 * c2)
    return _sig(T_eq)
