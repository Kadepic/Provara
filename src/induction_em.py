"""
INDUCTION ÉLECTROMAGNÉTIQUE — flux magnétique, loi de Faraday, loi de Lenz, fem de déplacement.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité/la loi juge, jamais un faux) :
  • Le MÉCANISME est une LOI PHYSIQUE EXACTE, pas une corrélation :
      – FLUX magnétique à travers une surface plane d'aire A dans un champ uniforme B, dont la normale fait
        un angle θ avec le champ :   Φ = B · A · cos(θ)   (en webers, Wb = T·m²).
      – Loi de FARADAY (forme intégrale, bobine de N spires identiques) :
            ε = − N · ΔΦ / Δt   (en volts).
        Le signe MOINS est la loi de LENZ : « le courant induit s'oppose, par ses effets, à la cause qui lui
        donne naissance » (H. Lenz, 1834). Si le flux AUGMENTE (ΔΦ > 0), la fem est NÉGATIVE : le courant
        induit crée un flux OPPOSÉ à l'augmentation.
      – Fem de DÉPLACEMENT (barre conductrice de longueur L glissant à la vitesse v, perpendiculairement
        à un champ B uniforme) :   ε = B · L · v.
        Cohérence interne : la barre balaie ΔA = L·v·Δt, donc ΔΦ = B·L·v·Δt et |ε| = ΔΦ/Δt = B·L·v
        (deux chemins de calcul distincts qui DOIVENT coïncider — vérifié en adverse).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (entrées flottantes ; on ne
    prétend pas à l'exactitude au-delà). Toute valeur issue de cos() est donc APPROCHÉE au flottant près
    (cos(π/2) machine ≈ 6e-17, pas exactement 0 : on le DIT, on ne maquille pas).

GARANTIES (vérifiées en adverse par `valide_induction_em.py`) :
  - Δt ≤ 0  -> ValueError  (une durée nulle ou négative n'a pas de sens pour un taux de variation) ;
  - N < 1 ou N non entier (ou bool)  -> ValueError  (le nombre de spires est un entier ≥ 1) ;
  - θ hors [0, π]  -> ValueError  (angle entre le champ et la normale : domaine [0, π] fermé) ;
  - A ≤ 0  -> ValueError  (une aire de surface est strictement positive) ;
  - B < 0, L ≤ 0, v < 0  -> ValueError  (B et v sont des GRANDEURS/normes ; un signe se porte sur θ ou ΔΦ) ;
  - types invalides (bool, str, complexe, NaN, ±inf) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
NB : `induction_horn.py` traite d'induction LOGIQUE (règles de Horn) — aucun rapport avec ce module.
"""
from __future__ import annotations

import math

PI = math.pi
SOURCE = ("loi de Faraday ε = −N·dΦ/dt + loi de Lenz (H. Lenz, 1834 : « le courant induit s'oppose à la "
          "cause qui lui donne naissance ») ; Φ = B·A·cosθ ; fem de déplacement ε = B·L·v (électromagnétisme classique)")

# Phrase de référence de la loi de Lenz (l'énoncé classique, ancre du sens physique du signe −).
LENZ = "Le courant induit s'oppose, par ses effets, à la cause qui lui donne naissance."

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_champ(B) -> float:
    """Norme du champ magnétique B (tesla) : réel fini ≥ 0 (le signe se porte sur l'angle θ)."""
    if not _est_reel(B) or B < 0:
        raise ValueError("champ B invalide : un réel fini >= 0 (tesla) est requis (le signe se porte sur θ)")
    return float(B)


def _exige_aire(A) -> float:
    if not _est_reel(A) or A <= 0:
        raise ValueError("aire A invalide : un réel strictement positif (m²) est requis")
    return float(A)


def _exige_angle(theta) -> float:
    """Angle entre le champ et la normale à la surface : réel dans [0, π] (fermé)."""
    if not _est_reel(theta) or not (0.0 <= theta <= PI):
        raise ValueError("angle θ invalide : un réel dans l'intervalle [0, pi] est requis")
    return float(theta)


def _exige_spires(N) -> int:
    """Nombre de spires : entier ≥ 1 (bool refusé : True n'est pas 1 spire)."""
    if isinstance(N, bool) or not isinstance(N, int) or N < 1:
        raise ValueError("nombre de spires N invalide : un entier >= 1 est requis")
    return N


def _exige_duree(dt) -> float:
    if not _est_reel(dt) or dt <= 0:
        raise ValueError("durée Δt invalide : un réel strictement positif (s) est requis")
    return float(dt)


def _exige_flux(phi, nom: str) -> float:
    """Un flux magnétique (Wb) : réel fini quelconque (peut être négatif : orientation de la normale)."""
    if not _est_reel(phi):
        raise ValueError(f"flux {nom} invalide : un réel fini (Wb) est requis")
    return float(phi)


# ── FLUX MAGNÉTIQUE  Φ = B·A·cos(θ) ──────────────────────────────────────────────────────────────────────────
def flux_magnetique(B: float, A: float, theta: float) -> float:
    """Flux magnétique Φ = B·A·cos(θ) en webers (Wb).

    B = norme du champ (T, ≥ 0) ; A = aire de la surface (m², > 0) ; θ = angle champ/normale, dans [0, π].
    θ > π/2 -> flux négatif (le champ traverse la surface « à contresens » de la normale choisie).
    Valeur APPROCHÉE au flottant près (cos machine)."""
    B = _exige_champ(B)
    A = _exige_aire(A)
    theta = _exige_angle(theta)
    return _sig(B * A * math.cos(theta))


# ── LOI DE FARADAY  ε = −N·ΔΦ/Δt ─────────────────────────────────────────────────────────────────────────────
def fem_faraday(N: int, delta_phi: float, delta_t: float) -> float:
    """Fem induite (V) dans une bobine de N spires : ε = −N·ΔΦ/Δt (loi de Faraday, signe de Lenz).

    ΔΦ > 0 (flux croissant) -> ε < 0 : le courant induit s'oppose à l'AUGMENTATION du flux (Lenz).
    N entier ≥ 1 ; Δt > 0 ; ΔΦ réel fini (signé). Sinon -> ValueError."""
    N = _exige_spires(N)
    delta_phi = _exige_flux(delta_phi, "ΔΦ")
    delta_t = _exige_duree(delta_t)
    return _sig(-N * delta_phi / delta_t)


# ── LOI DE LENZ (sens du courant induit) ─────────────────────────────────────────────────────────────────────
def sens_courant_induit(flux_avant: float, flux_apres: float) -> str:
    """Sens qualitatif du courant induit (loi de Lenz) d'après l'évolution du flux.

    flux croissant  -> 'oppose_a_l_augmentation' (le courant induit crée un flux OPPOSÉ au flux imposé) ;
    flux décroissant -> 'oppose_a_la_diminution' (le courant induit crée un flux DANS LE SENS du flux imposé,
                        pour retenir sa diminution) ;
    flux constant   -> 'aucun' (ΔΦ = 0 : pas de fem, pas de courant induit).
    Référence : LENZ (module) — « le courant induit s'oppose à la cause qui lui donne naissance »."""
    avant = _exige_flux(flux_avant, "avant")
    apres = _exige_flux(flux_apres, "après")
    if apres > avant:
        return "oppose_a_l_augmentation"
    if apres < avant:
        return "oppose_a_la_diminution"
    return "aucun"


# ── FEM DE DÉPLACEMENT  ε = B·L·v ────────────────────────────────────────────────────────────────────────────
def fem_deplacement(B: float, L: float, v: float) -> float:
    """Fem (V) aux bornes d'une barre de longueur L (m) glissant à la vitesse v (m/s) ⊥ à un champ B (T).

    ε = B·L·v (grandeur, ≥ 0). B ≥ 0 ; L > 0 ; v ≥ 0 (norme de la vitesse). Sinon -> ValueError.
    Cohérence : ΔΦ balayé = B·L·v·Δt, donc |ε| = ΔΦ/Δt = B·L·v (second chemin par fem_faraday)."""
    B = _exige_champ(B)
    if not _est_reel(L) or L <= 0:
        raise ValueError("longueur L invalide : un réel strictement positif (m) est requis")
    if not _est_reel(v) or v < 0:
        raise ValueError("vitesse v invalide : un réel fini >= 0 (m/s, norme) est requis")
    return _sig(B * L * float(v))
