"""
INTERFÉRENCES ET DIFFRACTION — dispositifs standards (fentes d'Young, réseau, fente simple).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (le théorème juge, jamais un faux) :
  • Le MÉCANISME est un ensemble de LOIS EXACTES de l'optique ondulatoire (approximation de Fraunhofer,
    petits angles pour Young), pas une corrélation :
      – FENTES D'YOUNG (écart a entre fentes, écran à distance D, longueur d'onde λ, petits angles) :
            interfrange           i = λ·D / a
            frange BRILLANTE d'ordre m (m entier)  : x = m·λ·D / a
            frange SOMBRE (m entier)               : x = (m + ½)·λ·D / a
        EXISTENCE : la frange d'ordre m n'existe sur un écran que si |sin θ| = |m·λ/a| < 1
        (respectivement |(m+½)·λ/a| < 1 pour une sombre). À |sin θ| = 1 la direction est rasante
        (θ = 90°, la lumière ne rencontre JAMAIS l'écran) et au-delà sin θ est impossible :
        dans les deux cas -> ABSTENTION (ValueError), jamais une position inventée. De même,
        l'interfrange n'est définie que s'il existe au moins une frange latérale : λ/a < 1 exigé.
      – RÉSEAU de diffraction (pas d) : maxima aux angles θ tels que  d·sin θ = m·λ  (m entier).
        Si |m·λ/d| > 1, l'ordre m N'EXISTE PAS physiquement (sin θ ne peut dépasser 1) -> ABSTENTION
        (ValueError), jamais un angle inventé.
      – FENTE SIMPLE (largeur a) : MINIMA de diffraction aux angles θ tels que  a·sin θ = m·λ  avec
        m entier NON NUL. m = 0 est le MAXIMUM central (pas un minimum) -> ValueError. |m·λ/a| > 1
        -> ordre inexistant -> ValueError.
  • Les ANGLES sont rendus en DEGRÉS (documenté sur chaque fonction) ; les positions en MÈTRES.
  • Les sorties sont ARRONDIES à 10 chiffres significatifs — précision honnête (entrées flottantes,
    on ne prétend pas à l'exactitude au-delà) ; la formule de Young est elle-même une APPROXIMATION
    petits angles (tan θ ≈ sin θ ≈ θ), classique et assumée dans la docstring.

GARANTIES (vérifiées en adverse par `valide_interferences_diffraction.py`) :
  - λ ≤ 0, D ≤ 0, a ≤ 0, d ≤ 0  -> ValueError (grandeurs strictement positives) ;
  - ordre m non entier (float, str) ou bool -> ValueError (True n'est pas 1) ;
  - réseau/fente : |m·λ / pas| > 1 -> ValueError (ordre physiquement inexistant, sin θ > 1) ;
  - Young : |m·λ/a| ≥ 1 (brillante), |(m+½)·λ/a| ≥ 1 (sombre), λ/a ≥ 1 (interfrange)
    -> ValueError (frange inexistante ou rasante : elle n'atteint aucun écran) ;
  - fente simple : m = 0 -> ValueError (maximum central, PAS un minimum) ;
  - types invalides (bool, str, NaN, ±inf, complexe) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = ("interférences d'Young i=λD/a (Young, 1801 ; optique ondulatoire classique) ; "
          "équation du réseau d·sinθ=mλ (Fraunhofer) ; minima de fente simple a·sinθ=mλ, m≠0")

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> float:
    """Grandeur physique strictement positive (λ, D, a, d) ; sinon ValueError."""
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"{nom} invalide : un réel strictement positif est requis")
    return float(x)


def _exige_ordre(m, nom: str = "ordre m") -> int:
    """Ordre d'interférence/diffraction : un ENTIER (bool refusé, float refusé même 2.0)."""
    if not isinstance(m, int) or isinstance(m, bool):
        raise ValueError(f"{nom} invalide : un entier (int) est requis (bool/float refusés)")
    return m


# ── FENTES D'YOUNG (petits angles) ─────────────────────────────────────────────────────────────────────────────
def _exige_frange_existante(sin_theta: float, quoi: str) -> None:
    """ABSTENTION si la frange n'atteint aucun écran : |sin θ| ≥ 1.

    |sin θ| > 1 : direction physiquement impossible (la frange n'existe pas).
    |sin θ| = 1 : direction rasante θ = 90° — la lumière file parallèlement à l'écran et ne le
    rencontre jamais ; la position x = m·λ·D/a serait une valeur plausible mais FAUSSE."""
    if abs(sin_theta) >= 1.0:
        raise ValueError(f"{quoi} inexistante sur l'écran : |sin θ| = {abs(sin_theta):.6g} ≥ 1 "
                         "(direction impossible ou rasante, aucune position à rendre)")


def interfrange_young(longueur_onde: float, distance_ecran: float, ecart_fentes: float) -> float:
    """Interfrange des fentes d'Young : i = λ·D / a  (en mètres, approximation petits angles).

    longueur_onde λ (m), distance_ecran D (m), ecart_fentes a (m) — tous strictement positifs,
    sinon ValueError. ABSTENTION (ValueError) si λ/a ≥ 1 : la première frange latérale (ordre 1,
    sin θ = λ/a) n'existe pas sur l'écran, donc AUCUN interfrange n'est observable."""
    lam = _exige_positif(longueur_onde, "longueur d'onde λ")
    D = _exige_positif(distance_ecran, "distance écran D")
    a = _exige_positif(ecart_fentes, "écart des fentes a")
    _exige_frange_existante(lam / a, "interfrange (frange d'ordre 1)")
    return _sig(lam * D / a)


def position_frange_brillante(ordre_m: int, longueur_onde: float,
                              distance_ecran: float, ecart_fentes: float) -> float:
    """Position (m) de la frange BRILLANTE d'ordre m (Young) : x = m·λ·D / a.

    m est un ENTIER (0 = frange centrale ; négatif = de l'autre côté de l'axe). Approximation petits
    angles. ABSTENTION (ValueError) si |m·λ/a| ≥ 1 : la frange d'ordre m n'existe sur aucun écran
    (sin θ impossible, ou direction rasante à 90°)."""
    m = _exige_ordre(ordre_m)
    lam = _exige_positif(longueur_onde, "longueur d'onde λ")
    D = _exige_positif(distance_ecran, "distance écran D")
    a = _exige_positif(ecart_fentes, "écart des fentes a")
    if m != 0:  # m = 0 : frange centrale, toujours présente (sin θ = 0)
        _exige_frange_existante(m * lam / a, f"frange brillante d'ordre m={m}")
    return _sig(m * lam * D / a)


def position_frange_sombre(ordre_m: int, longueur_onde: float,
                           distance_ecran: float, ecart_fentes: float) -> float:
    """Position (m) de la frange SOMBRE (Young) : x = (m + ½)·λ·D / a  (m entier).

    m = 0 donne la première frange sombre au-dessus du centre (x = i/2). Approximation petits angles.
    ABSTENTION (ValueError) si |(m+½)·λ/a| ≥ 1 : la frange sombre demandée n'existe sur aucun écran
    (sin θ impossible, ou direction rasante à 90°)."""
    m = _exige_ordre(ordre_m)
    lam = _exige_positif(longueur_onde, "longueur d'onde λ")
    D = _exige_positif(distance_ecran, "distance écran D")
    a = _exige_positif(ecart_fentes, "écart des fentes a")
    _exige_frange_existante((m + 0.5) * lam / a, f"frange sombre m={m}")
    return _sig((m + 0.5) * lam * D / a)


# ── RÉSEAU DE DIFFRACTION ──────────────────────────────────────────────────────────────────────────────────────
def angle_reseau(pas_d: float, ordre_m: int, longueur_onde: float) -> float:
    """Angle θ (en DEGRÉS) du maximum d'ordre m d'un réseau de pas d :  d·sin θ = m·λ.

    m est un ENTIER (0 = ordre central θ=0 ; négatif = symétrique). ABSTENTION (ValueError) si
    |m·λ/d| > 1 : l'ordre demandé n'existe pas physiquement (sin θ ne peut dépasser 1)."""
    d = _exige_positif(pas_d, "pas du réseau d")
    m = _exige_ordre(ordre_m)
    lam = _exige_positif(longueur_onde, "longueur d'onde λ")
    sin_theta = m * lam / d
    if abs(sin_theta) > 1.0:
        raise ValueError(f"ordre m={m} inexistant : |m·λ/d| = {abs(sin_theta):.6g} > 1 (sin θ impossible)")
    return _sig(math.degrees(math.asin(sin_theta)))


# ── FENTE SIMPLE (minima de diffraction) ───────────────────────────────────────────────────────────────────────
def angle_minimum_fente(largeur_a: float, ordre_m: int, longueur_onde: float) -> float:
    """Angle θ (en DEGRÉS) du MINIMUM d'ordre m de la diffraction par une fente de largeur a :
    a·sin θ = m·λ, avec m entier NON NUL.

    m = 0 -> ValueError (c'est le MAXIMUM central, pas un minimum). ABSTENTION (ValueError) si
    |m·λ/a| > 1 : le minimum demandé n'existe pas physiquement."""
    a = _exige_positif(largeur_a, "largeur de fente a")
    m = _exige_ordre(ordre_m)
    lam = _exige_positif(longueur_onde, "longueur d'onde λ")
    if m == 0:
        raise ValueError("m=0 : maximum central de diffraction, PAS un minimum (ordre m non nul requis)")
    sin_theta = m * lam / a
    if abs(sin_theta) > 1.0:
        raise ValueError(f"minimum m={m} inexistant : |m·λ/a| = {abs(sin_theta):.6g} > 1 (sin θ impossible)")
    return _sig(math.degrees(math.asin(sin_theta)))
