"""COSMOLOGIE — Expansion de l'univers : primitives EXACTES, directement appelables, FAUX=0 (mission formule/concept).

Posture identique à `physique`/`maths_discretes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (la loi de Hubble, la définition du décalage vers le rouge) est EXACT — garantie structurelle.
  • Les CONSTANTES de conversion sont des DONNÉES SOURCÉES (1 Mpc = 3.086e19 km ; 1 an julien ≈ 3.156e7 s).
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision HONNÊTE (les conversions ne sont exactes
    qu'au niveau de la source ; H0 lui-même est mesuré avec incertitude).
  • ABSTENTION STRUCTURELLE : toute entrée invalide (H0 ≤ 0, longueur d'onde ≤ 0, distance/vitesse négative,
    type non numérique, valeur non finie) lève `ValueError` — JAMAIS un résultat faux. Conservateur : faux
    négatif (abstention) toléré, faux POSITIF interdit.

COUVRE (Expansion de l'univers) :
  - vitesse_recession(H0, d)        : loi de Hubble v = H0·d  [H0 en km/s/Mpc, d en Mpc -> v en km/s]
  - distance_hubble(H0, v)          : d = v / H0              [-> d en Mpc]
  - age_univers(H0)                 : temps de Hubble 1/H0    [-> âge en ANNÉES]
  - decalage_rouge(lambda_obs, lambda_emis) : z = (λ_obs − λ_emis)/λ_emis  [sans unité]

Vérifié en adverse par `valide_cosmologie.py` (ancres externes connues + soundness : entrée invalide -> ValueError).
"""
from __future__ import annotations

import math

# ── CONSTANTES SOURCÉES ──────────────────────────────────────────────────────────────────────────────────────────
MPC_KM = 3.086e19        # 1 mégaparsec en kilomètres (valeur de conversion conventionnelle)
AN_S = 3.156e7           # 1 année (julienne) en secondes (≈ 365.25 j)

SOURCE = "loi de Hubble v=H0·d ; 1 Mpc = 3.086e19 km ; 1 an ≈ 3.156e7 s"

_CHIFFRES_SIGNIFICATIFS = 10


def _arr(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x, nom: str) -> float:
    """Valide un réel fini ; bool/str/None/NaN/inf -> ValueError (jamais un calcul sur entrée invalide)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : nombre réel attendu, reçu {x!r}")
    x = float(x)
    if not math.isfinite(x):
        raise ValueError(f"{nom} : valeur finie attendue, reçu {x!r}")
    return x


def _strict_pos(x, nom: str) -> float:
    x = _num(x, nom)
    if x <= 0:
        raise ValueError(f"{nom} : strictement positif attendu, reçu {x!r}")
    return x


def _nonneg(x, nom: str) -> float:
    x = _num(x, nom)
    if x < 0:
        raise ValueError(f"{nom} : non négatif attendu, reçu {x!r}")
    return x


# ── EXPANSION DE L'UNIVERS ───────────────────────────────────────────────────────────────────────────────────────
def vitesse_recession(H0: float, d: float) -> float:
    """Loi de Hubble : v = H0·d. H0 [km/s/Mpc], d [Mpc] -> v [km/s]. H0>0, d≥0."""
    H0 = _strict_pos(H0, "H0")
    d = _nonneg(d, "d")
    return _arr(H0 * d)


def distance_hubble(H0: float, v: float) -> float:
    """Distance de Hubble : d = v / H0. H0 [km/s/Mpc], v [km/s] -> d [Mpc]. H0>0, v≥0."""
    H0 = _strict_pos(H0, "H0")
    v = _nonneg(v, "v")
    return _arr(v / H0)


def age_univers(H0: float) -> float:
    """Temps de Hubble (âge approché) = 1/H0. H0 [km/s/Mpc] -> âge en ANNÉES. H0>0.

    H0 converti en s^-1 : H0_si = H0 / (1 Mpc en km). Puis 1/H0_si en secondes, divisé par 1 an en secondes.
    """
    H0 = _strict_pos(H0, "H0")
    H0_si = H0 / MPC_KM          # s^-1
    t_s = 1.0 / H0_si            # = MPC_KM / H0, en secondes
    return _arr(t_s / AN_S)


def decalage_rouge(lambda_obs: float, lambda_emis: float) -> float:
    """Décalage vers le rouge : z = (λ_obs − λ_emis) / λ_emis. λ_obs>0, λ_emis>0 (longueurs d'onde)."""
    lo = _strict_pos(lambda_obs, "lambda_obs")
    le = _strict_pos(lambda_emis, "lambda_emis")
    return _arr((lo - le) / le)
