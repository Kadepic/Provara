"""
ATOME D'HYDROGÈNE — niveaux d'énergie quantifiés (modèle de Bohr / solution de Schrödinger, B-PHY).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est un résultat EXACT de la mécanique quantique (et déjà du modèle de Bohr, 1913) :
        E_n = − E_R / n²          (n = 1, 2, 3, …)
    où E_R = 13.605693122994 eV est l'énergie de Rydberg (constante CODATA 2018, hors correction de
    masse réduite du noyau — approximation noyau infiniment lourd, la précision spectroscopique fine
    n'est PAS revendiquée au-delà de ~0,05 %).
  • Transition n_i -> n_f :  ΔE = E_f − E_i = E_R·(n_f² − n_i²)/(n_i²·n_f²)
    (négatif = émission d'un photon, positif = absorption).
  • Longueur d'onde du photon :  λ = h·c / |ΔE|  avec h et c EXACTES (SI 2019).
  • Rayon de Bohr de l'orbite n :  r_n = n² · a0,  a0 = 5.29177210903e-11 m (CODATA 2018).
  • Séries spectrales : Lyman (n_f=1), Balmer (n_f=2), Paschen (n_f=3).
  • Énergie d'ionisation depuis le niveau n :  E_ion(n) = + E_R / n²  (= 0 − E_n).
  • ÉVALUATION EXACTE : tous les quotients en n sont calculés en ARITHMÉTIQUE RATIONNELLE
    (`fractions.Fraction`, numérateurs/dénominateurs ENTIERS ; les constantes décimales sont prises
    comme rationnels exacts). Une SEULE conversion finale vers float, correctement arrondie
    (≤ 0,5 ulp) — AUCUNE annulation catastrophique 1/n_i² − 1/n_f², même pour n astronomiques.
  • Les sorties flottantes sont ARRONDIES à 10 chiffres significatifs — précision honnête ; les valeurs
    sont APPROCHÉES au niveau de l'approximation « noyau infiniment lourd » (dit explicitement ici).

GARANTIES (vérifiées en adverse par `valide_atome_hydrogene.py`) :
  - n non entier (float, str, bool, NaN, inf) -> ValueError (un nombre quantique principal est un entier) ;
  - n < 1 -> ValueError (le fondamental est n=1 ; n=0 n'existe pas) ;
  - n_i == n_f -> ValueError (pas de transition sans changement de niveau ; jamais λ infinie déguisée) ;
  - résultat exact NON REPRÉSENTABLE en flottant à pleine précision (sous-flow vers 0.0 ou vers un
    subnormal, ou dépassement vers ±inf) -> ValueError : ABSTENTION plutôt qu'un zéro trompeur entre
    deux niveaux distincts, qu'un subnormal dégradé sous les 10 chiffres promis, ou qu'un infini ;
  - nom de série inconnu (ou non-str) -> ValueError (closed-set : Lyman/Balmer/Paschen, rien d'autre) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

NE PAS CONFONDRE avec `quantique.niveaux_puits_infini` : le puits infini est un AUTRE système
(E_n ∝ +n², croissant) ; ici l'atome d'hydrogène (E_n ∝ −1/n², liaison coulombienne).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math`, `sys`,
`fractions` (stdlib).
"""
from __future__ import annotations

import math
import sys
from fractions import Fraction

SOURCE = ("E_n = −E_R/n² (Bohr 1913 / Schrödinger 1926) ; E_R = 13.605693122994 eV, "
          "a0 = 5.29177210903e-11 m (CODATA 2018) ; h, c, e exactes (SI 2019)")

# ── Constantes (CODATA 2018 / SI 2019) ─────────────────────────────────────────────────────────────
E_RYDBERG_EV = 13.605693122994          # énergie de Rydberg, eV (CODATA 2018 ; hcR∞ en eV)
RAYON_BOHR_M = 5.29177210903e-11        # rayon de Bohr a0, mètres (CODATA 2018)
PLANCK_J_S = 6.62607015e-34             # constante de Planck h, J·s (EXACTE, SI 2019)
CELERITE_M_S = 299792458.0              # vitesse de la lumière c, m/s (EXACTE, SI 2019)
EV_EN_JOULES = 1.602176634e-19          # 1 eV en joules (charge élémentaire e, EXACTE, SI 2019)

# Mêmes constantes en RATIONNELS EXACTS (les décimaux ci-dessus sont des littéraux décimaux finis :
# leur écriture Fraction("…") est leur valeur exacte, sans l'arrondi binaire du float).
_E_RYDBERG_EXACT = Fraction("13.605693122994")
_RAYON_BOHR_EXACT = Fraction("5.29177210903e-11")
_PLANCK_EXACT = Fraction("6.62607015e-34")
_CELERITE_EXACT = Fraction(299792458)
_EV_EXACT = Fraction("1.602176634e-19")

_SERIES = {"lyman": 1, "balmer": 2, "paschen": 3}   # closed-set : nom -> n_f

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _exige_n(n, nom: str = "n") -> int:
    """Nombre quantique principal : ENTIER ≥ 1. bool/float/str/NaN/inf -> ValueError."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"{nom} invalide : un entier (int, pas bool/float/str) est requis")
    if n < 1:
        raise ValueError(f"{nom} invalide : le nombre quantique principal vaut au moins 1 (n={n})")
    return n


def _vers_float_fiable(exact: Fraction, contexte: str) -> float:
    """Convertit un rationnel EXACT non nul en float à pleine précision, sinon ABSTENTION.

    ValueError si la conversion déborde (±inf), s'annule (0.0 pour une grandeur non nulle = zéro
    trompeur) ou tombe dans les subnormaux (précision dégradée sous les 10 chiffres promis)."""
    try:
        x = float(exact)                      # correctement arrondi (≤ 0,5 ulp) par CPython
    except OverflowError:
        raise ValueError(f"{contexte} : magnitude au-delà du plus grand flottant (abstention)")
    if math.isinf(x):
        raise ValueError(f"{contexte} : magnitude au-delà du plus grand flottant (abstention)")
    if x == 0.0 or abs(x) < sys.float_info.min:
        raise ValueError(f"{contexte} : magnitude sous le plus petit flottant normal — refus plutôt "
                         "qu'un zéro ou un subnormal trompeur (abstention)")
    return x


# ── NIVEAUX D'ÉNERGIE ──────────────────────────────────────────────────────────────────────────────
def energie_niveau(n: int) -> float:
    """Énergie du niveau n de l'hydrogène, en eV :  E_n = −E_R/n²  (toujours < 0 : état lié).

    Calcul rationnel exact puis une conversion float. Approximation noyau infiniment lourd
    (E_R = hcR∞). n<1, non entier, ou |E_n| non représentable à pleine précision -> ValueError."""
    n = _exige_n(n)
    return _sig(_vers_float_fiable(-_E_RYDBERG_EXACT / (n * n), "E_n"))


def energie_niveau_joules(n: int) -> float:
    """Énergie du niveau n en JOULES :  E_n = −E_R/n² × (1 eV en J). Mêmes abstentions qu'energie_niveau."""
    n = _exige_n(n)
    return _sig(_vers_float_fiable(-_E_RYDBERG_EXACT * _EV_EXACT / (n * n), "E_n (joules)"))


# ── TRANSITIONS ────────────────────────────────────────────────────────────────────────────────────
def energie_transition(n_i: int, n_f: int) -> float:
    """Énergie de la transition n_i -> n_f, en eV :  ΔE = E_f − E_i = E_R·(n_f² − n_i²)/(n_i²·n_f²).

    Numérateur et dénominateur en ENTIERS EXACTS (aucune annulation 1/n_i² − 1/n_f², valable pour
    tout n). Négatif = émission (n_i > n_f), positif = absorption (n_i < n_f).
    n_i == n_f -> ValueError (pas de transition). |ΔE| sous le plus petit flottant normal
    -> ValueError (refus plutôt qu'un zéro/subnormal trompeur entre deux niveaux distincts)."""
    n_i = _exige_n(n_i, "n_i")
    n_f = _exige_n(n_f, "n_f")
    if n_i == n_f:
        raise ValueError("n_i == n_f : pas de transition (aucun photon ; refus plutôt qu'un zéro trompeur)")
    delta_exact = _E_RYDBERG_EXACT * Fraction(n_f * n_f - n_i * n_i, n_i * n_i * n_f * n_f)
    return _sig(_vers_float_fiable(delta_exact, "ΔE"))


def longueur_onde_transition(n_i: int, n_f: int) -> float:
    """Longueur d'onde (mètres) du photon de la transition n_i <-> n_f :  λ = h·c/|ΔE|.

    Calcul rationnel exact de bout en bout (h, c, e exactes SI 2019), une seule conversion float.
    Symétrique en (n_i, n_f) (même |ΔE|). n_i == n_f -> ValueError ; λ au-delà du plus grand
    flottant (niveaux quasi dégénérés) -> ValueError (abstention, jamais un infini)."""
    n_i = _exige_n(n_i, "n_i")
    n_f = _exige_n(n_f, "n_f")
    if n_i == n_f:
        raise ValueError("n_i == n_f : pas de transition, pas de photon (λ serait infinie)")
    delta_e_joules_exact = (_E_RYDBERG_EXACT * _EV_EXACT
                            * Fraction(abs(n_f * n_f - n_i * n_i), n_i * n_i * n_f * n_f))
    return _sig(_vers_float_fiable(_PLANCK_EXACT * _CELERITE_EXACT / delta_e_joules_exact, "λ"))


# ── RAYON DE BOHR ──────────────────────────────────────────────────────────────────────────────────
def rayon_bohr(n: int) -> float:
    """Rayon de l'orbite de Bohr n, en mètres :  r_n = n²·a0 (rationnel exact puis une conversion).

    n<1, non entier, ou r_n au-delà du plus grand flottant -> ValueError."""
    n = _exige_n(n)
    return _sig(_vers_float_fiable(_RAYON_BOHR_EXACT * (n * n), "r_n"))


# ── SÉRIES SPECTRALES ──────────────────────────────────────────────────────────────────────────────
def serie(nom: str) -> int:
    """Niveau d'arrivée n_f d'une série spectrale : Lyman->1, Balmer->2, Paschen->3 (insensible à la casse).

    Closed-set : tout autre nom (ou non-str) -> ValueError (abstention, jamais une devinette)."""
    if not isinstance(nom, str):
        raise ValueError("nom de série invalide : une chaîne est requise")
    cle = nom.strip().lower()
    if cle not in _SERIES:
        raise ValueError(f"série inconnue {nom!r} : seules Lyman, Balmer, Paschen sont couvertes (abstention)")
    return _SERIES[cle]


# ── IONISATION ─────────────────────────────────────────────────────────────────────────────────────
def energie_ionisation(n: int) -> float:
    """Énergie (eV, > 0) pour ioniser l'atome depuis le niveau n :  E_ion = 0 − E_n = +E_R/n².

    n<1, non entier, ou E_ion non représentable à pleine précision -> ValueError."""
    n = _exige_n(n)
    return _sig(_vers_float_fiable(_E_RYDBERG_EXACT / (n * n), "E_ion"))
