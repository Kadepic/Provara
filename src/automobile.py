"""
automobile.py — Mécanique automobile élémentaire (formules établies).

Mécanismes EXACTS / déterministes (mécanique newtonienne + définitions de transmission) :

  • distance_freinage(vitesse_ms, coef_adherence, g=9.81) = v² / (2·µ·g)
      Distance d'arrêt sur sol horizontal, décélération maximale a = µ·g (frottement
      pneu/route). Énergie cinétique ½mv² dissipée par le travail µ·m·g·d.
      Ex. 100 km/h = 27.8 m/s, µ=0.8 -> ≈ 49 m.

  • puissance(force_N, vitesse_ms) = F · v        (watts)
      Puissance mécanique instantanée P = F·v (force motrice × vitesse).

  • rapport_transmission(dents_menee, dents_menante) = N_menee / N_menante
      Rapport de réduction d'un engrenage (roue menée / roue menante).
      > 1 = réduction (démultiplication), < 1 = surmultiplication.

  • regime_roue(regime_moteur, rapport) = N_moteur / rapport
      Régime de la roue (sortie) après une réduction de `rapport` (tr/min en entrée
      et en sortie). Cohérent avec rapport_transmission > 1 -> roue plus lente.

  • consommation_100km(litres, km) = litres · 100 / km
      Consommation moyenne en L/100 km (carburant consommé sur une distance).

ABSTENTION STRUCTURELLE (faux positif INTERDIT — jamais une valeur fausse) :
  • coef_adherence µ <= 0, g <= 0                          -> ValueError
  • vitesse_ms < 0 (toute vitesse négative)                -> ValueError
  • km <= 0 (distance nulle/négative), litres < 0          -> ValueError
  • dents <= 0 ou non entières, rapport <= 0               -> ValueError
  • régime moteur < 0                                       -> ValueError
  • entrée non numérique / booléenne / non finie           -> ValueError

stdlib uniquement. Sorties flottantes arrondies à 6 décimales.
"""

import math

__all__ = [
    "distance_freinage",
    "puissance",
    "rapport_transmission",
    "regime_roue",
    "consommation_100km",
]


def _reel(x, nom):
    """Réel fini strict (rejette bool / non numérique / inf / nan)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen non accepté : {x!r}")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{nom} non numérique : {x!r}")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _dents(x, nom):
    """Nombre de dents = entier strictement positif (40.0 admis comme 40)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} booléen non accepté : {x!r}")
    if isinstance(x, int):
        n = x
    elif isinstance(x, float):
        if not math.isfinite(x) or not x.is_integer():
            raise ValueError(f"{nom} non entier : {x!r}")
        n = int(x)
    else:
        raise ValueError(f"{nom} non numérique : {x!r}")
    if n <= 0:
        raise ValueError(f"{nom} non strictement positif : {n}")
    return n


def distance_freinage(vitesse_ms, coef_adherence, g=9.81):
    """
    Distance de freinage d = v² / (2·µ·g) (mètres).

    vitesse_ms >= 0 (m/s), coef_adherence µ > 0, g > 0 (m/s²).
    Retour arrondi à 6 décimales. Entrées invalides -> ValueError.
    """
    v = _reel(vitesse_ms, "vitesse_ms")
    mu = _reel(coef_adherence, "coef_adherence")
    gg = _reel(g, "g")
    if v < 0.0:
        raise ValueError(f"vitesse négative : {v}")
    if mu <= 0.0:
        raise ValueError(f"coef_adherence non strictement positif : {mu}")
    if gg <= 0.0:
        raise ValueError(f"g non strictement positif : {gg}")
    return round(v * v / (2.0 * mu * gg), 6)


def puissance(force_N, vitesse_ms):
    """
    Puissance mécanique P = F · v (watts).

    force_N : force motrice (N, réel fini). vitesse_ms >= 0 (m/s).
    Retour arrondi à 6 décimales. Entrées invalides -> ValueError.
    """
    f = _reel(force_N, "force_N")
    v = _reel(vitesse_ms, "vitesse_ms")
    if v < 0.0:
        raise ValueError(f"vitesse négative : {v}")
    return round(f * v, 6)


def rapport_transmission(dents_menee, dents_menante):
    """
    Rapport de transmission = N_menee / N_menante.

    dents_menee, dents_menante : entiers strictement positifs.
    Retour arrondi à 6 décimales. Entrées invalides -> ValueError.
    """
    menee = _dents(dents_menee, "dents_menee")
    menante = _dents(dents_menante, "dents_menante")
    return round(menee / menante, 6)


def regime_roue(regime_moteur, rapport):
    """
    Régime de la roue = N_moteur / rapport (même unité, p.ex. tr/min).

    regime_moteur >= 0, rapport > 0.
    Retour arrondi à 6 décimales. Entrées invalides -> ValueError.
    """
    n = _reel(regime_moteur, "regime_moteur")
    r = _reel(rapport, "rapport")
    if n < 0.0:
        raise ValueError(f"régime moteur négatif : {n}")
    if r <= 0.0:
        raise ValueError(f"rapport non strictement positif : {r}")
    return round(n / r, 6)


def consommation_100km(litres, km):
    """
    Consommation moyenne = litres · 100 / km (L/100 km).

    litres >= 0, km > 0.
    Retour arrondi à 6 décimales. Entrées invalides -> ValueError.
    """
    L = _reel(litres, "litres")
    d = _reel(km, "km")
    if L < 0.0:
        raise ValueError(f"litres négatif : {L}")
    if d <= 0.0:
        raise ValueError(f"km non strictement positif : {d}")
    return round(L * 100.0 / d, 6)
