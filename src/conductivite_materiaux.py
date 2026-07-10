"""
CONDUCTIVITÉ DES MATÉRIAUX — thermique (loi de Fourier) et électrique (loi de Pouillet), + Wiedemann-Franz.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est une LOI EXACTE, pas une corrélation :
      – Loi de FOURIER (conduction 1D en régime permanent, mur plan) :
            Φ = k · A · ΔT / L        (W)      et       R_th = L / (k · A)      (K/W)
      – Loi de POUILLET (conducteur filiforme homogène) :
            R = ρ · L / A             (Ω)      et       σ = 1 / ρ               (S/m)
      – Loi de WIEDEMANN-FRANZ (MÉTAUX uniquement — les porteurs de chaleur et de charge sont les
        mêmes électrons) :  k / (σ · T) ≈ L₀ = 2.44e-8 W·Ω·K⁻²  (nombre de Lorenz théorique).
        Elle est FAUSSE pour les isolants/non-métaux (phonons) : le module REFUSE de l'y appliquer.
  • CATALOGUE SOURCÉ à 20 °C (293,15 K) : conductivité thermique k (W·m⁻¹·K⁻¹) et résistivité
    électrique ρ (Ω·m) de matériaux courants (valeurs de tables classiques, cf. SOURCE).
    Les valeurs de catalogue sont des mesures APPROCHÉES (elles varient avec pureté/température) ;
    tout résultat qui en dérive est donc approché, arrondi à 10 chiffres significatifs (précision honnête).

GARANTIES (vérifiées en adverse par `valide_conductivite_materiaux.py`) :
  - matériau hors catalogue -> ValueError (abstention : jamais une valeur inventée) ;
  - résistivité demandée pour un matériau sans ρ au catalogue (eau, bois, air) -> ValueError ;
  - nombre_lorenz sur un NON-MÉTAL (verre, bois, air, eau, polystyrène) -> ValueError (loi réservée
    aux métaux) ; T hors de la plage [273.15, 313.15] K -> ValueError (le catalogue est à 20 °C,
    l'appliquer loin de l'ambiante serait un faux) ;
  - k ≤ 0, ρ ≤ 0, A ≤ 0, L ≤ 0, ΔT ≤ 0, T ≤ 0 -> ValueError ;
  - types invalides (bool, str, NaN, ±inf, non-str pour un nom de matériau) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = ("loi de Fourier (conduction thermique) + loi de Pouillet R=ρL/A + loi de Wiedemann-Franz "
          "L₀=2.44e-8 W·Ω·K⁻² ; catalogue k/ρ à 20 °C : tables classiques (CRC Handbook / Lide)")

_CHIFFRES_SIGNIFICATIFS = 10

# Nombre de Lorenz théorique (Sommerfeld) : L₀ = (π²/3)·(k_B/e)² ≈ 2.44e-8 W·Ω·K⁻².
NOMBRE_LORENZ_THEORIQUE = 2.44e-8

# ── CATALOGUE (20 °C = 293,15 K) — valeurs de tables, APPROCHÉES ────────────────────────────────────────────────
# Conductivité thermique k en W·m⁻¹·K⁻¹.
CATALOGUE_K = {
    "argent": 429.0,
    "cuivre": 401.0,
    "or": 317.0,
    "aluminium": 237.0,
    "fer": 80.4,
    "acier inox": 16.0,
    "verre": 1.0,
    "eau": 0.6,
    "bois": 0.15,
    "polystyrene": 0.033,
    "air": 0.026,
}

# Résistivité électrique ρ en Ω·m (eau/bois/air : pas de valeur fiable unique -> ABSENTS = abstention).
CATALOGUE_RHO = {
    "argent": 1.59e-8,
    "cuivre": 1.68e-8,
    "or": 2.44e-8,
    "aluminium": 2.65e-8,
    "fer": 9.71e-8,
    "acier inox": 6.9e-7,
    "verre": 1e12,        # isolant
    "polystyrene": 1e16,  # isolant
}

# Métaux du catalogue (seuls candidats légitimes à Wiedemann-Franz).
METAUX = frozenset({"argent", "cuivre", "or", "aluminium", "fer", "acier inox"})

# Plage de température où le catalogue (20 °C) reste une approximation honnête : 0 °C .. 40 °C.
_T_MIN_K = 273.15
_T_MAX_K = 313.15


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> float:
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"{nom} invalide : un réel fini strictement positif est requis")
    return float(x)


def _exige_materiau(materiau) -> str:
    """Nom de matériau du catalogue, normalisé (minuscules, accents 'polystyrène' tolérés)."""
    if not isinstance(materiau, str):
        raise ValueError("matériau invalide : une chaîne (nom du catalogue) est requise")
    cle = materiau.strip().lower().replace("polystyrène", "polystyrene")
    if cle not in CATALOGUE_K:
        raise ValueError(f"matériau hors catalogue : {materiau!r} (abstention, jamais une devinette)")
    return cle


# ── ACCÈS AU CATALOGUE ─────────────────────────────────────────────────────────────────────────────────────────
def conductivite_thermique(materiau: str) -> float:
    """k du matériau à 20 °C en W·m⁻¹·K⁻¹ (valeur de table, APPROCHÉE). Hors catalogue -> ValueError."""
    return CATALOGUE_K[_exige_materiau(materiau)]


def resistivite_electrique(materiau: str) -> float:
    """ρ du matériau à 20 °C en Ω·m (valeur de table, APPROCHÉE).

    Hors catalogue, ou matériau sans ρ tabulée (eau, bois, air) -> ValueError (abstention)."""
    cle = _exige_materiau(materiau)
    if cle not in CATALOGUE_RHO:
        raise ValueError(f"résistivité non tabulée pour {materiau!r} (eau/bois/air : pas de valeur "
                         "unique fiable) — abstention")
    return CATALOGUE_RHO[cle]


def materiaux() -> tuple:
    """Noms des matériaux du catalogue (ordre alphabétique, déterministe)."""
    return tuple(sorted(CATALOGUE_K))


# ── THERMIQUE (LOI DE FOURIER) ─────────────────────────────────────────────────────────────────────────────────
def flux_thermique(k: float, A: float, dT: float, L: float) -> float:
    """Flux thermique en régime permanent à travers un mur plan : Φ = k·A·ΔT/L (W).

    k (W·m⁻¹·K⁻¹), A (m²), ΔT (K, strictement positif : on oriente du chaud vers le froid), L (m).
    k ≤ 0, A ≤ 0, ΔT ≤ 0 ou L ≤ 0 -> ValueError. Résultat approché (10 chiffres significatifs)."""
    k = _exige_positif(k, "conductivité thermique k")
    A = _exige_positif(A, "surface A")
    dT = _exige_positif(dT, "écart de température ΔT")
    L = _exige_positif(L, "épaisseur L")
    return _sig(k * A * dT / L)


def resistance_thermique(L: float, k: float, A: float) -> float:
    """Résistance thermique de conduction d'un mur plan : R_th = L/(k·A) (K/W).

    L ≤ 0, k ≤ 0 ou A ≤ 0 -> ValueError. Résultat approché (10 chiffres significatifs)."""
    L = _exige_positif(L, "épaisseur L")
    k = _exige_positif(k, "conductivité thermique k")
    A = _exige_positif(A, "surface A")
    return _sig(L / (k * A))


# ── ÉLECTRIQUE (LOI DE POUILLET) ───────────────────────────────────────────────────────────────────────────────
def resistance_electrique(rho: float, L: float, A: float) -> float:
    """Résistance d'un conducteur filiforme homogène : R = ρ·L/A (Ω).

    ρ (Ω·m), L (m), A (m², section). ρ ≤ 0, L ≤ 0 ou A ≤ 0 -> ValueError.
    Résultat approché (10 chiffres significatifs)."""
    rho = _exige_positif(rho, "résistivité ρ")
    L = _exige_positif(L, "longueur L")
    A = _exige_positif(A, "section A")
    return _sig(rho * L / A)


def conductivite(rho: float) -> float:
    """Conductivité électrique σ = 1/ρ (S/m). ρ ≤ 0 -> ValueError. Approché (10 chiffres)."""
    rho = _exige_positif(rho, "résistivité ρ")
    return _sig(1.0 / rho)


# ── WIEDEMANN-FRANZ (MÉTAUX SEULEMENT) ─────────────────────────────────────────────────────────────────────────
def nombre_lorenz(materiau: str, T: float) -> float:
    """Rapport de Wiedemann-Franz  k/(σ·T) = k·ρ/T  (W·Ω·K⁻²) d'un MÉTAL du catalogue.

    Pour un métal pur, ce rapport tombe près du nombre de Lorenz théorique L₀ = 2.44e-8 W·Ω·K⁻²
    (pour un alliage comme l'acier inox, l'écart est plus grand — la valeur rendue est le rapport
    RÉEL des tables, pas L₀). La loi repose sur la conduction par ÉLECTRONS : elle est FAUSSE pour
    les non-métaux (phonons) -> ValueError sur verre, bois, air, eau, polystyrène.
    Le catalogue est à 20 °C : T hors [273.15, 313.15] K -> ValueError (abstention, pas d'extrapolation).
    Résultat approché (10 chiffres significatifs)."""
    cle = _exige_materiau(materiau)
    if cle not in METAUX:
        raise ValueError(f"loi de Wiedemann-Franz réservée aux MÉTAUX : {materiau!r} est un non-métal "
                         "(conduction thermique par phonons, pas par électrons) — ValueError")
    T = _exige_positif(T, "température T")
    if not (_T_MIN_K <= T <= _T_MAX_K):
        raise ValueError("T hors [273.15, 313.15] K : le catalogue k/ρ est à 20 °C, "
                         "l'extrapoler serait un faux — abstention")
    k = CATALOGUE_K[cle]
    rho = CATALOGUE_RHO[cle]
    # k/(σ·T) avec σ = 1/ρ  ->  k·ρ/T
    return _sig(k * rho / T)
