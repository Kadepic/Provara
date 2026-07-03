"""
HABITABILITÉ BORNÉE — zone habitable circumstellaire & température d'équilibre (mandat Yohan : couvrir le borné).

Même posture que `physique` / `chimie` (la réalité juge, JAMAIS un faux) :
  • Le MÉCANISME (les formules astrophysiques standard) est EXACT — c'est la garantie structurelle.
  • Les CONSTANTES de calibration sont des DONNÉES SOURCÉES (modèle d'équilibre radiatif d'un corps sphérique à
    albédo de Bond A, en rotation rapide / redistribution thermique uniforme). Le préfacteur 278.6 K et les bornes
    de flux 1.1 / 0.53 S_⊕ proviennent de l'astrophysique stellaire usuelle.
  • La sortie est ARRONDIE à 6 chiffres significatifs — précision HONNÊTE (le préfacteur dépend de T_eff⊙, du rayon
    solaire et de 1 UA, mesurés ; on ne prétend pas à l'exactitude au-delà du modèle).

MÉCANISME EXACT
---------------
1) Température d'équilibre (bilan radiatif planète sphérique, redistribution uniforme) :
       T_eq = 278.6 · [ (1 - A) · L / d² ]^(1/4)   [K]
   où L = luminosité stellaire en luminosités solaires (L⊙), d = distance orbitale en unités astronomiques (UA),
   A = albédo de Bond ∈ [0,1].
   Dérivation : πR²(1-A)(L L⊙)/(4πd²) = 4πR²σT_eq⁴  ⇒  T_eq = [ (1-A) L_⊙ / (16 π σ (1 UA)²) ]^¼ · (L/d²)^¼.
   Le facteur 278.6 K regroupe L⊙, σ et (1 UA)² (≈ T_eff⊙ · √(R⊙/2·UA)).

2) Zone habitable « eau liquide » (estimation flux-stellaire de premier ordre) :
       bord_interne = √( L / 1.1 )      bord_externe = √( L / 0.53 )   [UA]
   bornée par les flux relatifs S_int ≈ 1.1 S_⊕ (limite humide / emballement) et S_ext ≈ 0.53 S_⊕ (limite neige
   carbonique maximale). À flux S (en S_⊕), d = √(L/S) car S = L/d².

GARANTIES (vérifiées en adverse par `valide_habitabilite.py`) :
  - L ≤ 0  -> ValueError (une étoile a une luminosité strictement positive) ;
  - d ≤ 0  -> ValueError (distance orbitale strictement positive) ;
  - albédo hors [0,1] -> ValueError (un albédo physique est une fraction) ;
  - type non numérique (bool, str…) -> ValueError ;
  - déterministe ; conservateur (abstention/ValueError tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

# ── Constantes de calibration SOURCÉES (modèle d'équilibre radiatif) ─────────────────────────────────────────────
PREFACTEUR_TEQ = 278.6      # K — regroupe L⊙, σ (Stefan-Boltzmann) et (1 UA)² ; T_eq d'un corps noir gris à 1 UA.
FLUX_BORD_INTERNE = 1.1     # S_⊕ — flux stellaire relatif à la limite interne (emballement humide).
FLUX_BORD_EXTERNE = 0.53    # S_⊕ — flux stellaire relatif à la limite externe (maximum d'effet de serre CO₂).

SOURCE = "modèle d'équilibre radiatif (préfacteur 278.6 K) ; bornes de flux 1.1 / 0.53 S_⊕"

_CHIFFRES_SIGNIFICATIFS = 6


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_nombre(x) -> bool:
    """True ssi x est un réel exploitable (exclut bool, qui est un int en Python)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _luminosite_valide(L) -> float:
    if not _est_nombre(L):
        raise ValueError(f"luminosité non numérique : {L!r}")
    L = float(L)
    if not (L > 0) or L != L:  # > 0 et non NaN
        raise ValueError(f"luminosité doit être > 0 (L⊙) : {L!r}")
    return L


def _distance_valide(d) -> float:
    if not _est_nombre(d):
        raise ValueError(f"distance non numérique : {d!r}")
    d = float(d)
    if not (d > 0) or d != d:
        raise ValueError(f"distance doit être > 0 (UA) : {d!r}")
    return d


def _albedo_valide(A) -> float:
    if not _est_nombre(A):
        raise ValueError(f"albédo non numérique : {A!r}")
    A = float(A)
    if A != A or not (0.0 <= A <= 1.0):
        raise ValueError(f"albédo doit être ∈ [0,1] : {A!r}")
    return A


def temperature_equilibre(luminosite_rel, distance_UA, albedo: float = 0.3) -> float:
    """Température d'équilibre (K) d'une planète sans atmosphère, redistribution uniforme.

    T_eq = 278.6 · [ (1 - A) · L / d² ]^(1/4)
    L en L⊙, d en UA, A = albédo de Bond ∈ [0,1].

    Abstention structurelle (ValueError) si L ≤ 0, d ≤ 0, A ∉ [0,1] ou type invalide.
    """
    L = _luminosite_valide(luminosite_rel)
    d = _distance_valide(distance_UA)
    A = _albedo_valide(albedo)
    flux = (1.0 - A) * L / (d * d)
    teq = PREFACTEUR_TEQ * (flux ** 0.25)
    return _sig(teq)


def zone_habitable(luminosite_rel) -> tuple[float, float]:
    """Zone habitable circumstellaire (bord_interne, bord_externe) en UA, de premier ordre.

    bord_interne = √(L / 1.1)   ;   bord_externe = √(L / 0.53)   (L en L⊙).
    bord_interne < bord_externe par construction (1.1 > 0.53).

    Abstention structurelle (ValueError) si L ≤ 0 ou type invalide.
    """
    L = _luminosite_valide(luminosite_rel)
    interne = (L / FLUX_BORD_INTERNE) ** 0.5
    externe = (L / FLUX_BORD_EXTERNE) ** 0.5
    return (_sig(interne), _sig(externe))


def flux_stellaire_recu(luminosite_rel, distance_UA) -> float:
    """Flux stellaire reçu S = L / d² (en flux solaire à la Terre, S_⊕). L en L⊙, d en UA.

    Abstention structurelle (ValueError) si L ≤ 0, d ≤ 0 ou type invalide.
    """
    L = _luminosite_valide(luminosite_rel)
    d = _distance_valide(distance_UA)
    return _sig(L / (d * d))


def dans_zone_habitable(luminosite_rel, distance_UA) -> bool:
    """True ssi la distance orbitale tombe dans [bord_interne, bord_externe] de l'étoile.

    Abstention structurelle (ValueError) si L ≤ 0, d ≤ 0 ou type invalide.
    """
    d = _distance_valide(distance_UA)
    interne, externe = zone_habitable(luminosite_rel)
    return interne <= d <= externe
