"""
CARTOGRAPHIE / SIG / GÉOMATIQUE — calculs EXACTS (mandat Yohan : « tous les sujets bornés, chirurgical, FAUX=0 »).

Domaine BORNÉ par la réalité : il s'agit d'IDENTITÉS de définition (échelle d'une carte, conversion d'unités
angulaires), pas de corrélations. Le MÉCANISME est exact ; les seules « données » employées sont des
CONVENTIONS ÉTABLIES et exactes (1 pouce international = 2,54 cm exactement ; 1° = 60′, 1′ = 60″).

  1) ÉCHELLE D'UNE CARTE. L'échelle 1:N signifie : 1 unité sur la carte = N unités sur le terrain.
        distance réelle = distance sur la carte × N            (même unité, ici le cm)
        distance carte  = distance réelle    / N
     Ex. échelle 1:25000, 4 cm sur la carte -> 4 × 25000 = 100000 cm = 1000 m = 1 km sur le terrain.

  2) RÉSOLUTION AU SOL (geomatique / numérisation). La taille au sol d'un pixel d'une carte numérisée vaut
        résolution_sol = taille_pixel_sur_carte × N.
     Depuis une numérisation à `dpi` points par pouce : taille_pixel = 2,54/dpi cm, d'où
        résolution_sol = (2,54/dpi) × N.
     Ex. 1:25000 numérisé à 300 dpi -> (2,54/300) × 25000 ≈ 211,67 cm ≈ 2,12 m au sol.

  3) COORDONNÉES — conversion sexagésimale (DMS) -> décimale (DD).
        DD = signe(d) × ( |d| + m/60 + s/3600 )
     Ex. 48°51′12″ -> 48 + 51/60 + 12/3600 = 48,853333…°.
     (DMS strict : degrés et minutes ENTIERS, minutes et secondes dans [0, 60) ; le signe vient des degrés.)

GARANTIES (vérifiées en adverse par `valide_cartographie.py`) :
  - échelle (dénominateur) ≤ 0 -> ValueError (jamais une distance inventée / division par zéro masquée) ;
  - distance / taille de pixel / dpi négatifs -> ValueError ;
  - minutes ou secondes hors [0, 60) -> ValueError (jamais une coordonnée hors-norme « corrigée » en douce) ;
  - degrés ou minutes non entiers en DMS -> ValueError (DMS malformé) ;
  - entrée non numérique / non finie / booléenne -> ValueError (abstention, jamais un faux) ;
  - déterministe (fonctions pures).
"""
from __future__ import annotations

import math
from collections import namedtuple

SOURCE_ECHELLE = "définition de l'échelle cartographique (1:N => terrain = carte × N)"
SOURCE_ANGLE = "conventions sexagésimales (1° = 60′, 1′ = 60″) ; pouce international = 2,54 cm (exact)"

POUCE_CM = 2.54  # 1 pouce international = 2,54 cm EXACTEMENT (norme internationale).

# Résolution au sol : valeur + unité de référence (cm sur le terrain par pixel de carte).
ResolutionSol = namedtuple("ResolutionSol", ["valeur_cm", "source"])


def _reel(x, nom: str) -> float:
    """Renvoie le flottant fini réel ou lève ValueError.

    Seuls les vrais nombres int/float sont acceptés (pas de coercition silencieuse de chaîne) ; booléen et
    valeur non finie (NaN/inf) refusés.
    """
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : valeur non numérique ({x!r})")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"{nom} : valeur non finie ({x!r})")
    return v


def _entier(x, nom: str) -> int:
    """Renvoie l'entier réel (int, ou float à valeur entière) ou lève ValueError."""
    v = _reel(x, nom)
    if v != math.floor(v):
        raise ValueError(f"{nom} : doit être un entier ({x!r})")
    return int(v)


def _echelle(echelle_denominateur) -> float:
    """Dénominateur d'échelle strictement positif, sinon ValueError."""
    n = _reel(echelle_denominateur, "echelle_denominateur")
    if n <= 0:
        raise ValueError(f"échelle (dénominateur) ≤ 0 : {n}")
    return n


def _non_negatif(x, nom: str) -> float:
    v = _reel(x, nom)
    if v < 0:
        raise ValueError(f"{nom} : valeur négative ({v})")
    return v


def _strict_positif(x, nom: str) -> float:
    v = _reel(x, nom)
    if v <= 0:
        raise ValueError(f"{nom} : valeur ≤ 0 ({v})")
    return v


# ── 1) ÉCHELLE ─────────────────────────────────────────────────────────────────────────────────────────────────
def echelle_distance_reelle(distance_carte_cm, echelle_denominateur) -> float:
    """Distance réelle (cm) = distance sur la carte (cm) × dénominateur d'échelle (EXACT).

    Ex. echelle_distance_reelle(4, 25000) = 100000 cm (= 1 km).
    """
    d = _non_negatif(distance_carte_cm, "distance_carte_cm")
    n = _echelle(echelle_denominateur)
    return d * n


def distance_carte(distance_reelle_cm, echelle_denominateur) -> float:
    """Distance sur la carte (cm) = distance réelle (cm) / dénominateur d'échelle (EXACT).

    Inverse de `echelle_distance_reelle`. Ex. distance_carte(100000, 25000) = 4 cm.
    """
    d = _non_negatif(distance_reelle_cm, "distance_reelle_cm")
    n = _echelle(echelle_denominateur)
    return d / n


# ── 2) RÉSOLUTION AU SOL ────────────────────────────────────────────────────────────────────────────────────────
def resolution_au_sol(taille_pixel_carte_cm, echelle_denominateur) -> ResolutionSol:
    """Taille au sol (cm) d'un pixel de carte = taille du pixel sur la carte (cm) × dénominateur d'échelle.

    Ex. un pixel de 0,01 cm sur une carte 1:25000 -> 250 cm = 2,5 m au sol.
    """
    p = _strict_positif(taille_pixel_carte_cm, "taille_pixel_carte_cm")
    n = _echelle(echelle_denominateur)
    return ResolutionSol(valeur_cm=p * n, source=SOURCE_ANGLE)


def resolution_au_sol_depuis_dpi(dpi, echelle_denominateur) -> ResolutionSol:
    """Taille au sol (cm) d'un pixel issu d'une numérisation à `dpi` points/pouce, à l'échelle 1:N.

        résolution_sol = (2,54 / dpi) × N
    Ex. 300 dpi à 1:25000 -> (2,54/300) × 25000 ≈ 211,667 cm.
    """
    d = _strict_positif(dpi, "dpi")
    n = _echelle(echelle_denominateur)
    return ResolutionSol(valeur_cm=(POUCE_CM / d) * n, source=SOURCE_ANGLE)


# ── 3) COORDONNÉES — DMS -> DD ──────────────────────────────────────────────────────────────────────────────────
def conversion_dms_dd(degres, minutes, secondes) -> float:
    """Convertit degrés-minutes-secondes (sexagésimal) en degrés décimaux (EXACT par définition).

        DD = signe(degres) × ( |degres| + minutes/60 + secondes/3600 )

    DMS strict : `degres` et `minutes` entiers ; `minutes` ∈ [0, 60) et `secondes` ∈ [0, 60). Le signe vient des
    degrés ; minutes et secondes décrivent une magnitude (toujours ≥ 0).
    Ex. conversion_dms_dd(48, 51, 12) = 48,853333…°.
    """
    d = _entier(degres, "degres")
    m = _entier(minutes, "minutes")
    s = _reel(secondes, "secondes")
    if not (0 <= m < 60):
        raise ValueError(f"minutes hors [0, 60) : {m}")
    if not (0 <= s < 60):
        raise ValueError(f"secondes hors [0, 60) : {s}")
    signe = -1.0 if d < 0 else 1.0
    return signe * (abs(d) + m / 60.0 + s / 3600.0)


# ── Conversions d'unités de longueur (exactes) ──────────────────────────────────────────────────────────────────
def cm_en_m(cm) -> float:
    """Centimètres -> mètres (÷100, exact)."""
    return _reel(cm, "cm") / 100.0


def cm_en_km(cm) -> float:
    """Centimètres -> kilomètres (÷100000, exact)."""
    return _reel(cm, "cm") / 100000.0


if __name__ == "__main__":
    # Échelle 1:25000, 4 cm sur la carte -> 1 km réel.
    reel = echelle_distance_reelle(4, 25000)
    print(f"echelle_distance_reelle(4, 25000) = {reel} cm = {cm_en_km(reel)} km")
    print(f"distance_carte(100000, 25000)     = {distance_carte(100000, 25000)} cm")
    print(f"resolution_au_sol_depuis_dpi(300, 25000) = {resolution_au_sol_depuis_dpi(300, 25000).valeur_cm:.3f} cm")
    print(f"conversion_dms_dd(48, 51, 12)     = {conversion_dms_dd(48, 51, 12)}")
